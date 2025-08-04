# vehicles\urls.py
from django.urls import path

from vehicles.views.vehicles import (
    VehicleDetailAPIView,
    VehicleListCreateAPIView,
    VehicleModelListAPIView,
    check_license,
)

urlpatterns = [
    # 차량 모델 전체 목록 조회
    path(
        "vehicle-models/",
        VehicleModelListAPIView.as_view(),  # GET: 전체 차량 모델 리스트 반환
        name="vehicle-model-list",
    ),
    # 내 차량 목록 조회 및 새 차량 등록
    path(
        "vehicles/",
        VehicleListCreateAPIView.as_view(),  # GET: 내 차량 리스트, POST: 차량 생성
        name="vehicle-list-create",
    ),
    # 단일 차량 조회/수정/삭제
    path(
        "vehicles/<int:pk>/",
        VehicleDetailAPIView.as_view(),  # GET/PUT/PATCH/DELETE: 차량 상세 관리
        name="vehicle-detail",
    ),
    # 차량 번호판 중복 확인 endpoint
    path(
        "vehicles/check-license/",
        check_license,  # GET: ?license_plate=… → 중복 여부 반환
        name="vehicle-check-license",
    ),
]
