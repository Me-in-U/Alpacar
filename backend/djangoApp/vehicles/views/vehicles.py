from rest_framework import generics, permissions, status
from rest_framework.response import Response
from vehicles.models import Vehicle, VehicleModel
from vehicles.serializers.vehicles import (
    VehicleCreateSerializer,
    VehicleModelSerializer,
    VehicleSerializer,
)


class VehicleModelListAPIView(generics.ListAPIView):
    queryset = VehicleModel.objects.all().order_by("brand", "model_name")
    serializer_class = VehicleModelSerializer
    permission_classes = [permissions.IsAuthenticated]


class VehicleCreateAPIView(generics.CreateAPIView):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleCreateSerializer
    permission_classes = [permissions.IsAuthenticated]


class VehicleListAPIView(generics.ListAPIView):
    serializer_class = VehicleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Vehicle.objects.filter(user=self.request.user)


class VehicleDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/vehicles/{pk}/   → 단일 차량 조회
    PUT    /api/vehicles/{pk}/   → 전체 업데이트
    PATCH  /api/vehicles/{pk}/   → 부분 업데이트
    DELETE /api/vehicles/{pk}/   → 차량 삭제
    """

    serializer_class = VehicleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # 본인 소유 차량만
        return Vehicle.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        # 수정(create) 시에는 model, license_plate 필드만 받기 위해 CreateSerializer 사용
        if self.request.method in ["PUT", "PATCH"]:
            return VehicleCreateSerializer
        return VehicleSerializer

    def perform_update(self, serializer):
        # partial 업데이트 지원
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        # DeleteAPIView의 destroy를 호출
        return super().destroy(request, *args, **kwargs)
