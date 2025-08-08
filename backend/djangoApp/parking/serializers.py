# parking/serializers.py
from rest_framework import serializers
from .models import ParkingAssignment, ParkingAssignmentHistory, ParkingSpace
from vehicles.models import Vehicle


class ParkingSpaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParkingSpace
        fields = ["id", "zone", "slot_number", "size_class", "status"]


class VehicleSimpleSerializer(serializers.ModelSerializer):
    """차량 간단 정보 시리얼라이저"""

    class Meta:
        model = Vehicle
        fields = ["id", "license_plate", "make", "model"]


class ParkingAssignmentSerializer(serializers.ModelSerializer):
    """주차 배정 시리얼라이저"""

    space_display = serializers.CharField(source="space", read_only=True)
    vehicle = VehicleSimpleSerializer(read_only=True)

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
        return str(obj.space) if obj.space else "N/A"

    def get_score(self, obj):
        """해당 배정의 점수 반환"""
        try:
            # ParkingAssignmentHistory에서 해당 assignment의 점수를 가져오기
            history = ParkingAssignmentHistory.objects.filter(assignment=obj).first()
            if history:
                return history.score
            else:
                # 임시로 랜덤값 반환
                import random

                return random.randint(60, 95)
        except Exception:
            # 에러 발생시 기본값 반환
            return 75


class ParkingScoreHistorySerializer(serializers.ModelSerializer):
    """주차 점수 히스토리 시리얼라이저"""

    date = serializers.SerializerMethodField()

    class Meta:
        model = ParkingAssignmentHistory
        fields = ["id", "score", "date", "created_at"]

    def get_date(self, obj):
        """MM-DD 형식으로 날짜 반환"""
        return obj.created_at.strftime("%m-%d")
