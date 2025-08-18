# parking/services.py
from django.utils import timezone
from django.db import transaction

from jetson.feed import broadcast_active_vehicles
from vehicles.models import Vehicle
from events.models import VehicleEvent
from .models import ParkingSpace, ParkingAssignment
from events.broadcast import broadcast_parking_log_event
from parking.views import _broadcast_space  # 이미 있는 브로드캐스트 유틸 재사용


def _parse_slot_label(label: str):
    if not label or len(label) < 2:
        raise ValueError("invalid slot label")
    return label[0], int(label[1:])


@transaction.atomic
def handle_assignment_from_jetson(license_plate: str, slot_label: str):
    """
    Jetson이 회신한 (번호판, 슬롯라벨)을 기준으로 ParkingAssignment/Space 갱신.
    - 해당 차량의 '미출차' VehicleEvent를 찾는다.
    - 배정이 없으면 새로 만들고, 있으면 재배정한다.
    - 슬롯 상태는 reserved로, current_vehicle 세팅.
    - 브로드캐스트들 갱신.
    """
    try:
        vehicle = Vehicle.objects.select_related("user").get(
            license_plate=license_plate
        )
    except Vehicle.DoesNotExist:
        return False, "vehicle not found"

    # 이 차량의 진행 중(미출차) 이벤트
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

    # 배정 생성/재배정
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
        # 새 배정 → 새 슬롯 예약
        new_space.status = "reserved"
        new_space.current_vehicle = vehicle
        new_space.save(update_fields=["status", "current_vehicle", "updated_at"])
        _broadcast_space(new_space)
    else:
        # 재배정: 공간 변경 시 이전 공간 해제 + 새 공간 예약
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
            # 같은 슬롯을 다시 회신한 경우 → 상태만 보정
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

    # 다른 화면들 스냅샷 갱신
    broadcast_active_vehicles()
    broadcast_parking_log_event(ev)

    return True, "ok"
