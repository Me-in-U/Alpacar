# jetson/feed.py
from typing import Dict, List, Optional

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models import Q

from events.models import VehicleEvent
from parking.models import ParkingSpace
from parking.origin import get_ws_origin

PARKING_STATUS_GROUP = "parking-status"


def _with_origin(payload: dict) -> dict:
    origin = get_ws_origin() or "system"
    if "origin" not in payload:
        payload["origin"] = origin
    return payload


def _parse_label(label: Optional[str]) -> Optional[tuple[str, int]]:
    if not label:
        return None
    s = label.strip().upper()
    if len(s) < 2:
        return None
    zone, num = s[0], s[1:]
    if not num.isdigit():
        return None
    return zone, int(num)


def _build_space_snapshot(labels: Optional[List[str]] = None) -> Dict[str, dict]:
    qs = ParkingSpace.objects.all()
    if labels:
        q = Q()
        for label in labels:
            parsed = _parse_label(label)
            if parsed:
                z, n = parsed
                q |= Q(zone=z, slot_number=n)
        if q:
            qs = qs.filter(q)

    rows = qs.values(
        "zone",
        "slot_number",
        "size_class",
        "status",
        "current_vehicle_id",
        "current_vehicle__license_plate",
    )

    out: Dict[str, dict] = {}
    for r in rows:
        key = f"{r['zone']}{r['slot_number']}"
        out[key] = {
            "status": r["status"],
            "size": r["size_class"],
            "vehicle_id": r["current_vehicle_id"],
            "license_plate": r["current_vehicle__license_plate"],
        }
    return out


def _build_active_vehicles_snapshot() -> dict:
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

        # ✅ KST(+09:00)로 변환하여 문자열화
        entrance_iso = (
            timezone.localtime(ev.entrance_time).isoformat()
            if ev.entrance_time
            else None
        )

        results.append(
            {
                "id": ev.id,
                "vehicle_id": ev.vehicle_id,
                "license_plate": ev.vehicle.license_plate,
                "entrance_time": entrance_iso,
                "status": ev.status,
                "assigned_space": assigned,
            }
        )
    return {"results": results}


def broadcast_parking_space(labels: list[str] | None = None) -> None:
    payload = {"message_type": "parking_space", "spaces": _build_space_snapshot(labels)}
    async_to_sync(get_channel_layer().group_send)(
        PARKING_STATUS_GROUP,
        {"type": "broadcast", "payload": _with_origin(payload)},
    )


def broadcast_active_vehicles() -> None:
    payload = {
        "message_type": "active_vehicles",
        "results": _build_active_vehicles_snapshot().get("results", []),
    }
    async_to_sync(get_channel_layer().group_send)(
        PARKING_STATUS_GROUP,
        {"type": "broadcast", "payload": _with_origin(payload)},
    )
