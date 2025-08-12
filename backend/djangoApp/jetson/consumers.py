# jetson/consumers.py
import json
from typing import Any, Dict, List, Tuple

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.db.models import Q
from events.models import VehicleEvent
from parking.models import ParkingSpace
from parking.services import add_score_from_jetson, handle_assignment_from_jetson

JETSON_GROUP = "jetson-ws"
CAR_POSITION_GROUP = "car_position"
PARKING_SPACE_GROUP = "parking_space"
ACTIVE_VEHICLES_GROUP = "active_vehicles"


class JetsonAssignConsumer(AsyncWebsocketConsumer):
    """
    /ws/jetson: Jetson/프런트가 모두 붙는 단일 엔드포인트
    - 장고→젯슨 요청 브로드캐스트 수신: jetson_request
    - 젯슨 텔레메트리 {slot, vehicles} 수신 → 슬롯/차량 팬아웃
    - assignment/score 명령 수신 → 서비스 호출
    - 보기용 그룹(car_position / parking_space / active_vehicles)에도 조인 → 동일 소켓으로 수신
    """

    async def connect(self):
        await self.accept()
        # 제어/요청 그룹
        await self.channel_layer.group_add(JETSON_GROUP, self.channel_name)
        # 보기용 그룹(프런트가 /ws/jetson 하나만으로 수신)
        await self.channel_layer.group_add(CAR_POSITION_GROUP, self.channel_name)
        await self.channel_layer.group_add(PARKING_SPACE_GROUP, self.channel_name)
        await self.channel_layer.group_add(ACTIVE_VEHICLES_GROUP, self.channel_name)

        # ✅ 접속 직후 1회: 현재 DB 스냅샷을 이 소켓으로 직접 전송
        space_payload = await self._snapshot_space_all()
        await self.send(text_data=json.dumps(space_payload, ensure_ascii=False))

        active_payload = await self._snapshot_active_vehicles()
        await self.send(text_data=json.dumps(active_payload, ensure_ascii=False))

    async def disconnect(self, code):
        await self.channel_layer.group_discard(JETSON_GROUP, self.channel_name)
        await self.channel_layer.group_discard(CAR_POSITION_GROUP, self.channel_name)
        await self.channel_layer.group_discard(PARKING_SPACE_GROUP, self.channel_name)
        await self.channel_layer.group_discard(ACTIVE_VEHICLES_GROUP, self.channel_name)

    # 장고→젯슨 브로드캐스트
    async def jetson_request(self, event):
        await self.send(text_data=json.dumps(event["payload"], ensure_ascii=False))

        # 보기용 그룹 이벤트 → 그대로 send

    async def car_position_update(self, event):
        await self.send(text_data=event["message"])  # JSON 문자열(배열)

    async def parking_space_update(self, event):
        await self.send(text_data=json.dumps(event["payload"], ensure_ascii=False))

    async def active_vehicles_update(self, event):
        await self.send(text_data=json.dumps(event["payload"], ensure_ascii=False))

    # 젯슨→장고 결과 수신
    async def receive(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data or "{}")
        except Exception:
            return

        message_type = data.get("message_type")

        # 1) 슬롯/차량 텔레메트리 (message_type 없음, 혹은 "telemetry")
        if message_type == "car_position":
            await self._handle_telemetry_payload(data)
            return

        # 2) 배정 확정 보고
        if message_type == "assignment":
            plate = data.get("license_plate")
            slot_label = data.get("assignment")
            if not (plate and slot_label):
                await self.send(
                    text_data=json.dumps(
                        {
                            "message_type": "assignment_ack",
                            "status": "error",
                            "detail": "license_plate and assignment required",
                        },
                        ensure_ascii=False,
                    )
                )
                return

            ok, msg = await database_sync_to_async(handle_assignment_from_jetson)(
                plate, slot_label
            )
            await self.send(
                text_data=json.dumps(
                    {
                        "message_type": "assignment_ack",
                        "license_plate": plate,
                        "assignment": slot_label,
                        "status": "success" if ok else "error",
                        "detail": msg,
                    },
                    ensure_ascii=False,
                )
            )
            return
        # 3) 점수/스코어 보고
        if message_type == "score":
            plate = data.get("license_plate")
            score = data.get("score")
            if plate is None or score is None:
                await self.send(
                    text_data=json.dumps(
                        {
                            "message_type": "score_ack",
                            "status": "error",
                            "detail": "license_plate and score required",
                        },
                        ensure_ascii=False,
                    )
                )
                return
            try:
                score = int(score)
            except Exception:
                await self.send(
                    text_data=json.dumps(
                        {
                            "message_type": "score_ack",
                            "status": "error",
                            "detail": "score must be integer",
                        },
                        ensure_ascii=False,
                    )
                )
                return

            ok, msg = await database_sync_to_async(add_score_from_jetson)(plate, score)
            await self.send(
                text_data=json.dumps(
                    {
                        "message_type": "score_ack",
                        "license_plate": plate,
                        "score": score,
                        "status": "success" if ok else "error",
                        "detail": msg,
                    },
                    ensure_ascii=False,
                )
            )
            return

    # ──────────────────────────────────────────────────────────────
    # DB 스냅샷 헬퍼 (초기 전송/요청시 재사용)

    @database_sync_to_async
    def _snapshot_space_all(self) -> Dict[str, Any]:
        rows = ParkingSpace.objects.values(
            "zone",
            "slot_number",
            "size_class",
            "status",
            "current_vehicle_id",
            "current_vehicle__license_plate",
        ).order_by("zone", "slot_number")
        out: Dict[str, Any] = {}
        for r in rows:
            key = f"{r['zone']}{r['slot_number']}"
            out[key] = {
                "status": r["status"],  # "free" | "occupied" | "reserved"
                "size": r["size_class"],  # string | None
                "vehicle_id": r["current_vehicle_id"],
                "license_plate": r["current_vehicle__license_plate"],
            }
        return out

    @database_sync_to_async
    def _snapshot_active_vehicles(self) -> Dict[str, Any]:
        qs = (
            VehicleEvent.objects.select_related("vehicle")
            .filter(exit_time__isnull=True)
            .order_by("-id")
        )
        results = []
        for ev in qs:
            assigned = None
            assignment = getattr(ev, "assignment", None)
            if assignment and assignment.space:
                s = assignment.space
                assigned = {
                    "zone": s.zone,
                    "slot_number": s.slot_number,
                    "label": f"{s.zone}{s.slot_number}",
                    "status": s.status,
                }
            results.append(
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
        return {"results": results}

    # ── 텔레메트리 처리 ────────────────────────────────────────────────
    #  { "slot": { "B1": "occupied", ... }, "vehicles": [ ... ] }
    async def _handle_telemetry_payload(self, data: Dict[str, Any]):
        slot_map: Dict[str, str] = data.get("slot") or {}
        vehicles_in: List[Dict[str, Any]] = data.get("vehicles") or []

        if slot_map:
            await self._apply_slot_status(slot_map)

        # 슬롯 스냅샷 팬아웃 (SpacePayload 맵)
        space_payload = await self._build_space_snapshot_from_map(slot_map)
        if space_payload is not None:
            await self.channel_layer.group_send(
                PARKING_SPACE_GROUP,
                {"type": "parking_space.update", "payload": space_payload},
            )

        # 차량 오버레이 팬아웃 (배열)
        def _flatten_corners(corners):
            out = []
            for pt in corners or []:
                out.extend(pt)
            return out

        vehicles_out = []
        for v in vehicles_in:
            center = v.get("center") or {}
            vehicles_out.append(
                {
                    "track_id": str(v.get("plate") or ""),
                    "center": [center.get("x", 0), center.get("y", 0)],
                    "corners": _flatten_corners(v.get("corners") or []),
                    "state": v.get("state"),
                    "suggested": v.get("suggested") or "",
                }
            )

        await self.channel_layer.group_send(
            CAR_POSITION_GROUP,
            {
                "type": "car_position.update",
                "message": json.dumps(vehicles_out, ensure_ascii=False),
            },
        )

    @database_sync_to_async
    def _apply_slot_status(self, slot_map: Dict[str, str]) -> None:
        """
        슬롯 레이블(예: "B3") → DB 반영.
        - status 필드를 Jetson에서 오는 'free|reserved|occupied' 로 동기화
        """
        # 레이블을 (zone, slot_number)로 분리
        to_update: List[Tuple[str, int, str]] = []
        for label, status in slot_map.items():
            if not label or len(label) < 2:
                continue
            zone = label[0]
            try:
                num = int(label[1:])
            except ValueError:
                continue
            to_update.append((zone, num, status))

        # 개별 업데이트 (빈도 높으면 bulk 전략으로 최적화)
        for zone, num, status in to_update:
            try:
                ps = ParkingSpace.objects.get(zone=zone, slot_number=num)
                # 값이 달라질 때만 저장하여 write 줄임
                if ps.status != status:
                    ps.status = status
                    ps.save(update_fields=["status"])
            except ParkingSpace.DoesNotExist:
                continue

    @database_sync_to_async
    def _build_space_snapshot_from_map(
        self, slot_map: Dict[str, str]
    ) -> Dict[str, Any] | None:
        if not slot_map:
            return None

        q = Q()
        for label in slot_map.keys():
            if not label or len(label) < 2:
                continue
            zone = label[0]
            try:
                num = int(label[1:])
            except ValueError:
                continue
            q |= Q(zone=zone, slot_number=num)

        rows = ParkingSpace.objects.filter(q).values(
            "zone",
            "slot_number",
            "size_class",
            "status",
            "current_vehicle_id",
            "current_vehicle__license_plate",
        )

        out: Dict[str, Any] = {}
        for r in rows:
            key = f"{r['zone']}{r['slot_number']}"
            out[key] = {
                "status": slot_map.get(key, r["status"]),
                "size": r["size_class"],
                "vehicle_id": r["current_vehicle_id"],
                "license_plate": r["current_vehicle__license_plate"],
            }

        for label, status in slot_map.items():
            out.setdefault(
                label,
                {
                    "status": status,
                    "size": None,
                    "vehicle_id": None,
                    "license_plate": None,
                },
            )
        return out
