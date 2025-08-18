# events/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from events.models import VehicleEvent
from parking.models import ParkingAssignment, ParkingSpace

from jetson.feed import (
    broadcast_parking_space,
    broadcast_active_vehicles,
)


@receiver(post_save, sender=VehicleEvent)
def vehicle_event_saved(sender, instance: VehicleEvent, created, **kwargs):
    # 입차/상태변경 시 → 활성차량 스냅샷 push
    broadcast_active_vehicles()


@receiver(post_save, sender=ParkingAssignment)
def assignment_saved(sender, instance: ParkingAssignment, created, **kwargs):
    # 배정 생성/재배정/상태변경 → 관련 슬롯/활성차량 동기화
    labels = []
    if instance.space_id and instance.space:
        labels.append(f"{instance.space.zone}{instance.space.slot_number}")
    broadcast_parking_space(labels or None)  # 해당 슬롯만 빠르게 갱신(없으면 전체)
    broadcast_active_vehicles()


@receiver(post_delete, sender=ParkingAssignment)
def assignment_deleted(sender, instance: ParkingAssignment, **kwargs):
    labels = []
    if instance.space_id and instance.space:
        labels.append(f"{instance.space.zone}{instance.space.slot_number}")
    broadcast_parking_space(labels or None)
    broadcast_active_vehicles()


@receiver(post_save, sender=ParkingSpace)
def space_saved(sender, instance: ParkingSpace, **kwargs):
    # 슬롯 상태 변경 시 → 슬롯/활성차량 동기화
    label = f"{instance.zone}{instance.slot_number}"
    broadcast_parking_space([label])
    broadcast_active_vehicles()
