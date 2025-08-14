# parking\models.py
from django.db import models
from django.utils import timezone

from events.models import VehicleEvent
from vehicles.models import Vehicle


class ParkingSpace(models.Model):
    """
    주차 공간 모델
    - zone과 slot_number를 기준으로 유일한 공간
    - 크기 분류(size_class)에 따라 허용 차량 크기 구분
    - is_occupied로 점유 여부 관리
    """

    SIZE_CLASS_CHOICES = [
        ("compact", "Compact"),  # 소형
        ("midsize", "Midsize"),  # 중형
        ("suv", "SUV"),  # 대형(SUV)
    ]

    STATUS_CHOICES = [
        ("free", "비어있음"),
        ("occupied", "사용중"),
        ("reserved", "예약됨"),
    ]

    zone = models.CharField("구역", max_length=10)  # 주차 구역 이름
    slot_number = models.PositiveIntegerField("슬롯 번호")  # 구역 내 고유 슬롯 번호
    size_class = models.CharField(
        "허용 크기",
        max_length=10,
        choices=SIZE_CLASS_CHOICES,
    )  # 허용 차량 크기
    status = models.CharField(
        "상태",
        max_length=10,
        choices=STATUS_CHOICES,
        default="free",
    )
    #  현재 이 공간을 점유/예약 중인 차량(없으면 null)
    current_vehicle = models.ForeignKey(
        Vehicle,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="current_space",
    )
    created_at = models.DateTimeField("생성일시", auto_now_add=True)  # 등록 시각
    updated_at = models.DateTimeField("수정일시", auto_now=True)  # 수정 시각

    class Meta:
        db_table = "parking_space"  # 테이블명 지정
        verbose_name = "주차 공간"
        verbose_name_plural = "주차 공간"
        unique_together = (("zone", "slot_number"),)  # 구역+번호 조합 유일

    def __str__(self):
        return f"{self.zone}-{self.slot_number}"


class ParkingAssignment(models.Model):
    """
    주차 배정 모델
    - user와 vehicle, space FK로 연결
    - start_time, end_time으로 입차·출차 시각 기록
    - status로 현황 표시(배정됨/완료됨)
    """

    entrance_event = models.OneToOneField(  # << 입차 기록당 1개 배정
        VehicleEvent,
        on_delete=models.PROTECT,
        related_name="assignment",
        null=True,
        blank=True,  # 기존 데이터 고려
    )
    STATUS_CHOICES = [
        ("ASSIGNED", "배정됨"),  # 입차 완료, 주차 중
        ("COMPLETED", "완료됨"),  # 출차 완료
    ]

    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="assignments",
    )  # 배정 받는 사용자
    vehicle = models.ForeignKey(
        "vehicles.Vehicle",
        on_delete=models.PROTECT,
        related_name="assignments",
    )  # 배정된 차량
    space = models.ForeignKey(
        ParkingSpace,
        on_delete=models.PROTECT,
        related_name="assignments",
    )  # 배정된 주차 공간
    start_time = models.DateTimeField(
        "입차 시각", default=timezone.now
    )  # 입차 시각 기본 현재 시각
    end_time = models.DateTimeField(
        "출차 시각", null=True, blank=True
    )  # 출차 시각(미출차 시 null)
    status = models.CharField(
        "상태",
        max_length=10,
        choices=STATUS_CHOICES,
        default="ASSIGNED",
    )  # 배정 상태

    created_at = models.DateTimeField("생성일시", auto_now_add=True)  # 등록 시각
    updated_at = models.DateTimeField("수정일시", auto_now=True)  # 수정 시각

    class Meta:
        db_table = "parking_assignment"  # 테이블명 지정
        verbose_name = "주차 배정"
        verbose_name_plural = "주차 배정"

    def __str__(self):
        return f"{self.space} - {self.get_status_display()}"  # 대표 문자열


class ParkingAssignmentHistory(models.Model):
    """
    주차 배정 이력 모델
    - score 히스토리 기록
    - assignment FK로 배정 참조(삭제 시 null)
    """

    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="score_histories",
    )  # 점수를 받는 사용자
    assignment = models.ForeignKey(
        ParkingAssignment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )  # 관련 배정 (삭제 시 null)
    score = models.IntegerField("점수", help_text="변경된 점수")  # 변경된 점수
    created_at = models.DateTimeField("변경 시각", auto_now_add=True)  # 이력 기록 시각

    class Meta:
        db_table = "parking_assignment_history"  # 테이블명 지정
        verbose_name = "배정 점수 히스토리"
        verbose_name_plural = "배정 점수 히스토리"

    def __str__(self):
        return (
            f"{self.user.nickname} - {self.score}점 @ {self.created_at}"  # 대표 문자열
        )
