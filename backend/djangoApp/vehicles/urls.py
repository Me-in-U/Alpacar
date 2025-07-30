from django.urls import path

from vehicles.views.vehicles import (
    VehicleDetailAPIView,
    VehicleListCreateAPIView,
    VehicleModelListAPIView,
    check_license,
)

urlpatterns = [
    # 차량 모델 전체 목록
    path(
        "api/vehicle-models/",
        VehicleModelListAPIView.as_view(),
        name="vehicle-model-list",
    ),
    # 내 차량 목록 조회 & 차량 생성
    path(
        "api/vehicles/",
        VehicleListCreateAPIView.as_view(),
        name="vehicle-list-create",
    ),
    # 단일 차량 조회/수정/삭제
    path(
        "api/vehicles/<int:pk>/",
        VehicleDetailAPIView.as_view(),
        name="vehicle-detail",
    ),
    # 차량 번호판 중복 확인
    path("api/vehicles/check-license/", check_license, name="vehicle-check-license"),
]
