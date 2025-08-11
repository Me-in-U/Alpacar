# parking\consumers.py
import asyncio
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from events.models import VehicleEvent
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
    {
      "A1": {
        "status": "free|reserved|occupied",
        "size": "compact|midsize|suv",
        "vehicle_id": 123 or null,
        "license_plate": "12가3456" or null
      },
      ...
    } 형태로 브로드캐스트
    """

    POLL_SEC = 1.0

    async def connect(self):
        await self.accept()
        await self.channel_layer.group_add("parking_space", self.channel_name)
        self._task = asyncio.create_task(self._poll_loop())

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("parking_space", self.channel_name)
        try:
            self._task.cancel()
        except Exception:
            pass

    async def _poll_loop(self):
        last_snapshot = None
        while True:
            try:
                snapshot = await self._fetch_snapshot()
                if snapshot != last_snapshot:
                    await self.channel_layer.group_send(
                        "parking_space",
                        {"type": "parking_space.update", "payload": snapshot},
                    )
                    last_snapshot = snapshot
            except Exception as e:
                print("[ParkingSpaceConsumer] poll error:", e)
            await asyncio.sleep(self.POLL_SEC)

    @database_sync_to_async
    def _fetch_snapshot(self):
        # DB → dict 변환: "A1","A2"… 키로 매핑
        rows = (
            ParkingSpace.objects.all()
            .values(
                "zone",
                "slot_number",
                "size_class",
                "status",
                # 🔽 차량 정보까지 포함
                "current_vehicle_id",
                "current_vehicle__license_plate",
            )
            .order_by("zone", "slot_number")
        )
        out = {}
        for r in rows:
            key = f"{r['zone']}{r['slot_number']}"
            out[key] = {
                "status": r["status"],
                "size": r["size_class"],
                "vehicle_id": r["current_vehicle_id"],  # None 가능
                "license_plate": r["current_vehicle__license_plate"],  # None 가능
            }
        return out

    async def parking_space_update(self, event):
        await self.send(text_data=json.dumps(event["payload"], ensure_ascii=False))


class ActiveVehiclesConsumer(AsyncWebsocketConsumer):
    """
    미출차 이벤트(Exit 미포함) 스냅샷을 전송.
    - 방송 트리거가 들어오면 최신 스냅샷 push
    - (옵션) 폴링 루프도 가능하지만, 신뢰도는 트리거 push가 더 좋음
    """

    async def connect(self):
        await self.accept()
        await self.channel_layer.group_add("active_vehicles", self.channel_name)
        # 최초 스냅샷 즉시 전송
        data = await self._fetch_snapshot()
        await self.send(text_data=json.dumps({"results": data}, ensure_ascii=False))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("active_vehicles", self.channel_name)

    async def active_vehicles_update(self, event):
        # 트리거 수신 시 최신 스냅샷 재전송
        data = await self._fetch_snapshot()
        await self.send(text_data=json.dumps({"results": data}, ensure_ascii=False))

    @database_sync_to_async
    def _fetch_snapshot(self):
        qs = (
            VehicleEvent.objects.select_related("vehicle")
            .filter(exit_time__isnull=True)
            .order_by("-id")
        )
        out = []
        for ev in qs:
            assigned = None
            assignment = getattr(ev, "assignment", None)
            if assignment and assignment.space:
                assigned = {
                    "zone": assignment.space.zone,
                    "slot_number": assignment.space.slot_number,
                    "label": f"{assignment.space.zone}{assignment.space.slot_number}",
                    "status": assignment.space.status,
                }
            out.append(
                {
                    "id": ev.id,
                    "vehicle_id": ev.vehicle_id,
                    "license_plate": ev.vehicle.license_plate,
                    "entrance_time": (
                        ev.entrance_time.isoformat() if ev.entrance_time else None
                    ),
                    "status": ev.status,
                    "assigned_space": assigned,
                }
            )
        return out
