# events\views.py

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from events.broadcast import broadcast_active_vehicles
from parking.models import ParkingAssignment
from vehicles.models import Vehicle

from .models import VehicleEvent
from .serializers import VehicleEventSerializer


class VehicleEventPagination(PageNumberPagination):
    page_size = 10  # 한 페이지당 10개


@api_view(["GET"])
@permission_classes([IsAdminUser])
def list_vehicle_events(request):
    qs = VehicleEvent.objects.select_related("vehicle").order_by("-id")
    paginator = VehicleEventPagination()
    page = paginator.paginate_queryset(qs, request)
    serializer = VehicleEventSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


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
    if last_event is None or last_event.status == "Exit":
        ev = VehicleEvent.objects.create(
            vehicle=vehicle,
            entrance_time=timezone.now(),
            parking_time=None,
            exit_time=None,
            status="Entrance",
        )
        # 입차 목록 갱신 트리거
        broadcast_active_vehicles()
        ser = VehicleEventSerializer(ev)
        return Response(ser.data, status=status.HTTP_201_CREATED)

    # 이미 Entrance/Parking 등 진행 중이면 그 이벤트 그대로 반환
    ser = VehicleEventSerializer(last_event)
    broadcast_active_vehicles()
    return Response(ser.data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAdminUser])
def manual_parking_complete(request, vehicle_id):
    now = timezone.now()
    # 1) “입차는 되었으나(parking_time is null) 아직 주차되지 않은” 이벤트 조회
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
        return Response(
            {"detail": "해당 차량의 입차 기록이 없습니다."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # 2) 주차시간·상태 업데이트
    ev.parking_time = now
    ev.status = "Parking"
    ev.save()
    broadcast_active_vehicles()
    #  이 입차 이벤트에 대한 배정이 있으면 슬롯도 occupied 처리
    try:
        pa = ParkingAssignment.objects.select_related("space").get(
            entrance_event=ev, status="ASSIGNED"
        )
        space = pa.space
        if space:
            space.status = "occupied"
            space.save(update_fields=["status", "updated_at"])

            # 슬롯 상태 브로드캐스트(색/상태 반영)
            from parking.views import _broadcast_space

            _broadcast_space(space)
    except ParkingAssignment.DoesNotExist:
        pass

    # 입차 차량 패널 실시간 갱신 트리거
    broadcast_active_vehicles()
    return Response(VehicleEventSerializer(ev).data, status=200)


from rest_framework import status


@api_view(["POST"])
@permission_classes([IsAdminUser])
def manual_exit(request, vehicle_id):
    now = timezone.now()
    # ① “주차는 되었으나(exit_time이 null) 아직 출차되지 않은” 이벤트 조회
    ev = (
        VehicleEvent.objects.filter(
            vehicle_id=vehicle_id, parking_time__isnull=False, exit_time__isnull=True
        )
        .order_by("-id")
        .first()
    )

    if ev is None:
        return Response(
            {"detail": "출차할 주차 기록이 없습니다."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # ② exit_time·status 업데이트
    ev.exit_time = now
    ev.status = "Exit"
    ev.save()
    broadcast_active_vehicles()
    #  배정이 있으면 완료 처리 + 슬롯 해제
    try:
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
            from parking.views import _broadcast_space

            _broadcast_space(space)
    except ParkingAssignment.DoesNotExist:
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
        # FK: ParkingAssignment.entrance_event = ev
        assignment = getattr(ev, "assignment", None)  # OneToOne 역참조
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
                "assigned_space": assigned,  # ← 추가!
            }
        )
    return Response({"results": data})
