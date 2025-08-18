# parking/services.py
from django.utils import timezone
from django.db import transaction
from vehicles.models import Vehicle
from events.models import VehicleEvent
from .models import ParkingSpace, ParkingAssignment, ParkingAssignmentHistory


def _parse_slot_label(label: str):
    if not label or len(label) < 2:
        raise ValueError("invalid slot label")
    return label[0], int(label[1:])


@transaction.atomic
def handle_assignment_from_jetson(license_plate: str, slot_label: str):
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
        # 새 공간 보정
        if new_space.status != "reserved" or new_space.current_vehicle_id != vehicle.id:
            new_space.status = "reserved"
            new_space.current_vehicle = vehicle
            new_space.save(update_fields=["status", "current_vehicle", "updated_at"])

    # 방송은 signals가 처리
    return True, "ok"


def add_score_from_jetson(license_plate: str, score: int):
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


@transaction.atomic
def mark_parking_complete_from_ai(license_plate: str, zone_label: str | None = None):
    """
    Jetson의 score 수신을 '주차 완료'로 간주하여 상태를 갱신한다.
    - 진행 중(VehicleEvent.exit_time is null) 이벤트를 찾고 Parking 시각/상태 저장
    - 배정된 슬롯이 있다면 해당 슬롯을 occupied로 전환
    - zone_label이 들어오면 우선 일치 검증(선택)
    Returns: (ok: bool, msg: str, occupied_label: str | None)
    """
    now = timezone.now()

    ev = (
        VehicleEvent.objects.select_related("vehicle", "assignment__space")
        .filter(vehicle__license_plate=license_plate, exit_time__isnull=True)
        .order_by("-id")
        .first()
    )
    if not ev:
        return False, "active vehicle_event not found", None

    # 이미 Parking 처리되어 있으면 그대로 성공 반환
    if ev.parking_time and ev.status == "Parking":
        label = None
        if getattr(ev, "assignment", None) and ev.assignment.space:
            s = ev.assignment.space
            label = f"{s.zone}{s.slot_number}"
        return True, "already parked", label

    # 배정 슬롯
    space = None
    if getattr(ev, "assignment", None) and ev.assignment.space:
        space = ev.assignment.space

    # 선택적으로 zone_label과 일치 여부 체크
    if zone_label and space:
        expected = f"{space.zone}{space.slot_number}".upper()
        if zone_label.upper() != expected:
            return False, f"slot mismatch: expected {expected}, got {zone_label}", None

    # VehicleEvent → Parking 전환
    ev.parking_time = now
    ev.status = "Parking"
    ev.save(update_fields=["parking_time", "status"])

    occupied_label = None
    # 슬롯을 occupied 로 전환
    if space:
        if space.status != "occupied":
            space.status = "occupied"
            space.save(update_fields=["status", "updated_at"])
        occupied_label = f"{space.zone}{space.slot_number}"

    return True, "ok", occupied_label
