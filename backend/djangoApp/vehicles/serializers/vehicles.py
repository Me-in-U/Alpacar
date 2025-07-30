from rest_framework import serializers
from vehicles.models import Vehicle, VehicleModel


class VehicleModelSerializer(serializers.ModelSerializer):
    """차량 모델(제조사·모델명·이미지) 직렬화"""

    class Meta:
        model = VehicleModel
        fields = ["id", "brand", "model_name", "image_url"]


class VehicleSerializer(serializers.ModelSerializer):
    """내 차량 목록/조회용 직렬화 (license_plate + 중첩된 모델 정보)"""

    model = VehicleModelSerializer(read_only=True)

    class Meta:
        model = Vehicle
        fields = ["id", "license_plate", "model"]


class VehicleCreateSerializer(serializers.ModelSerializer):
    """차량 생성·수정용 직렬화 (user 자동 연결)"""

    class Meta:
        model = Vehicle
        fields = ["id", "model", "license_plate"]

    def validate_license_plate(self, value):
        # 이미 등록된 번호판인지 확인
        if Vehicle.objects.filter(license_plate=value).exists():
            raise serializers.ValidationError("이미 등록된 번호판입니다.")
        return value

    def create(self, validated_data):
        user = self.context["request"].user
        return Vehicle.objects.create(user=user, **validated_data)

    def update(self, instance, validated_data):
        # PUT/PATCH 시에도 user 건드리지 않고 model/license_plate만 업데이트
        return super().update(instance, validated_data)
