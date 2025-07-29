from django.urls import path
from vehicles.views import vehicle_models_view, vehicle_models_api

urlpatterns = [
    # 차량 모델 관련
    path("vehicle-models/", vehicle_models_view, name="vehicle-models"),
    path("api/vehicle-models/", vehicle_models_api, name="api-vehicle-models"),
] 