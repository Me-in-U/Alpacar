from django.db import models
from django.utils import timezone


class ParkingSpace(models.Model):
    SIZE_CLASS_CHOICES = [
        ("compact", "Compact"),
        ("midsize", "Midsize"),
        ("suv", "SUV"),
    ]

    zone = models.CharField("구역", max_length=10)
    slot_number = models.PositiveIntegerField("슬롯 번호")
    size_class = models.CharField(
        "허용 크기", max_length=10, choices=SIZE_CLASS_CHOICES
    )
    is_occupied = models.BooleanField("점유 여부", default=False)

    created_at = models.DateTimeField("생성일시", auto_now_add=True)
    updated_at = models.DateTimeField("수정일시", auto_now=True)

    class Meta:
        db_table = "parking_space"
        verbose_name = "주차 공간"
        verbose_name_plural = "주차 공간"
        unique_together = (("zone", "slot_number"),)

    def __str__(self):
        return f"{self.zone}-{self.slot_number}"


class ParkingAssignment(models.Model):
    STATUS_CHOICES = [
        ("ASSIGNED", "배정됨"),
        ("COMPLETED", "완료됨"),
    ]

    user = models.ForeignKey(
        "accounts.User", on_delete=models.PROTECT, related_name="assignments"
    )
    vehicle = models.ForeignKey(
        "vehicles.Vehicle", on_delete=models.PROTECT, related_name="assignments"
    )
    space = models.ForeignKey(
        ParkingSpace, on_delete=models.PROTECT, related_name="assignments"
    )
    start_time = models.DateTimeField("입차 시각", default=timezone.now)
    end_time = models.DateTimeField("출차 시각", null=True, blank=True)
    status = models.CharField(
        "상태", max_length=10, choices=STATUS_CHOICES, default="ASSIGNED"
    )

    created_at = models.DateTimeField("생성일시", auto_now_add=True)
    updated_at = models.DateTimeField("수정일시", auto_now=True)

    class Meta:
        db_table = "parking_assignment"
        verbose_name = "주차 배정"
        verbose_name_plural = "주차 배정"

    def __str__(self):
        return f"{self.space} - {self.get_status_display()}"


class ParkingAssignmentHistory(models.Model):
    """
    사용자 점수 변경을 포함한 히스토리 관리.
    """

    user = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="score_histories"
    )
    assignment = models.ForeignKey(
        ParkingAssignment, on_delete=models.SET_NULL, null=True, blank=True
    )
    score = models.IntegerField("점수", help_text="변경된 점수")
    created_at = models.DateTimeField("변경 시각", auto_now_add=True)

    class Meta:
        db_table = "parking_assignment_history"
        verbose_name = "배정 점수 히스토리"
        verbose_name_plural = "배정 점수 히스토리"

    def __str__(self):
        return f"{self.user.nickname} - {self.score}점 @ {self.created_at}"
