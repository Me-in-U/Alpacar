# events/signals.py
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from parking.models import ParkingAssignment, ParkingSpace

from .broadcast import broadcast_parking_log_event
from .models import VehicleEvent

from django.db.models.signals import post_save
from django.dispatch import receiver

from jetson.broadcast import send_request_assignment

from .models import VehicleEvent


@receiver(post_save, sender=VehicleEvent)
def vehicle_event_saved(sender, instance, created, **kwargs):
    # 생성/수정 모두 브로드캐스트 (상태/시간 변경 즉시 반영)
    broadcast_parking_log_event(instance)


@receiver(post_save, sender=ParkingAssignment)
def assignment_saved(sender, instance, created, **kwargs):
    # 배정 생성/재배정/상태변경 시 해당 입차 이벤트를 푸시
    ev = getattr(instance, "entrance_event", None)
    if ev:
        broadcast_parking_log_event(ev)


@receiver(post_delete, sender=ParkingAssignment)
def assignment_deleted(sender, instance, **kwargs):
    # 배정 삭제 시 assigned_space=None 반영
    ev = getattr(instance, "entrance_event", None)
    if ev:
        broadcast_parking_log_event(ev)


@receiver(post_save, sender=ParkingSpace)
def space_saved(sender, instance, **kwargs):
    # 슬롯 상태 변경 시, 그 슬롯을 참조 중인 ASSIGNED 배정의 entrance_event를 푸시
    pa = (
        instance.assignments.filter(status="ASSIGNED")
        .select_related("entrance_event")
        .first()
    )
    if pa and pa.entrance_event:
        broadcast_parking_log_event(pa.entrance_event)


@receiver(post_save, sender=VehicleEvent)
def request_assignment_on_event_created(
    sender, instance: VehicleEvent, created, **kwargs
):
    print("[★★★★] request_assignment_on_event_created")
    # 입차 이벤트가 새로 생성될 때만 젯슨에 요청을 보낸다.
    if not created:
        print("[★★★★] request_assignment_on_event_created: not created")
        return
    vehicle = instance.vehicle
    model = getattr(vehicle, "model", None)
    size_class = getattr(model, "size_class", None)
    if not size_class:
        print("[★★★★] request_assignment_on_event_created: no size_class")
        return
    send_request_assignment(vehicle.license_plate, size_class)
