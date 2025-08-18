# events/broadcast.py
import json

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from events.consumers import ParkingLogConsumer
from events.serializers import VehicleEventSerializer


def broadcast_parking_log_event(ev) -> None:
    """주차 로그 1건을 parking_logs 그룹에 push"""
    payload = json.dumps(
        VehicleEventSerializer(ev).data, ensure_ascii=False, default=str
    )
    async_to_sync(get_channel_layer().group_send)(
        ParkingLogConsumer.group_name,
        {"type": "vehicle_event", "data": payload},
    )
