# jetson/consumers.py
import json
from typing import Any, Dict, List, Tuple

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.db.models import Q
from events.models import VehicleEvent
from parking.models import ParkingSpace
from parking.services import (
    add_score_from_jetson,
    handle_assignment_from_jetson,
    mark_parking_complete_from_ai,
)
from django.utils import timezone
from django.db import transaction
from channels.generic.websocket import AsyncWebsocketConsumer
import json

JETSON_CONTROL_GROUP = "jetson-control"
PARKING_STATUS_GROUP = "parking-status"

# hello 요청에 응답할 초기 차량 목록(8대, 모두 midsize)
VEHICLES = [
    {"license_plate": "466우5726", "size_class": "midsize"},
    {"license_plate": "770오4703", "size_class": "midsize"},
    {"license_plate": "411수5748", "size_class": "midsize"},
    {"license_plate": "820마2378", "size_class": "midsize"},
    {"license_plate": "932배1741", "size_class": "midsize"},
    {"license_plate": "136수5621", "size_class": "midsize"},
    {"license_plate": "43머8208", "size_class": "midsize"},
    {"license_plate": "13다8208", "size_class": "midsize"},
]


class JetsonIngestConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.channel_layer.group_add(JETSON_CONTROL_GROUP, self.channel_name)

    async def disconnect(self, code):
        await self.channel_layer.group_discard(JETSON_CONTROL_GROUP, self.channel_name)

    async def jetson_control(self, event):
        await self.send(text_data=json.dumps(event["payload"], ensure_ascii=False))

    async def receive(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data or "{}")
        except Exception:
            return

        msg_type = data.get("message_type")

        if msg_type == "hello":
            await self.send(
                text_data=json.dumps(
                    {
                        "message_type": "assignment_request",
                        "vehicles": VEHICLES,
                    },
                    ensure_ascii=False,
                )
            )
            return

        if msg_type == "car_position":
            slot_map: Dict[str, str] = data.get("slot") or {}
            vehicles_in: List[Dict[str, Any]] = data.get("vehicles") or []

            if slot_map:
                await self._apply_slot_status(slot_map)  # 저장만(방송은 signals)

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
                    "origin": "ai",
                }
            )
            return

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
            # 방송은 signals가 처리
            return

        if msg_type == "score":
            plate = (data.get("license_plate") or "").strip()
            score = data.get("score")
            slot_label = (
                data.get("zone_id") or ""
            ).strip()  # Jetson이 보낸 “해당 구역/슬롯”

            if not plate or score is None:
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

            # ✅ “내 차만” 반영: 현재 plate의 배정 슬롯과 Jetson이 보고한 slot_label이 일치할 때만 수락
            assigned_label = await self._get_assigned_label_for_plate(
                plate
            )  # e.g., "B3"
            if (
                slot_label
                and assigned_label
                and slot_label.upper() != assigned_label.upper()
            ):
                # 내 차가 아닌 주차 완료 이벤트 → 무시(ignored)로 응답
                await self.send(
                    text_data=json.dumps(
                        {
                            "message_type": "score_ack",
                            "license_plate": plate,
                            "score": score,
                            "zone_id": slot_label,
                            "status": "ignored",
                            "detail": "slot mismatch (not this vehicle's assigned space)",
                            "expected": assigned_label,
                            "received": slot_label,
                        },
                        ensure_ascii=False,
                    )
                )
                return

            # ✅ “내 차만” 반영은 유지하되, 다른 칸에 주차해도 수락하여 방영/완료 처리
            #    - mismatch 여부만 기록하고 계속 진행
            slot_label = (data.get("zone_id") or "").strip().upper()
            assigned_label = await self._get_assigned_label_for_plate(
                plate
            )  # e.g., "B3"
            mismatch = bool(
                slot_label and assigned_label and slot_label != assigned_label
            )

            # 1) 점수 저장
            ok_score, msg_score = await database_sync_to_async(add_score_from_jetson)(
                plate, int(score)
            )

            # 2) 점수 수신을 '주차 완료'로 간주하여 상태 전환
            #    - slot_label이 오면 그 칸으로 완료 처리 (불일치여도 수락)
            ok_park, msg_park, occupied_label = await database_sync_to_async(
                mark_parking_complete_from_ai
            )(plate, slot_label or None)

            # 3) ACK 응답 (둘 다 성공해야 success)
            used_label = slot_label or assigned_label or occupied_label
            await self.send(
                text_data=json.dumps(
                    {
                        "message_type": "score_ack",
                        "license_plate": plate,
                        "score": int(score),
                        "zone_id": used_label,
                        "status": "success" if (ok_score and ok_park) else "error",
                        "detail": f"{msg_score}; {msg_park}",
                        "mismatch": mismatch,  # ← 불일치 여부 (true/false)
                        "expected": assigned_label,  # ← 원래 배정칸 (예: "B3")
                        "received": slot_label,  # ← 젯슨이 전송한 실제칸 (예: "B2")
                    },
                    ensure_ascii=False,
                )
            )
            return

        if msg_type == "re-assignment":
            plate = (data.get("license_plate") or "").strip()
            new_label = (data.get("assignment") or "").strip()

            if not plate or not new_label:
                await self.send(
                    text_data=json.dumps(
                        {
                            "message_type": "re_assignment_ack",
                            "status": "error",
                            "detail": "license_plate and assignment required",
                        },
                        ensure_ascii=False,
                    )
                )
                return

            ok, msg = await database_sync_to_async(handle_assignment_from_jetson)(
                plate, new_label
            )

            # 개별 소켓 ACK
            await self.send(
                text_data=json.dumps(
                    {
                        "message_type": "re_assignment_ack",
                        "license_plate": plate,
                        "assignment": new_label,
                        "status": "success" if ok else "error",
                        "detail": msg,
                    },
                    ensure_ascii=False,
                )
            )

            # ✅ 모든 뷰어에 방송: 프론트가 추천/표시를 즉시 갱신할 수 있게 함
            await self._broadcast_to_viewers(
                {
                    "message_type": "re-assignment",
                    "license_plate": plate,
                    "assignment": new_label,
                    "status": "success" if ok else "error",
                    "detail": msg,
                    "origin": "ai",
                }
            )
            return
        if msg_type == "exit":
            plate = (data.get("license_plate") or "").strip()
            zone_label = (data.get("zone") or "").strip()  # ex) "B3" 예상

            if not plate:
                await self.send(
                    text_data=json.dumps(
                        {
                            "message_type": "exit_ack",
                            "status": "error",
                            "detail": "license_plate required",
                        },
                        ensure_ascii=False,
                    )
                )
                return

            ok, msg, freed_label = await self._handle_exit_tx(plate, zone_label)

            # 개별 ACK
            await self.send(
                text_data=json.dumps(
                    {
                        "message_type": "exit_ack",
                        "license_plate": plate,
                        "zone": zone_label or None,
                        "freed": freed_label,
                        "status": "success" if ok else "error",
                        "detail": msg,
                    },
                    ensure_ascii=False,
                )
            )

            # 즉시 뷰어에게 반영(신호/시그널이 이미 방송한다면 생략 가능)
            if ok and freed_label:
                await self._broadcast_to_viewers(
                    {
                        "message_type": "parking_space",
                        "spaces": {
                            freed_label: {
                                "status": "free",
                                "size": None,
                                "vehicle_id": None,
                                "license_plate": None,
                            }
                        },
                        "origin": "ai",
                    }
                )
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
    def _get_assigned_label_for_plate(self, plate: str) -> str | None:
        """
        현재 출차 전(ev.exit_time is null)인 차량 중 번호판이 plate인 이벤트의
        배정 슬롯 레이블(예: 'B3')을 반환. 없으면 None.
        """
        ev = (
            VehicleEvent.objects.select_related("vehicle", "assignment__space")
            .filter(vehicle__license_plate=plate, exit_time__isnull=True)
            .order_by("-id")
            .first()
        )
        if not ev:
            return None
        assignment = getattr(ev, "assignment", None)
        if not assignment or not assignment.space:
            return None
        s = assignment.space
        return f"{s.zone}{s.slot_number}"

    async def _broadcast_to_viewers(self, payload: Dict[str, Any]) -> None:
        # ✅ origin 기본값 보정
        if "origin" not in payload:
            payload["origin"] = "ai"
        await self.channel_layer.group_send(
            PARKING_STATUS_GROUP, {"type": "broadcast", "payload": payload}
        )

    @database_sync_to_async
    def _handle_exit_tx(self, plate: str, zone_label: str | None):
        """
        젯슨이 보낸 exit를 기준으로 '내 차만' 안전하게 자동 출차 처리.
        - 현재 진행중인 VehicleEvent(plate, exit_time is null)를 찾고
        - 배정/점유 슬롯을 해결한 뒤
        - VehicleEvent.exit_time, status 갱신
        - ParkingAssignment(end_time, status) 종료
        - ParkingSpace 비우기(status='free', current_vehicle=None)
        """
        with transaction.atomic():
            return self._handle_exit(plate, zone_label)

    def _handle_exit(self, plate: str, zone_label: str | None):
        from events.models import VehicleEvent
        from parking.models import ParkingSpace

        # 1) 활성 이벤트 조회
        ev = (
            VehicleEvent.objects.select_related("vehicle", "assignment__space")
            .filter(vehicle__license_plate=plate, exit_time__isnull=True)
            .order_by("-id")
            .first()
        )
        if not ev:
            return False, "active vehicle_event not found", None

        # 2) 대상 슬롯 탐색 우선순위:
        #   (a) 젯슨이 보낸 zone_label(예: 'B3') → 존재/일치하면 사용
        #   (b) 이벤트의 assignment.space
        #   (c) 현재 점유 중인 슬롯(current_vehicle__license_plate=plate)
        space = None
        parsed = self._parse_slot_label(zone_label) if zone_label else None
        if parsed:
            z, n = parsed
            try:
                space = ParkingSpace.objects.select_related("current_vehicle").get(
                    zone=z, slot_number=n
                )
            except ParkingSpace.DoesNotExist:
                space = None

        if space is None and getattr(ev, "assignment", None) and ev.assignment.space:
            space = ev.assignment.space

        if space is None:
            try:
                space = ParkingSpace.objects.select_related("current_vehicle").get(
                    current_vehicle__license_plate=plate
                )
            except ParkingSpace.DoesNotExist:
                space = None

        # 3) 슬롯/점유 검증 및 정리
        freed_label = None
        if space:
            # 내 차가 점유 중인 슬롯이면 점유 해제
            if (
                getattr(space, "current_vehicle", None)
                and space.current_vehicle
                and space.current_vehicle.license_plate == plate
            ):
                space.current_vehicle = None

            # 상태를 free로
            if space.status != "free":
                space.status = "free"

            space.save(update_fields=["status", "current_vehicle"])
            freed_label = f"{space.zone}{space.slot_number}"

        # 4) 배정 종료
        if getattr(ev, "assignment", None):
            assign = ev.assignment
            # end_time/status 필드명이 다르면 프로젝트 스키마에 맞춰 조정
            if not assign.end_time:
                assign.end_time = timezone.now()
            # 상태값 명세에 맞게(예: 'completed'/'ended')
            if hasattr(assign, "status"):
                assign.status = "completed"
            assign.save(
                update_fields=(
                    ["end_time", "status"]
                    if hasattr(assign, "status")
                    else ["end_time"]
                )
            )

        # 5) 이벤트 종료
        now = timezone.now()
        ev.exit_time = now
        if hasattr(ev, "status"):
            ev.status = "Exit"  # 프로젝트의 상태 문자열 관례에 맞게
        ev.save(
            update_fields=(
                ["exit_time", "status"] if hasattr(ev, "status") else ["exit_time"]
            )
        )

        return True, "exit processed", freed_label

    # 슬롯 레이블 파서: "B3" -> ("B", 3)
    def _parse_slot_label(self, label: str | None):
        if not label:
            return None
        s = label.strip().upper()
        if len(s) < 2:
            return None
        z = s[0]
        num_str = s[1:]
        if not num_str.isdigit():
            return None
        return z, int(num_str)


# =========================
# /ws/parking_status
# =========================
class ParkingStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.channel_layer.group_add("parking-status", self.channel_name)
        # 최초 스냅샷
        space_payload = await self._snapshot_space_all()
        await self.send(
            text_data=json.dumps(
                {
                    "message_type": "parking_space",
                    "spaces": space_payload,
                    "origin": "system",
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
                    "origin": "system",
                },
                ensure_ascii=False,
            )
        )

    async def disconnect(self, code):
        await self.channel_layer.group_discard("parking-status", self.channel_name)

    async def broadcast(self, event):
        await self.send(text_data=json.dumps(event["payload"], ensure_ascii=False))

    # ---- 스냅샷 헬퍼 ----
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
