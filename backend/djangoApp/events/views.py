# events\views.py

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from .models import VehicleEvent
from .serializers import VehicleEventSerializer


@api_view(["POST"])
@permission_classes([IsAdminUser])
def manual_parking_complete(request, vehicle_id):
    event = VehicleEvent.objects.create(
        vehicle_id=vehicle_id,
        event_type="Parking",
        timestamp=timezone.now(),
    )
    data = VehicleEventSerializer(event).data
    return Response(data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAdminUser])
def manual_exit(request, vehicle_id):
    event = VehicleEvent.objects.create(
        vehicle_id=vehicle_id,
        event_type="Exit",
        timestamp=timezone.now(),
    )
    data = VehicleEventSerializer(event).data
    return Response(data, status=status.HTTP_201_CREATED)
