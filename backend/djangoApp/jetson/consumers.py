# jetson/consumers.py
import json
from typing import Any, Dict, List, Tuple

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.db.models import Q
from events.models import VehicleEvent
from parking.models import ParkingSpace
from parking.services import add_score_from_jetson, handle_assignment_from_jetson

# 그룹 이름 분리
JETSON_CONTROL_GROUP = "jetson-control"  # 장고 -> 젯슨 제어/요청 브로드캐스트
PARKING_STATUS_GROUP = "parking-status"  # 장고 -> 프론트 상태 브로드캐스트


class JetsonIngestConsumer(AsyncWebsocketConsumer):
    """
    /ws/jetson/ : Jetson만 연결 (수신용)
    - 장고 -> 젯슨 제어(Request) 수신: jetson_control
    - 젯슨 -> 장고: car_position / assignment / score 처리
      * DB 반영 후, /ws/parking_status 구독자들에게 브로드캐스트
    """

    async def connect(self):
        await self.accept()
        # 젯슨은 제어 그룹에 참가 → 장고가 보낸 request_assignment 등을 받음
        await self.channel_layer.group_add(JETSON_CONTROL_GROUP, self.channel_name)

    async def disconnect(self, code):
        await self.channel_layer.group_discard(JETSON_CONTROL_GROUP, self.channel_name)

    # 장고 → 젯슨 제어 브로드캐스트 (예: request_assignment)
    async def jetson_control(self, event):
        await self.send(text_data=json.dumps(event["payload"], ensure_ascii=False))

    # 젯슨 → 장고
    async def receive(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data or "{}")
        except Exception:
            return

        msg_type = data.get("message_type")

        # 1) 차량/슬롯 상태 프레임 (젯슨에서 주기적으로 보냄)
        if msg_type == "car_position":
            # payload: { slot: {A1:"free"|...}, vehicles: [...] }
            slot_map: Dict[str, str] = data.get("slot") or {}
            vehicles_in: List[Dict[str, Any]] = data.get("vehicles") or []

            if slot_map:
                await self._apply_slot_status(slot_map)

            # Front에 보낼 포맷으로 변환
            # A) 슬롯 스냅샷
            space_payload = await self._build_space_snapshot_from_map(slot_map)
            if space_payload is None:
                space_payload = await self._snapshot_space_all()

            await self._broadcast_to_viewers(
                {
                    "message_type": "parking_space",
                    "spaces": space_payload,
                }
            )

            # B) 차량 오버레이
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

            await self._broadcast_to_viewers(
                {
                    "message_type": "car_position",
                    "vehicles": vehicles_out,
                }
            )
            return

        # 2) 배정 확정(젯슨 판단/권고에 따른 회신)
        if msg_type == "assignment":
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

            # 성공 시, 최신 슬롯/활성차량을 프런트로 브로드캐스트
            if ok:
                await self._broadcast_space_refresh([slot_label])
                await self._broadcast_active_vehicles()
            return

        # 3) 점수 보고(주차 완료 판단)
        if msg_type == "score":
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

            # 점수 반영 후 활성 차량 갱신 브로드캐스트
            await self._broadcast_active_vehicles()
            return

    # ---------- 내부 유틸/DB ----------
    @database_sync_to_async
    def _apply_slot_status(self, slot_map: Dict[str, str]) -> None:
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
        for zone, num, status in to_update:
            try:
                ps = ParkingSpace.objects.get(zone=zone, slot_number=num)
                if ps.status != status:
                    ps.status = status
                    ps.save(update_fields=["status"])
            except ParkingSpace.DoesNotExist:
                continue

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
                "status": r["status"],
                "size": r["size_class"],
                "vehicle_id": r["current_vehicle_id"],
                "license_plate": r["current_vehicle__license_plate"],
            }
        return out

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

    async def _broadcast_to_viewers(self, payload: Dict[str, Any]) -> None:
        await self.channel_layer.group_send(
            PARKING_STATUS_GROUP,
            {"type": "broadcast", "payload": payload},
        )

    async def _broadcast_space_refresh(self, labels: List[str] | None) -> None:
        # labels가 지정되면 해당 슬롯만, 아니면 전체
        if labels:
            space_map = await self._build_space_snapshot_from_map(
                {k: "" for k in labels}
            )
        else:
            space_map = await self._snapshot_space_all()
        await self._broadcast_to_viewers(
            {"message_type": "parking_space", "spaces": space_map}
        )

    async def _broadcast_active_vehicles(self) -> None:
        active = await self._snapshot_active_vehicles()
        await self._broadcast_to_viewers(
            {"message_type": "active_vehicles", "results": active.get("results", [])}
        )


# =========================
# (2) 프론트 시청자: /ws/parking_status
# =========================
class ParkingStatusConsumer(AsyncWebsocketConsumer):
    """
    /ws/parking_status : 관리자/사용자 프런트가 구독
    - 접속 직후: parking_space(전체), active_vehicles 스냅샷 1회 송신
    - 이후: 그룹 브로드캐스트(broadcast) 수신 → 그대로 내려줌
    """

    async def connect(self):
        await self.accept()
        await self.channel_layer.group_add(PARKING_STATUS_GROUP, self.channel_name)

        # 최초 스냅샷
        space_payload = await self._snapshot_space_all()
        await self.send(
            text_data=json.dumps(
                {
                    "message_type": "parking_space",
                    "spaces": space_payload,
                },
                ensure_ascii=False,
            )
        )

        active_payload = await self._snapshot_active_vehicles()
        await self.send(
            text_data=json.dumps(
                {
                    "message_type": "active_vehicles",
                    "results": active_payload.get("results", []),
                },
                ensure_ascii=False,
            )
        )

    async def disconnect(self, code):
        await self.channel_layer.group_discard(PARKING_STATUS_GROUP, self.channel_name)

    # 그룹 브로드캐스트 공통 엔트리포인트
    async def broadcast(self, event):
        await self.send(text_data=json.dumps(event["payload"], ensure_ascii=False))

    # ---- 스냅샷 헬퍼 (JetsonIngest와 동일 구현 재사용) ----
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
                "status": r["status"],
                "size": r["size_class"],
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
