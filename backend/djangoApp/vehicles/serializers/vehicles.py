from rest_framework import serializers
from vehicles.models import Vehicle, VehicleModel


class VehicleModelSerializer(serializers.ModelSerializer):
    """
    차량 모델 정보 직렬화
    - id, 브랜드, 모델명, 이미지 URL 필드 포함
    """

    class Meta:
        model = VehicleModel
        fields = ["id", "brand", "model_name", "image_url"]  # 노출할 필드


class VehicleSerializer(serializers.ModelSerializer):
    """
    내 차량 조회용 직렬화
    - license_plate와 중첩된 모델 정보 포함
    """

    model = VehicleModelSerializer(read_only=True)  # 읽기 전용 중첩 모델 정보

    class Meta:
        model = Vehicle
        fields = ["id", "license_plate", "model"]


class VehicleCreateSerializer(serializers.ModelSerializer):
    """
    차량 생성 및 수정용 직렬화
    - request.user를 자동으로 연관하여 생성
    """

    class Meta:
        model = Vehicle
        fields = ["id", "model", "license_plate"]

    def validate_license_plate(self, value):
        """
        번호판 중복 검증
        """
        # 이미 등록된 번호판인지 확인
        if Vehicle.objects.filter(license_plate=value).exists():
            raise serializers.ValidationError("이미 등록된 번호판입니다.")
        return value

    def create(self, validated_data):
        """
        사용자 자동 연결 후 Vehicle 객체 생성
        """
        user = self.context["request"].user
        return Vehicle.objects.create(user=user, **validated_data)

    def update(self, instance, validated_data):
        """
        수정 시 user 필드는 변경하지 않고
        model과 license_plate만 업데이트
        """
        # PUT/PATCH 시에도 user 건드리지 않고 model/license_plate만 업데이트
        return super().update(instance, validated_data)
