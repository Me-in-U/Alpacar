# events/views.py
import logging

from accounts.utils import (
    send_vehicle_entry_notification,
)  # 입차 알림 대신 자리 배정 알림
from accounts.utils import create_notification, send_parking_complete_notification
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from vehicles.models import Vehicle

from .models import VehicleEvent
from .serializers import VehicleEventSerializer

logger = logging.getLogger(__name__)

# 실시간 방송은 signals에서 수행. 여기서는 저장/알림만.


class VehicleEventPagination(PageNumberPagination):
    page_size = 10


@api_view(["GET"])
@permission_classes([IsAdminUser])
def list_vehicle_events(request):
    qs = VehicleEvent.objects.select_related("vehicle").order_by("-id")
    paginator = VehicleEventPagination()
    page = paginator.paginate_queryset(qs, request)
    ser = VehicleEventSerializer(page, many=True)
    return paginator.get_paginated_response(ser.data)


# ! 수동 입차
@api_view(["POST"])
@permission_classes([IsAdminUser])
def manual_entrance(request):
    plate = (request.data.get("license_plate") or "").strip()
    if not plate:
        return Response({"detail": "license_plate가 필요합니다."}, status=400)

    try:
        vehicle = Vehicle.objects.get(license_plate=plate)
    except Vehicle.DoesNotExist:
        return Response({"detail": "해당 차량을 찾을 수 없습니다."}, status=404)

    last_event = VehicleEvent.objects.filter(vehicle=vehicle).order_by("-id").first()

    # 최근 이벤트가 없거나 출차였다면 새 입차 생성
    if last_event is None or last_event.status == "Exit":
        ev = VehicleEvent.objects.create(
            vehicle=vehicle,
            entrance_time=timezone.now(),
            parking_time=None,
            exit_time=None,
            status="Entrance",
        )

        # 입차 알림 제거 - 수동 입차 시에는 알림 발송하지 않음
        print(f"[ADMIN] 수동 입차 기록됨: {vehicle.license_plate} (알림 없음)")

        # VehicleEvent 저장으로 signals가 실시간 갱신 방송 처리
        return Response(VehicleEventSerializer(ev).data, status=201)

    # 진행 중 이벤트가 있으면 그대로 반환
    return Response(VehicleEventSerializer(last_event).data, status=200)


# ! 수동 주차 완료
@api_view(["POST"])
@permission_classes([IsAdminUser])
def manual_parking_complete(request, vehicle_id):
    now = timezone.now()
    # '주차완료' 여부와 상관없이, 입차 후 아직 출차 안 된 이벤트를 대상으로 허용
    ev = (
        VehicleEvent.objects.filter(
            vehicle_id=vehicle_id,
            entrance_time__isnull=False,
            exit_time__isnull=True,
        )
        .order_by("-id")
        .first()
    )
    if ev is None:
        return Response({"detail": "해당 차량의 입차 기록이 없습니다."}, status=400)

    ev.parking_time = now
    ev.status = "Parking"
    ev.save()

    vehicle = ev.vehicle
    # 배정이 있다면 점수 푸시 등 알림 유지(방송은 signals가 처리)
    try:
        from parking.models import ParkingAssignment, ParkingSpace

        pa = ParkingAssignment.objects.select_related("space").get(
            entrance_event=ev, status="ASSIGNED"
        )
        space = pa.space
        if space:
            # 상태 변경만, 방송은 signals가 처리
            space.status = "occupied"
            space.save(update_fields=["status", "updated_at"])

            # 임시 점수/알림(유지)
            import random

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
    except Exception:
        # 배정 없음 등
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
            pass

    return Response(VehicleEventSerializer(ev).data, status=200)


# ! 수동 출차
def _get_open_event_for_exit(vehicle_id):
    return (
        VehicleEvent.objects.select_for_update()
        .filter(vehicle_id=vehicle_id, exit_time__isnull=True)
        .order_by("-id")
        .first()
    )


def _mark_event_exited(ev, now):
    ev.exit_time = now
    ev.status = "Exit"
    ev.save(update_fields=["exit_time", "status"])
    return ev


def _complete_active_assignment(ev, now):
    """진행 중 배정(ASSIGNED)만 종료하고 공간 상태 갱신. 없으면 None 반환."""
    from parking.models import ParkingAssignment, ParkingSpace

    try:
        pa = (
            ParkingAssignment.objects.select_for_update()
            .select_related("space")
            .get(entrance_event=ev, status="ASSIGNED")
        )
    except ParkingAssignment.DoesNotExist:
        return None

    pa.status = "COMPLETED"
    pa.end_time = now
    pa.save(update_fields=["status", "end_time", "updated_at"])

    space = pa.space
    if not space or not space.pk:
        return None

    # 일부 백엔드에서 related select_for_update 미지원 → 재조회
    space = ParkingSpace.objects.select_for_update().get(pk=space.pk)
    space.status = "free"
    space.current_vehicle = None
    space.save(update_fields=["status", "current_vehicle", "updated_at"])
    return space


def _format_parking_duration(ev):
    if not (ev.parking_time and ev.exit_time):
        return None
    duration = ev.exit_time - ev.parking_time
    total_minutes = int(duration.total_seconds() / 60)
    h, m = divmod(total_minutes, 60)
    return f"{h}시간 {m}분" if h > 0 else f"{m}분"


def _notify_exit(vehicle, space, now, parking_duration):
    base_data = {
        "plate_number": vehicle.license_plate,
        "exit_time": now.isoformat(),
        "admin_action": True,
        "action_url": "/parking-recommend",
        "action_type": "navigate",
    }

    if space:
        msg = f"{vehicle.license_plate} 차량이 {space.zone}{space.slot_number} 구역에서 출차 완료되었습니다."
        if parking_duration:
            msg += f" 주차 시간: {parking_duration}"
        data = {
            **base_data,
            "parking_space": f"{space.zone}{space.slot_number}",
            "parking_duration": parking_duration,
        }
    else:
        msg = f"{vehicle.license_plate} 차량이 주차장에서 출차 완료되었습니다."
        data = {**base_data, "parking_space": "주차장"}

    create_notification(
        user=vehicle.user,
        title="🚗 출차 완료",
        message=msg,
        notification_type="exit",
        data=data,
    )


@api_view(["POST"])
@permission_classes([IsAdminUser])
def manual_exit(request, vehicle_id):
    now = timezone.now()
    with transaction.atomic():
        ev = _get_open_event_for_exit(vehicle_id)
        if ev is None:
            return Response({"detail": "출차할 주차 기록이 없습니다."}, status=400)

        _mark_event_exited(ev, now)
        vehicle = ev.vehicle

        try:
            space = _complete_active_assignment(ev, now)
        except Exception as e:
            logger.warning("배정 종료 처리 중 오류(무시): %s", e)
            space = None

    # 트랜잭션 밖: 알림 (실패해도 응답에는 영향 X)
    try:
        _notify_exit(vehicle, space, now, _format_parking_duration(ev))
    except Exception as e:
        logger.warning("출차 알림 전송 실패(무시): %s", e)

    return Response(VehicleEventSerializer(ev).data, status=200)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def active_vehicle_events(request):
    qs = (
        VehicleEvent.objects.select_related("vehicle", "vehicle__model")
        .filter(exit_time__isnull=True)
        .order_by("-id")
    )
    data = []
    for ev in qs:
        assignment = getattr(ev, "assignment", None)
        assigned = None
        if assignment and assignment.space:
            assigned = {
                "zone": assignment.space.zone,
                "slot_number": assignment.space.slot_number,
                "label": f"{assignment.space.zone}{assignment.space.slot_number}",
            }
        data.append(
            {
                "id": ev.id,
                "vehicle_id": ev.vehicle_id,
                "license_plate": ev.vehicle.license_plate,
                "entrance_time": ev.entrance_time,
                "status": ev.status,
                "assigned_space": assigned,
            }
        )
    return Response({"results": data})
