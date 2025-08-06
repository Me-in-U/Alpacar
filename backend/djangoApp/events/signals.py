# events/signals.py
import json
from django.dispatch import receiver
from django.db.models.signals import post_save
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from events.consumers import ParkingLogConsumer

from .models import VehicleEvent
from .serializers import VehicleEventSerializer


@receiver(post_save, sender=VehicleEvent)
def broadcast_vehicle_event(sender, instance, created, **kwargs):
    if not created:
        return
    serializer = VehicleEventSerializer(instance)
    data = json.dumps(serializer.data)
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        ParkingLogConsumer.group_name,
        {
            "type": "vehicle_event",
            "data": data,
        },
    )
