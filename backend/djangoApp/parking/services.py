# parking/services.py
from django.utils import timezone
from django.db import transaction

from vehicles.models import Vehicle
from events.models import VehicleEvent
from .models import ParkingSpace, ParkingAssignment, ParkingAssignmentHistory
from events.broadcast import broadcast_active_vehicles, broadcast_parking_log_event
from parking.views import _broadcast_space  # 이미 존재


def _parse_slot_label(label: str):
    if not label or len(label) < 2:
        raise ValueError("invalid slot label")
    return label[0], int(label[1:])


@transaction.atomic
def handle_assignment_from_jetson(license_plate: str, slot_label: str):
    """
    Jetson이 회신한 (번호판, 슬롯라벨)을 기준으로 ParkingAssignment/Space 갱신.
    - '미출차' VehicleEvent 찾기
    - 배정 생성/재배정
    - 공간 상태 reserved, current_vehicle 세팅
    - 브로드캐스트 갱신
    """
    try:
        vehicle = Vehicle.objects.select_related("user").get(
            license_plate=license_plate
        )
    except Vehicle.DoesNotExist:
        return False, "vehicle not found"

    ev = (
        VehicleEvent.objects.filter(vehicle=vehicle, exit_time__isnull=True)
        .order_by("-id")
        .first()
    )
    if not ev:
        return False, "no active event for vehicle"

    try:
        zone, slot_number = _parse_slot_label(slot_label)
        new_space = ParkingSpace.objects.select_for_update().get(
            zone=zone, slot_number=slot_number
        )
    except ParkingSpace.DoesNotExist:
        return False, "parking space not found"
    except Exception as e:
        return False, str(e)

    pa, created = ParkingAssignment.objects.select_for_update().get_or_create(
        entrance_event=ev,
        defaults={
            "user": vehicle.user,
            "vehicle": vehicle,
            "space": new_space,
            "start_time": timezone.now(),
            "status": "ASSIGNED",
        },
    )

    if created:
        new_space.status = "reserved"
        new_space.current_vehicle = vehicle
        new_space.save(update_fields=["status", "current_vehicle", "updated_at"])
        _broadcast_space(new_space)
    else:
        if pa.space_id != new_space.id:
            old_space = pa.space
            pa.space = new_space
            pa.save(update_fields=["space", "updated_at"])

            if old_space and old_space.status != "free":
                old_space.status = "free"
                old_space.current_vehicle = None
                old_space.save(
                    update_fields=["status", "current_vehicle", "updated_at"]
                )
                _broadcast_space(old_space)

            new_space.status = "reserved"
            new_space.current_vehicle = vehicle
            new_space.save(update_fields=["status", "current_vehicle", "updated_at"])
            _broadcast_space(new_space)
        else:
            if (
                new_space.status != "reserved"
                or new_space.current_vehicle_id != vehicle.id
            ):
                new_space.status = "reserved"
                new_space.current_vehicle = vehicle
                new_space.save(
                    update_fields=["status", "current_vehicle", "updated_at"]
                )
                _broadcast_space(new_space)

    broadcast_active_vehicles()
    broadcast_parking_log_event(ev)
    return True, "ok"


def add_score_from_jetson(license_plate: str, score: int):
    """
    Jetson 점수 메시지를 받아 ParkingAssignmentHistory에 기록.
    - 진행중(미출차) 배정이 있으면 그 배정에 연결
    - 없으면 해당 차량의 '가장 최근' 배정에 연결
    """
    try:
        vehicle = Vehicle.objects.select_related("user").get(
            license_plate=license_plate
        )
    except Vehicle.DoesNotExist:
        return False, "vehicle not found"

    ev = (
        VehicleEvent.objects.filter(vehicle=vehicle, exit_time__isnull=True)
        .order_by("-id")
        .first()
    )
    assignment = None
    if ev:
        assignment = ParkingAssignment.objects.filter(entrance_event=ev).first()

    if not assignment:
        assignment = (
            ParkingAssignment.objects.filter(vehicle=vehicle)
            .order_by("-start_time")
            .first()
        )

    ParkingAssignmentHistory.objects.create(
        user=vehicle.user,
        assignment=assignment,  # 없으면 null 허용
        score=int(score),
    )
    return True, "ok"
