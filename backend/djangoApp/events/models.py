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

    EVENT_TYPE_CHOICES = [
        ("Entrance", "입차"),  # 입차 이벤트
        ("Exit", "출차"),  # 출차 이벤트
        ("Exception", "예외"),  # 기타 예외 이벤트
    ]
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        db_column="vehicle_id",
        related_name="events",
        verbose_name="차량",
    )  # 이벤트 대상 차량
    event_type = models.CharField(
        max_length=20,
        choices=EVENT_TYPE_CHOICES,
        verbose_name="이벤트 종류",
    )  # 이벤트 타입
    timestamp = models.DateTimeField(verbose_name="발생 시각")  # 이벤트 발생 시각 저장

    class Meta:
        db_table = "vehicle_event"  # 테이블명 지정
        verbose_name = "차량 이벤트"
        verbose_name_plural = "차량 이벤트"

    def __str__(self):
        # 문자열 표현: "번호판 — 이벤트종류 @ 시각"
        return f"{self.vehicle.license_plate} — {self.get_event_type_display()} @ {self.timestamp}"
