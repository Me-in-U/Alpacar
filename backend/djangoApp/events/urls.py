from django.urls import path
from .views import manual_parking_complete, manual_exit

urlpatterns = [
    path(
        "vehicles/<int:vehicle_id>/manual-parking/",
        manual_parking_complete,
        name="manual_parking",
    ),
    path("vehicles/<int:vehicle_id>/manual-exit/", manual_exit, name="manual_exit"),
]
