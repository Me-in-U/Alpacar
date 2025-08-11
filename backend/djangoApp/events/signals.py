# events/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from parking.models import ParkingAssignment, ParkingSpace
from .models import VehicleEvent
from .broadcast import broadcast_parking_log_event


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
