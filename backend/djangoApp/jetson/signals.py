# events/signals.py (추가/보강)
from django.db.models.signals import post_save
from django.dispatch import receiver

from jetson.broadcast import send_request_assignment

from .models import VehicleEvent


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
