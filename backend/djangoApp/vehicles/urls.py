from django.urls import path

from vehicles.views.vehicles import (
    VehicleCreateAPIView,
    VehicleDetailAPIView,
    VehicleListAPIView,
    VehicleModelListAPIView,
)

urlpatterns = [
    # 차량 모델 조회
    path(
        "api/vehicle-models/",
        VehicleModelListAPIView.as_view(),
        name="vehicle-model-list",
    ),
    # 내 차량 목록 및 생성
    path("api/vehicles/", VehicleListAPIView.as_view(), name="vehicle-list"),
    path("api/vehicles/", VehicleCreateAPIView.as_view(), name="vehicle-create"),
    # 단일 차량 조회/수정/삭제
    path(
        "api/vehicles/<int:pk>/", VehicleDetailAPIView.as_view(), name="vehicle-detail"
    ),
]
