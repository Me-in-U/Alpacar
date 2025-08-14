# events/views.py
from __future__ import annotations

import logging
from typing import Optional

from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from accounts.utils import (
    create_notification,
    send_parking_complete_notification,
)
from parking.models import ParkingAssignment, ParkingSpace
from vehicles.models import Vehicle

from .models import VehicleEvent
from .serializers import VehicleEventSerializer

logger = logging.getLogger(__name__)

# ── 상태 코드 상수(모델 choices와 일치시킬 것) ──
STATUS_ENTRANCE = "Entrance"
STATUS_PARKING = "Parking"
STATUS_EXIT = "Exit"


# 실시간 방송은 signals에서 수행. 여기서는 저장/알림만.
class VehicleEventPagination(PageNumberPagination):
    page_size = 10


def _format_parking_duration(ev: VehicleEvent) -> Optional[str]:
    if ev.parking_time and ev.exit_time:
        duration = ev.exit_time - ev.parking_time
        total_minutes = int(duration.total_seconds() // 60)
        h, m = divmod(total_minutes, 60)
        return f"{h}시간 {m}분" if h > 0 else f"{m}분"
    return None


@api_view(["GET"])
@permission_classes([IsAdminUser])
def list_vehicle_events(request):
    qs = VehicleEvent.objects.select_related("vehicle", "assignment__space").order_by(
        "-id"
    )
    paginator = VehicleEventPagination()
    page = paginator.paginate_queryset(qs, request)
    ser = VehicleEventSerializer(page, many=True)
    return paginator.get_paginated_response(ser.data)


@api_view(["POST"])
@permission_classes([IsAdminUser])
def manual_entrance(request):
    plate = (request.data.get("license_plate") or "").strip()
    if not plate:
        return Response(
            {"detail": "license_plate가 필요합니다."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        vehicle = Vehicle.objects.get(license_plate=plate)
    except Vehicle.DoesNotExist:
        return Response(
            {"detail": "해당 차량을 찾을 수 없습니다."},
            status=status.HTTP_404_NOT_FOUND,
        )

    last_event = VehicleEvent.objects.filter(vehicle=vehicle).order_by("-id").first()

    # 최근 이벤트가 없거나 출차였다면 새 입차 생성
    if last_event is None or last_event.status == STATUS_EXIT:
        ev = VehicleEvent.objects.create(
            vehicle=vehicle,
            entrance_time=timezone.now(),
            parking_time=None,
            exit_time=None,
            status=STATUS_ENTRANCE,
        )
        logger.info("[ADMIN] 수동 입차 기록: %s (알림 미발송)", vehicle.license_plate)
        return Response(VehicleEventSerializer(ev).data, status=status.HTTP_201_CREATED)

    # 진행 중 이벤트가 있으면 그대로 반환
    return Response(VehicleEventSerializer(last_event).data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAdminUser])
def manual_parking_complete(request, vehicle_id: int):
    now = timezone.now()

    # 입차 후 아직 출차 안 된 이벤트
    ev = (
        VehicleEvent.objects.filter(
            vehicle_id=vehicle_id, entrance_time__isnull=False, exit_time__isnull=True
        )
        .order_by("-id")
        .select_related("vehicle")
        .first()
    )
    if ev is None:
        return Response(
            {"detail": "해당 차량의 입차 기록이 없습니다."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    ev.parking_time = now
    ev.status = STATUS_PARKING
    ev.save(update_fields=["parking_time", "status", "updated_at"])

    vehicle = ev.vehicle

    # 배정이 있다면 공간 상태를 occupied로 갱신(방송은 signals가 처리)
    try:
        pa = ParkingAssignment.objects.select_related("space").get(
            entrance_event=ev, status="ASSIGNED"
        )
        space = pa.space
        if space:
            space.status = "occupied"
            space.save(update_fields=["status", "updated_at"])

            send_parking_complete_notification(
                vehicle.user,
                {
                    "plate_number": vehicle.license_plate,
                    "parking_space": f"{space.zone}{space.slot_number}",
                    "parking_time": now.isoformat(),
                    "score": 0,
                    "admin_action": True,
                },
            )
    except ParkingAssignment.DoesNotExist:
        # 배정이 없어도 알림은 보냄(주차공간 정보 없음)
        try:
            send_parking_complete_notification(
                vehicle.user,
                {
                    "plate_number": vehicle.license_plate,
                    "parking_space": "배정된 구역",
                    "parking_time": now.isoformat(),
                    "score": None,
                    "admin_action": True,
                },
            )
        except Exception:
            logger.exception(
                "send_parking_complete_notification 실패(vehicle_id=%s)", vehicle_id
            )
    except Exception:
        logger.exception(
            "manual_parking_complete 처리 중 오류(vehicle_id=%s)", vehicle_id
        )

    return Response(VehicleEventSerializer(ev).data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAdminUser])
def manual_exit(request, vehicle_id: int):
    now = timezone.now()

    with transaction.atomic():
        # 출차 대상 이벤트 잠금
        ev = (
            VehicleEvent.objects.select_for_update()
            .select_related("vehicle")
            .filter(vehicle_id=vehicle_id, exit_time__isnull=True)
            .order_by("-id")
            .first()
        )
        if ev is None:
            return Response(
                {"detail": "출차할 주차 기록이 없습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ev.exit_time = now
        ev.status = STATUS_EXIT
        ev.save(update_fields=["exit_time", "status", "updated_at"])

        space = None
        try:
            # 진행 중 배정(ASSIGNED) 잠금 후 종료
            pa = (
                ParkingAssignment.objects.select_for_update()
                .select_related("space")
                .get(entrance_event=ev, status="ASSIGNED")
            )
            pa.status = "COMPLETED"
            pa.end_time = now
            pa.save(update_fields=["status", "end_time", "updated_at"])

            # 공간 상태를 free로
            space = pa.space
            if space and space.pk:
                space = ParkingSpace.objects.select_for_update().get(pk=space.pk)
                space.status = "free"
                space.current_vehicle = None
                space.save(update_fields=["status", "current_vehicle", "updated_at"])
        except ParkingAssignment.DoesNotExist:
            space = None  # 배정이 없을 수 있음
        except Exception:
            logger.exception(
                "manual_exit 배정/공간 갱신 실패(vehicle_id=%s)", vehicle_id
            )
            space = None

    # 알림(트랜잭션 외부)
    try:
        vehicle = ev.vehicle
        parking_duration = _format_parking_duration(ev)

        if space:
            create_notification(
                user=vehicle.user,
                title="🚗 출차 완료",
                message=(
                    f"{vehicle.license_plate} 차량이 {space.zone}{space.slot_number} 구역에서 출차 완료되었습니다."
                    + (f" 주차 시간: {parking_duration}" if parking_duration else "")
                ),
                notification_type="exit",
                data={
                    "plate_number": vehicle.license_plate,
                    "parking_space": f"{space.zone}{space.slot_number}",
                    "exit_time": now.isoformat(),
                    "parking_duration": parking_duration,
                    "admin_action": True,
                    "action_url": "/parking-recommend",
                    "action_type": "navigate",
                },
            )
        else:
            create_notification(
                user=vehicle.user,
                title="🚗 출차 완료",
                message=f"{vehicle.license_plate} 차량이 주차장에서 출차 완료되었습니다.",
                notification_type="exit",
                data={
                    "plate_number": vehicle.license_plate,
                    "parking_space": "주차장",
                    "exit_time": now.isoformat(),
                    "admin_action": True,
                    "action_url": "/parking-recommend",
                    "action_type": "navigate",
                },
            )
    except Exception:
        logger.exception("출차 알림 생성 실패(vehicle_id=%s)", vehicle_id)

    return Response(VehicleEventSerializer(ev).data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def active_vehicle_events(request):
    qs = (
        VehicleEvent.objects.select_related(
            "vehicle", "vehicle__model", "assignment__space"
        )
        .filter(exit_time__isnull=True)
        .order_by("-id")
    )

    results = []
    for ev in qs:
        assignment = getattr(ev, "assignment", None)
        space = getattr(assignment, "space", None) if assignment else None
        assigned = None
        if space:
            assigned = {
                "zone": space.zone,
                "slot_number": space.slot_number,
                "label": f"{space.zone}{space.slot_number}",
            }
        results.append(
            {
                "id": ev.id,
                "vehicle_id": ev.vehicle_id,
                "license_plate": ev.vehicle.license_plate,
                "entrance_time": ev.entrance_time,
                "status": ev.status,
                "assigned_space": assigned,
            }
        )

    return Response({"results": results}, status=status.HTTP_200_OK)
