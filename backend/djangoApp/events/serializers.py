# events/serializers.py
from rest_framework import serializers
from .models import VehicleEvent


class VehicleEventSerializer(serializers.ModelSerializer):
    vehicle_id = serializers.IntegerField(source="vehicle.id", read_only=True)
    license_plate = serializers.CharField(
        source="vehicle.license_plate", read_only=True
    )
    location = serializers.CharField(source="vehicle.model.model_name", read_only=True)
    status = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = VehicleEvent
        fields = [
            "id",
            "vehicle_id",
            "license_plate",
            "location",
            "entrance_time",
            "parking_time",
            "exit_time",
            "status",
        ]

    def get_status(self, obj):
        return obj.get_event_type_display()

    def get_parking_time(self, obj):
        if obj.status != "Parking":
            return None
        # datetime → ISO 문자열로 변환
        return obj.parking_time.isoformat()

    def get_exit_time(self, obj):
        if obj.status != "Exit":
            return None
        return obj.exit_time.isoformat()
