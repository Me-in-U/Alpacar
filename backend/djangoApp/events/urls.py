from django.urls import path
from .views import (
    list_vehicle_events,
    manual_entrance,
    manual_parking_complete,
    manual_exit,
)

urlpatterns = [
    path("vehicle-events/", list_vehicle_events, name="list_events"),
    path(
        "vehicles/<int:vehicle_id>/manual-parking/",
        manual_parking_complete,
        name="manual_parking",
    ),
    path("vehicles/<int:vehicle_id>/manual-exit/", manual_exit, name="manual_exit"),
    path("vehicles/manual-entrance/", manual_entrance, name="manual-entrance"),
]
