# events/signals.py
from django.db import transaction
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from events.models import VehicleEvent
from parking.models import ParkingAssignment, ParkingSpace
from events.broadcast import broadcast_parking_log_event
from jetson.broadcast import send_request_assignment, get_user_skill_level
from jetson.feed import (
    broadcast_parking_space,
    broadcast_active_vehicles,
)


@receiver(post_save, sender=VehicleEvent)
def vehicle_event_saved(sender, instance: VehicleEvent, created, **kwargs):
    # 로그 갱신
    transaction.on_commit(lambda: broadcast_parking_log_event(instance))
    # 활성차량 패널 갱신
    transaction.on_commit(broadcast_active_vehicles)


@receiver(post_save, sender=ParkingAssignment)
def assignment_saved(sender, instance: ParkingAssignment, created, **kwargs):
    labels = []
    if instance.space_id and instance.space:
        labels.append(f"{instance.space.zone}{instance.space.slot_number}")
    # 칸/활성차량 갱신
    transaction.on_commit(lambda: broadcast_parking_space(labels or None))
    transaction.on_commit(broadcast_active_vehicles)
    # 해당 입차 이벤트 로그도 갱신
    ev = getattr(instance, "entrance_event", None)
    if ev:
        transaction.on_commit(lambda: broadcast_parking_log_event(ev))


@receiver(post_delete, sender=ParkingAssignment)
def assignment_deleted(sender, instance: ParkingAssignment, **kwargs):
    labels = []
    if instance.space_id and instance.space:
        labels.append(f"{instance.space.zone}{instance.space.slot_number}")
    transaction.on_commit(lambda: broadcast_parking_space(labels or None))
    transaction.on_commit(broadcast_active_vehicles)
    ev = getattr(instance, "entrance_event", None)
    if ev:
        transaction.on_commit(lambda: broadcast_parking_log_event(ev))


@receiver(post_save, sender=ParkingSpace)
def space_saved(sender, instance: ParkingSpace, **kwargs):
    label = f"{instance.zone}{instance.slot_number}"
    transaction.on_commit(lambda: broadcast_parking_space([label]))
    transaction.on_commit(broadcast_active_vehicles)


@receiver(post_save, sender=VehicleEvent)
def request_assignment_on_event_created(
    sender, instance: VehicleEvent, created, **kwargs
):
    # Entrance 이벤트가 새로 생기면 젯슨에 배정 요청
    if not created:
        return

    def _send():
        vehicle = instance.vehicle
        model = getattr(vehicle, "model", None)
        size_class = getattr(model, "size_class", None)
        
        # 사용자 실력 레벨 가져오기
        user_skill_level = None
        if hasattr(vehicle, 'user') and vehicle.user:
            user_skill_level = get_user_skill_level(vehicle.user.score)
        
        if size_class:
            send_request_assignment(vehicle.license_plate, size_class, user_skill_level)

    transaction.on_commit(_send)
