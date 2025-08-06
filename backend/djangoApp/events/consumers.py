# events/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .serializers import VehicleEventSerializer


class ParkingLogConsumer(AsyncWebsocketConsumer):
    group_name = "parking_logs"

    async def connect(self):
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # 그룹으로부터 이벤트 수신
    async def vehicle_event(self, event):
        # event["data"]는 이미 JSON 직렬화된 문자열
        await self.send(text_data=event["data"])
