# events/serializers.py (개선본)
from __future__ import annotations

from typing import Any, Dict, Optional, TypedDict

from rest_framework import serializers

from .models import VehicleEvent

# ── 상태 코드 상수 ──
STATUS_ENTRANCE = "Entrance"
STATUS_PARKING = "Parking"
STATUS_EXIT = "Exit"

SPACE_FREE = "free"  # 로그용 강제 상태
SPACE_RESERVED = "reserved"
SPACE_OCCUPIED = "occupied"


class AssignedSpaceOut(TypedDict, total=False):
    zone: str
    slot_number: int
    label: str
    status: str


class VehicleEventSerializer(serializers.ModelSerializer):
    """
    VehicleEvent 단건 직렬화기.
    - 차량 식별자/번호판 노출
    - 상태 코드/표시 문자열 동시 제공
    - assigned_space: 배정된 슬롯의 과거 스냅샷 성격으로 반환
    """

    vehicle_id = serializers.IntegerField(source="vehicle.id", read_only=True)
    license_plate = serializers.CharField(
        source="vehicle.license_plate", read_only=True
    )

    status = serializers.CharField(read_only=True)  # 코드값 그대로
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    assigned_space = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = VehicleEvent
        fields = [
            "id",
            "vehicle_id",
            "license_plate",
            "entrance_time",
            "parking_time",
            "exit_time",
            "status",
            "status_display",
            "assigned_space",
        ]

    def get_assigned_space(self, obj: VehicleEvent) -> Optional[AssignedSpaceOut]:
        """
        반환 규칙:
        - 배정이 없으면 None
        - 출차 이벤트로 간주되면(status == 'Exit' 또는 exit_time 존재) status는 'free'로 고정
        - 미출차면 실제 슬롯 상태 사용(reserved/occupied/free)
        주의: N+1 방지를 위해 뷰에서 select_related("vehicle", "assignment__space") 권장
        """
        # assignment 또는 space가 없으면 None
        pa = getattr(obj, "assignment", None)
        if pa is None:
            return None

        sp = getattr(pa, "space", None)
        if sp is None:
            return None

        # 출차 판정 강화: status 코드와 exit_time 둘 다 고려
        is_exited = (getattr(obj, "status", None) == STATUS_EXIT) or bool(
            getattr(obj, "exit_time", None)
        )

        if is_exited:
            status_for_log = SPACE_FREE
        else:
            # 방어적: 슬롯 상태가 비정상/결측이면 free로 폴백
            sp_status = getattr(sp, "status", None)
            status_for_log = (
                sp_status
                if sp_status in {SPACE_RESERVED, SPACE_OCCUPIED, SPACE_FREE}
                else SPACE_FREE
            )

        label = f"{sp.zone}{sp.slot_number}"
        return AssignedSpaceOut(
            zone=sp.zone,
            slot_number=sp.slot_number,
            label=label,
            status=status_for_log,
        )
