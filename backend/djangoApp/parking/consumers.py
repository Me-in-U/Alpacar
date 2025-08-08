# parking\consumers.py
import asyncio
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from parking.models import ParkingSpace


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


class ParkingSpaceConsumer(AsyncWebsocketConsumer):
    """
    parking_space 테이블을 주기적으로 폴링해서
    { "A1": {"occupied": true, "size": "suv"}, ... } 형태로 브로드캐스트
    """

    POLL_SEC = 1.0  # 추측: 1초 간격 폴링 (원하면 0.5~2.0초로 조절)

    async def connect(self):
        await self.accept()
        await self.channel_layer.group_add("parking_space", self.channel_name)
        # 폴링 루프 시작
        self._task = asyncio.create_task(self._poll_loop())

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("parking_space", self.channel_name)
        try:
            self._task.cancel()
        except Exception:
            pass

    async def _poll_loop(self):
        # 최초 상태를 기억해서 변경된 경우만 푸시 (불필요 트래픽 절감, 대략 90%↓)
        last_snapshot = None
        while True:
            try:
                snapshot = await self._fetch_snapshot()
                if snapshot != last_snapshot:
                    await self.channel_layer.group_send(
                        "parking_space",
                        {"type": "parking_space.update", "payload": snapshot},
                    )
                    print("[ParkingSpaceConsumer] Updated parking space snapshot")
                    print(snapshot)
                    last_snapshot = snapshot
            except Exception as e:
                # 필요 시 로깅
                print("[ParkingSpaceConsumer] poll error:", e)
            await asyncio.sleep(self.POLL_SEC)

    @database_sync_to_async
    def _fetch_snapshot(self):
        # DB → dict 변환: "A1","A2"… 키로 매핑
        # _fetch_snapshot()
        rows = (
            ParkingSpace.objects.all()
            .values("zone", "slot_number", "size_class", "status")
            .order_by("zone", "slot_number")
        )
        out = {}
        for r in rows:
            key = f"{r['zone']}{r['slot_number']}"
            out[key] = {
                "status": r["status"],  # "free" | "occupied" | "reserved"
                "size": r["size_class"],
            }
        return out

    async def parking_space_update(self, event):
        await self.send(text_data=json.dumps(event["payload"], ensure_ascii=False))
