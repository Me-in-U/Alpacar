from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone

from .broadcast import broadcast_plate

# 프로젝트 스키마에 맞는 모델 import
from parking.models import ParkingAssignment
from events.models import VehicleEvent


# ---- 상태 상수 유틸 (대소문자 혼용 대비) ----
def _norm(s):
    return (s or "").strip().lower()


ASSIGNED = {"assigned", "ASSIGNED".lower()}
ENDED = {"completed", "released", "ended", "cancelled"}


# ---- pre_save: 변경 전 상태/슬롯 기억 ----
@receiver(pre_save, sender=ParkingAssignment)
def pa_pre_save(sender, instance: ParkingAssignment, **kwargs):
    if not instance.pk:
        instance.__prev_status = None
        instance.__prev_space_id = None
        return
    try:
        old = sender.objects.select_related("space", "entrance_event__vehicle").get(
            pk=instance.pk
        )
        instance.__prev_status = getattr(old, "status", None)
        instance.__prev_space_id = old.space_id
    except sender.DoesNotExist:
        instance.__prev_status = None
        instance.__prev_space_id = None


# ---- post_save: 배정 생성/변경에 따른 방송 ----
@receiver(post_save, sender=ParkingAssignment)
def pa_post_save(sender, instance: ParkingAssignment, created, **kwargs):
    space = getattr(instance, "space", None)
    vehicle = getattr(getattr(instance, "entrance_event", None), "vehicle", None)
    plate = getattr(vehicle, "license_plate", "") if vehicle else ""

    label = f"{space.zone}{space.slot_number}" if space else None
    prev_status = getattr(instance, "__prev_status", None)
    prev_space_id = getattr(instance, "__prev_space_id", None)

    cur = _norm(getattr(instance, "status", None))
    prev = _norm(prev_status)

    # 1) 새로 ASSIGNED 되면 표시
    if created and cur in ASSIGNED and label and plate:
        broadcast_plate(label, plate)
        return

    # 2) 공간 변경(재배정) 시: 이전 슬롯 지우고 새 슬롯 표시
    if not created and prev_space_id and space and prev_space_id != space.id:
        try:
            from parking.models import ParkingSpace

            old_space = ParkingSpace.objects.get(pk=prev_space_id)
            old_label = f"{old_space.zone}{old_space.slot_number}"
            broadcast_plate(old_label, "")  # 이전 슬롯 지움
        except Exception:
            pass
        if cur in ASSIGNED and plate:
            broadcast_plate(label, plate)  # 새 슬롯 표시

    # 3) 상태 변경에 따른 표시/지움
    if not created and prev != cur:
        if cur in ASSIGNED and label and plate:
            broadcast_plate(label, plate)  # (재)활성화
        elif cur in ENDED and label:
            broadcast_plate(label, "")  # 종료 → 지움


# ---- 삭제 시(드물지만) 슬롯 지우기 ----
@receiver(post_delete, sender=ParkingAssignment)
def pa_post_delete(sender, instance: ParkingAssignment, **kwargs):
    space = getattr(instance, "space", None)
    if space:
        label = f"{space.zone}{space.slot_number}"
        broadcast_plate(label, "")


# ---- VehicleEvent 출차 시(보호적): 배정 종료 신호가 누락돼도 지우기 ----
@receiver(post_save, sender=VehicleEvent)
def ve_post_save(sender, instance: VehicleEvent, created, **kwargs):
    # 출차가 기록되면, 연결된 배정의 슬롯을 지우는 보조 장치
    if created:
        return
    if instance.exit_time:
        assign = getattr(instance, "assignment", None)
        if assign and assign.space:
            label = f"{assign.space.zone}{assign.space.slot_number}"
            broadcast_plate(label, "")
