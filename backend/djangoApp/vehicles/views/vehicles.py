from rest_framework import generics, permissions
from vehicles.models import Vehicle, VehicleModel
from vehicles.serializers.vehicles import (
    VehicleCreateSerializer,
    VehicleModelSerializer,
    VehicleSerializer,
)
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated


class VehicleModelListAPIView(generics.ListAPIView):
    """
    GET  /api/vehicle-models/
      → 제조사·모델명·이미지 목록 조회
    """

    queryset = VehicleModel.objects.all().order_by("brand", "model_name")
    serializer_class = VehicleModelSerializer
    permission_classes = [permissions.IsAuthenticated]


class VehicleListCreateAPIView(generics.ListCreateAPIView):
    """
    GET  /api/vehicles/   → 내 차량 목록 조회
    POST /api/vehicles/   → 차량 생성
    """

    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Vehicle.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return VehicleCreateSerializer
        return VehicleSerializer

    def perform_create(self, serializer):
        serializer.save()


class VehicleDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/vehicles/{pk}/   → 단일 차량 조회
    PUT    /api/vehicles/{pk}/   → 전체 수정 (model, license_plate)
    PATCH  /api/vehicles/{pk}/   → 부분 수정
    DELETE /api/vehicles/{pk}/   → 차량 삭제
    """

    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Swagger가 스키마 생성용으로 호출할 때는 빈 쿼리셋 반환
        if getattr(self, "swagger_fake_view", False):
            return Vehicle.objects.none()
        return Vehicle.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return VehicleCreateSerializer
        return VehicleSerializer


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def check_license(request):
    """
    GET /api/vehicles/check-license/?license=12가3456
    → { "exists": true } or { "exists": false }
    """
    license_plate = request.query_params.get("license")
    if not license_plate:
        return Response(
            {"detail": "license 파라미터가 필요합니다."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    exists = Vehicle.objects.filter(license_plate=license_plate).exists()
    return Response({"exists": exists})
