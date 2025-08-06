from django.db import models


class VehicleModel(models.Model):
    """
    차량 모델 정보 모델
    - 브랜드, 모델명, 크기 분류, 이미지 URL
    """

    SIZE_CLASS_CHOICES = [
        ("compact", "Compact"),  # 소형 차량
        ("midsize", "Midsize"),  # 중형 차량
        ("suv", "SUV"),  # SUV 차량
    ]

    brand = models.CharField("제조사", max_length=255)  # 제조사 이름
    model_name = models.CharField("모델명", max_length=255)  # 모델명
    size_class = models.CharField(
        "차량 크기 분류", max_length=10, choices=SIZE_CLASS_CHOICES
    )  # 허용 차량 크기 카테고리
    image_url = models.URLField("대표 이미지 URL")  # 차량 대표 이미지 URL

    created_at = models.DateTimeField("생성일시", auto_now_add=True)
    updated_at = models.DateTimeField("수정일시", auto_now=True)

    class Meta:
        db_table = "vehicle_model"  # 테이블명 지정
        verbose_name = "차량 모델"
        verbose_name_plural = "차량 모델"

    def __str__(self):
        return f"{self.brand} {self.model_name}"


class Vehicle(models.Model):
    """
    사용자의 차량 정보 모델
    - 고유 번호판, 소유자(FK), 모델(FK)
    """

    license_plate = models.CharField("차량 번호판", max_length=20, unique=True)
    user = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="vehicles"
    )
    model = models.ForeignKey(
        VehicleModel, on_delete=models.PROTECT, related_name="vehicles"
    )

    created_at = models.DateTimeField("등록일시", auto_now_add=True)
    updated_at = models.DateTimeField("수정일시", auto_now=True)

    class Meta:
        db_table = "vehicle"
        verbose_name = "차량"
        verbose_name_plural = "차량"

    def __str__(self):
        # 번호판을 문자열로 표현
        return self.license_plate


class VehicleLicensePlateModelMapping(models.Model):
    """
    차량 번호판 ↔ VehicleModel 매핑 테이블
    """

    license_plate = models.CharField(
        "차량 번호판",
        max_length=255,
        unique=True,
    )
    model = models.ForeignKey(
        VehicleModel,
        verbose_name="모델",
        on_delete=models.CASCADE,
        db_column="model_id",
        related_name="plate_mappings",
    )

    class Meta:
        db_table = "vehicle_license_plate_model_mapping"
        verbose_name = "번호판-모델 매핑"
        verbose_name_plural = "번호판-모델 매핑"

    def __str__(self):
        return f"{self.license_plate} → {self.model_id}"
