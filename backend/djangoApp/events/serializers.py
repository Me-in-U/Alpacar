# events/serializers.py
from rest_framework import serializers
from .models import VehicleEvent


class VehicleEventSerializer(serializers.ModelSerializer):
    vehicle_id = serializers.IntegerField(source="vehicle.id", read_only=True)
    license_plate = serializers.CharField(
        source="vehicle.license_plate", read_only=True
    )

    # 코드값('Entrance'|'Parking'|'Exit') 그대로
    status = serializers.CharField(read_only=True)
    # 표시용 한글
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
            "status",  # 코드값 → 프론트의 class 매칭 정상화
            "status_display",  # 필요 시 화면 표시용
            "assigned_space",
        ]

    def get_assigned_space(self, obj: VehicleEvent):
        """
        - 배정이 있었으면 label은 항상 보여줌(과거 기록 유지).
        - 단, 이벤트가 '출차' 상태(= exit_time 있음)이면 status는 무조건 'free'로 고정해서 표시.
        - 그 외(미출차)엔 현재 슬롯의 status를 그대로 표시(reserved/occupied/free).
        """
        pa = getattr(obj, "assignment", None)
        sp = getattr(pa, "space", None) if pa else None
        if not sp:
            # 정말로 배정이 없었던 케이스만 None
            return None

        if obj.exit_time:
            status_for_log = "free"
        else:
            # 미출차는 실제 슬롯 상태 그대로
            status_for_log = sp.status

        return {
            "zone": sp.zone,
            "slot_number": sp.slot_number,
            "label": f"{sp.zone}{sp.slot_number}",
            "status": status_for_log,
        }
