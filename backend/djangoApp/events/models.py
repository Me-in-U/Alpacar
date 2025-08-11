# events\models.py

from django.db import models

from vehicles.models import Vehicle


class VehicleEvent(models.Model):
    """
    차량 입출차 및 예외 이벤트를 저장하는 모델
    - vehicle: 이벤트가 발생한 차량(FK)
    - event_type: 입차, 출차, 예외 중 하나
    - timestamp: 이벤트 발생 시각
    """

    STATUS_CHOICES = [
        ("Entrance", "입차"),
        ("Parking", "주차완료"),
        ("Exit", "출차"),
        ("Exception", "예외"),
    ]

    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.CASCADE, db_column="vehicle_id"
    )
    entrance_time = models.DateTimeField(null=True, blank=True)
    parking_time = models.DateTimeField(null=True, blank=True)
    exit_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Entrance")

    class Meta:
        db_table = "vehicle_event"

    def __str__(self):
        # status의 display 사용
        ts = self.entrance_time or self.parking_time or self.exit_time
        return f"{self.vehicle.license_plate} — {self.get_status_display()} @ {ts}"
