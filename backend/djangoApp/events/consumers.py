# events/consumers.py
import json

from channels.generic.websocket import AsyncWebsocketConsumer

from .serializers import VehicleEventSerializer


class ParkingLogConsumer(AsyncWebsocketConsumer):
    group_name = "parking_logs"

    async def connect(self):
        print(
            f"[DEBUG] ParkingLogConsumer.connect 호출, channel_name={self.channel_name}, group_name={self.group_name}"
        )
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        print(
            f"[DEBUG] ParkingLogConsumer.disconnect 호출, close_code={close_code}, channel_name={self.channel_name}"
        )
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # 그룹으로부터 이벤트 수신
    async def vehicle_event(self, event):
        print(f"[DEBUG] ParkingLogConsumer.vehicle_event 호출, event={event}")
        # event["data"]는 이미 JSON 직렬화된 문자열
        await self.send(text_data=event["data"])
