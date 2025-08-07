# events/serializers.py
from rest_framework import serializers
from .models import VehicleEvent


class VehicleEventSerializer(serializers.ModelSerializer):
    vehicle_id = serializers.IntegerField(source="vehicle.id", read_only=True)  # 추가
    license_plate = serializers.CharField(
        source="vehicle.license_plate", read_only=True
    )
    location = serializers.CharField(source="vehicle.model.model_name", read_only=True)
    status = serializers.SerializerMethodField()
    entrance_time = serializers.DateTimeField(source="timestamp", read_only=True)
    parking_time = serializers.SerializerMethodField()
    exit_time = serializers.SerializerMethodField()

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

    def get_parking_time(self, obj):
        if obj.event_type != "Parking":
            return None
        return obj.timestamp

    def get_exit_time(self, obj):
        if obj.event_type != "Exit":
            return None
        return obj.timestamp
