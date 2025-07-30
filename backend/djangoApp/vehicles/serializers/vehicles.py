from rest_framework import serializers
from vehicles.models import Vehicle, VehicleModel


class VehicleModelSerializer(serializers.ModelSerializer):
    """차량 모델(제조사·모델명·이미지) 직렬화"""

    class Meta:
        model = VehicleModel
        fields = ["id", "brand", "model_name", "image_url"]


class VehicleSerializer(serializers.ModelSerializer):
    """차량(license_plate) + 연결된 모델 정보 직렬화"""

    model = VehicleModelSerializer(read_only=True)

    class Meta:
        model = Vehicle
        fields = [
            "id",
            "license_plate",
            "model",  # 이 안에 brand/model_name/image_url 포함
        ]


class VehicleCreateSerializer(serializers.ModelSerializer):
    """차량 생성 (user는 context['request'].user 로 설정)"""

    class Meta:
        model = Vehicle
        fields = ["id", "model", "license_plate"]

    def create(self, validated_data):
        user = self.context["request"].user
        return Vehicle.objects.create(user=user, **validated_data)
