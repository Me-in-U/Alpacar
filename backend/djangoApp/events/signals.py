# events/signals.py
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from jetson.broadcast import send_request_assignment
from parking.models import ParkingAssignment, ParkingSpace

from .broadcast import broadcast_parking_log_event
from .models import VehicleEvent
from django.db import transaction


@receiver(post_save, sender=VehicleEvent)
def vehicle_event_saved(sender, instance, created, **kwargs):
    # 생성/수정 모두 브로드캐스트 (상태/시간 변경 즉시 반영)
    transaction.on_commit(lambda: broadcast_parking_log_event(instance))


@receiver(post_save, sender=ParkingAssignment)
def assignment_saved(sender, instance, created, **kwargs):
    ev = getattr(instance, "entrance_event", None)
    if ev:
        transaction.on_commit(lambda: broadcast_parking_log_event(ev))


@receiver(post_delete, sender=ParkingAssignment)
def assignment_deleted(sender, instance, **kwargs):
    ev = getattr(instance, "entrance_event", None)
    if ev:
        transaction.on_commit(lambda: broadcast_parking_log_event(ev))


@receiver(post_save, sender=ParkingSpace)
def space_saved(sender, instance, **kwargs):
    pa = (
        instance.assignments.filter(status="ASSIGNED")
        .select_related("entrance_event")
        .first()
    )
    if pa and pa.entrance_event:
        transaction.on_commit(lambda: broadcast_parking_log_event(pa.entrance_event))


@receiver(post_save, sender=VehicleEvent)
def request_assignment_on_event_created(
    sender, instance: VehicleEvent, created, **kwargs
):
    print("[★★★★] request_assignment_on_event_created", created)
    if not created:
        print("[★★★★] request_assignment_on_event_created: not created")
        return

    def _send():
        vehicle = instance.vehicle
        model = getattr(vehicle, "model", None)
        size_class = getattr(model, "size_class", None)
        if not size_class:
            print("[★★★★] request_assignment_on_event_created: no size_class")
            return
        send_request_assignment(vehicle.license_plate, size_class)

    transaction.on_commit(_send)
