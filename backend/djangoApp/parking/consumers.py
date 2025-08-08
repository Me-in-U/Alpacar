# app/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer


class CarPositionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        # 모든 클라이언트에게 같은 그룹(옵션: 인증별 분기)
        await self.channel_layer.group_add("car_position", self.channel_name)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("car_position", self.channel_name)

    async def receive(self, text_data):
        # 클라이언트(Jetson)로부터 받은 메시지를
        # 동일 그룹의 다른 클라이언트(웹)로 broadcast
        await self.channel_layer.group_send(
            "car_position",
            {
                "type": "car_position.update",
                "message": text_data,
            },
        )

    async def car_position_update(self, event):
        # 실제 웹 클라이언트로 전송
        await self.send(text_data=event["message"])
