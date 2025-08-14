# events/signals.py
from __future__ import annotations

import logging
from typing import Callable, Iterable, List, Optional

from django.db import transaction
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from events.models import VehicleEvent
from parking.models import ParkingAssignment, ParkingSpace
from events.broadcast import broadcast_parking_log_event
from jetson.broadcast import send_request_assignment
from jetson.feed import broadcast_parking_space, broadcast_active_vehicles

logger = logging.getLogger(__name__)

STATUS_ENTRANCE = "Entrance"


def _label_from_space(space: Optional[ParkingSpace]) -> Optional[str]:
    if not space:
        return None
    return f"{space.zone}{space.slot_number}"


def _on_commit(*funcs: Iterable[Callable[[], None]]) -> None:
    for f in funcs:
        transaction.on_commit(f)


@receiver(post_save, sender=VehicleEvent)
def handle_vehicle_event_saved(sender, instance: VehicleEvent, created: bool, **kwargs):
    """
    - 모든 VehicleEvent 저장 시: 로그 패널 + 활성차량 패널 갱신
    - 새로 생성된 Entrance 이벤트: Jetson에 배정 요청
    """
    _on_commit(
        lambda: broadcast_parking_log_event(instance),
        broadcast_active_vehicles,
    )

    if created and getattr(instance, "status", None) == STATUS_ENTRANCE:

        def _send():
            vehicle = instance.vehicle
            model = getattr(vehicle, "model", None)
            size_class = getattr(model, "size_class", None)
            if size_class:
                send_request_assignment(vehicle.license_plate, size_class)
            else:
                logger.debug(
                    "Skip send_request_assignment: size_class missing (vehicle=%s)",
                    getattr(vehicle, "id", None),
                )

        _on_commit(_send)


@receiver(post_save, sender=ParkingAssignment)
def handle_assignment_saved(
    sender, instance: ParkingAssignment, created: bool, **kwargs
):
    """
    - ParkingAssignment 생성/수정 시:
      · 해당 슬롯 라벨만 부분 갱신(broadcast_parking_space)
      · 활성차량 패널 갱신
      · 관련 입차 이벤트 로그 갱신
    """
    label = _label_from_space(getattr(instance, "space", None))
    labels: Optional[List[str]] = [label] if label else None

    ev = getattr(instance, "entrance_event", None)

    tasks: List[Callable[[], None]] = [
        (lambda: broadcast_parking_space(labels)),
        broadcast_active_vehicles,
    ]
    if ev:
        tasks.append(lambda ev=ev: broadcast_parking_log_event(ev))

    _on_commit(*tasks)


@receiver(post_delete, sender=ParkingAssignment)
def handle_assignment_deleted(sender, instance: ParkingAssignment, **kwargs):
    """
    - ParkingAssignment 삭제 시:
      · 해당 슬롯 라벨만 부분 갱신(broadcast_parking_space)
      · 활성차량 패널 갱신
      · 관련 입차 이벤트 로그 갱신
    """
    label = _label_from_space(getattr(instance, "space", None))
    labels: Optional[List[str]] = [label] if label else None

    ev = getattr(instance, "entrance_event", None)

    tasks: List[Callable[[], None]] = [
        (lambda: broadcast_parking_space(labels)),
        broadcast_active_vehicles,
    ]
    if ev:
        tasks.append(lambda ev=ev: broadcast_parking_log_event(ev))

    _on_commit(*tasks)


@receiver(post_save, sender=ParkingSpace)
def handle_space_saved(sender, instance: ParkingSpace, **kwargs):
    """
    - ParkingSpace 저장 시:
      · 해당 슬롯 라벨만 부분 갱신(broadcast_parking_space)
      · 활성차량 패널 갱신
    """
    label = _label_from_space(instance)
    labels = [label] if label else None
    _on_commit(
        lambda: broadcast_parking_space(labels),
        broadcast_active_vehicles,
    )
