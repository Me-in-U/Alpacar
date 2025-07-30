from django.db import models

from vehicles.models import Vehicle

# Create your models here.


class VehicleEvent(models.Model):
    EVENT_TYPE_CHOICES = [
        ("Entrance", "입차"),
        ("Exit", "출차"),
        ("Exception", "예외"),
    ]
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        db_column="vehicle_id",
        related_name="events",
        verbose_name="차량",
    )
    event_type = models.CharField(
        max_length=20, choices=EVENT_TYPE_CHOICES, verbose_name="이벤트 종류"
    )
    timestamp = models.DateTimeField(verbose_name="발생 시각")

    class Meta:
        db_table = "vehicle_event"
        verbose_name = "차량 이벤트"
        verbose_name_plural = "차량 이벤트"

    def __str__(self):
        return f"{self.vehicle.license_plate} — {self.get_event_type_display()} @ {self.timestamp}"
