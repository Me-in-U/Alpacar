# parking/serializers.py

from rest_framework import serializers
from vehicles.models import Vehicle

from .models import ParkingAssignment, ParkingAssignmentHistory, ParkingSpace


# 수동 배정 요청 시리얼라이저
class AssignRequestSerializer(serializers.Serializer):
    license_plate = serializers.CharField()
    zone = serializers.CharField()
    slot_number = serializers.IntegerField()


class ParkingSpaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParkingSpace
        fields = ["id", "zone", "slot_number", "size_class", "status"]


class VehicleSimpleSerializer(serializers.ModelSerializer):
    """차량 간단 정보 시리얼라이저 (FK 모델 이름/브랜드 안전 접근)"""

    brand = serializers.SerializerMethodField()
    model_name = serializers.SerializerMethodField()

    class Meta:
        model = Vehicle
        fields = ["id", "license_plate", "brand", "model_name"]

    def get_brand(self, obj):
        # Vehicle.model.brand 가 없으면 None 반환
        return getattr(getattr(obj, "model", None), "brand", None)

    def get_model_name(self, obj):
        # Vehicle.model.model_name 가 없으면 None 반환
        return getattr(getattr(obj, "model", None), "model_name", None)


class ParkingAssignmentSerializer(serializers.ModelSerializer):
    space_display = serializers.SerializerMethodField()
    vehicle = VehicleSimpleSerializer(read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    space = serializers.PrimaryKeyRelatedField(read_only=True)

    def get_space_display(self, obj):
        """주차 공간 정보 반환 (상태 없이)"""
        if obj.space:
            return f"{obj.space.zone}-{obj.space.slot_number}"
        return "N/A"

    class Meta:
        model = ParkingAssignment
        fields = [
            "id",
            "user",
            "vehicle",
            "space",
            "space_display",
            "start_time",
            "end_time",
            "status",
            "created_at",
        ]


class ParkingHistorySerializer(serializers.ModelSerializer):
    """주차 이력 시리얼라이저 - 프론트엔드 형식에 맞춤"""

    date = serializers.SerializerMethodField()
    time = serializers.SerializerMethodField()
    space = serializers.SerializerMethodField()
    score = serializers.SerializerMethodField()

    class Meta:
        model = ParkingAssignment
        fields = ["id", "date", "time", "space", "score"]

    def get_date(self, obj):
        """YYYY-MM-DD 형식으로 날짜 반환"""
        return obj.start_time.strftime("%Y-%m-%d")

    def get_time(self, obj):
        """HH:MM 형식으로 시간 반환"""
        return obj.start_time.strftime("%H:%M")

    def get_space(self, obj):
        """주차 공간 정보 반환"""
        if obj.space:
            return f"{obj.space.zone}-{obj.space.slot_number}"
        return "N/A"

    def get_score(self, obj):
        """해당 배정의 점수 반환"""
        try:
            # ParkingAssignmentHistory에서 해당 assignment의 점수를 가져오기
            history = ParkingAssignmentHistory.objects.filter(assignment=obj).first()
            if history:
                return history.score
            else:
                # 점수 히스토리가 없는 경우 null 또는 기본값 반환
                return None
        except Exception:
            # 에러 발생시 null 반환
            return None


class ParkingScoreHistorySerializer(serializers.ModelSerializer):
    """주차 점수 히스토리 시리얼라이저"""

    date = serializers.SerializerMethodField()

    class Meta:
        model = ParkingAssignmentHistory
        fields = ["id", "score", "date", "created_at"]

    def get_date(self, obj):
        """MM-DD 형식으로 날짜 반환"""
        return obj.created_at.strftime("%m-%d")
