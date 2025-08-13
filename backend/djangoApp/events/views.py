# events/views.py
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from vehicles.models import Vehicle
from accounts.utils import (
    send_vehicle_entry_notification,
    send_parking_complete_notification,
    create_notification,
)
from .models import VehicleEvent
from .serializers import VehicleEventSerializer

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
    if last_event is None or last_event.status == "Exit":
        ev = VehicleEvent.objects.create(
            vehicle=vehicle,
            entrance_time=timezone.now(),
            parking_time=None,
            exit_time=None,
            status="Entrance",
        )
        # 입차 푸시(운영 로직 유지)
        try:
            entry_data = {
                "plate_number": vehicle.license_plate,
                "parking_lot": "SSAFY 주차장",
                "entry_time": timezone.now().isoformat(),
                "admin_action": True,
                "action_url": "/parking-recommend",
                "action_type": "navigate",
            }
            send_vehicle_entry_notification(vehicle.user, entry_data)
        except Exception:
            pass
        return Response(VehicleEventSerializer(ev).data, status=201)

    # 진행중 이벤트가 있으면 그대로 반환
    return Response(VehicleEventSerializer(last_event).data, status=200)


@api_view(["POST"])
@permission_classes([IsAdminUser])
def manual_parking_complete(request, vehicle_id):
    now = timezone.now()
    ev = (
        VehicleEvent.objects.filter(
            vehicle_id=vehicle_id,
            entrance_time__isnull=False,
            parking_time__isnull=True,
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

            score = random.randint(70, 95)
            send_parking_complete_notification(
                vehicle.user,
                {
                    "plate_number": vehicle.license_plate,
                    "parking_space": f"{space.zone}{space.slot_number}",
                    "parking_time": now.isoformat(),
                    "score": score,
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


@api_view(["POST"])
@permission_classes([IsAdminUser])
def manual_exit(request, vehicle_id):
    now = timezone.now()
    ev = (
        VehicleEvent.objects.filter(
            vehicle_id=vehicle_id, parking_time__isnull=False, exit_time__isnull=True
        )
        .order_by("-id")
        .first()
    )
    if ev is None:
        return Response({"detail": "출차할 주차 기록이 없습니다."}, status=400)

    ev.exit_time = now
    ev.status = "Exit"
    ev.save()

    vehicle = ev.vehicle
    try:
        from parking.models import ParkingAssignment, ParkingSpace

        pa = ParkingAssignment.objects.select_related("space").get(
            entrance_event=ev, status="ASSIGNED"
        )
        pa.status = "COMPLETED"
        pa.end_time = now
        pa.save(update_fields=["status", "end_time", "updated_at"])

        space = pa.space
        if space:
            space.status = "free"
            space.current_vehicle = None
            space.save(update_fields=["status", "current_vehicle", "updated_at"])

        # 알림
        parking_duration = None
        if ev.parking_time and ev.exit_time:
            duration = ev.exit_time - ev.parking_time
            total_minutes = int(duration.total_seconds() / 60)
            h, m = divmod(total_minutes, 60)
            parking_duration = f"{h}시간 {m}분" if h > 0 else f"{m}분"

        if space:
            create_notification(
                user=vehicle.user,
                title="🚗 출차 완료",
                message=f"{vehicle.license_plate} 차량이 {space.zone}{space.slot_number} 구역에서 출차 완료되었습니다."
                + (f" 주차 시간: {parking_duration}" if parking_duration else ""),
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
        pass

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
