# events/broadcast.py (새 파일)
import json

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .consumers import ParkingLogConsumer
from .serializers import VehicleEventSerializer


def broadcast_active_vehicles():
    """
    active_vehicles 그룹에 '업데이트해!' 신호만 보냄.
    실제 스냅샷은 Consumer에서 조회하여 전송.
    """
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "active_vehicles",
        {"type": "active_vehicles.update"},
    )


def broadcast_parking_log_event(ev):
    payload = json.dumps(
        VehicleEventSerializer(ev).data, ensure_ascii=False, default=str
    )
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        ParkingLogConsumer.group_name,
        {"type": "vehicle_event", "data": payload},
    )
