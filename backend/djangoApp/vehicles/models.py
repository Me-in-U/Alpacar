from django.db import models
from accounts.models import User


class VehicleModel(models.Model):
    SIZE_CLASS_CHOICES = [
        ("compact", "Compact"),
        ("midsize", "Midsize"),
        ("suv", "SUV"),
    ]

    brand = models.CharField("제조사", max_length=255)
    model_name = models.CharField("모델명", max_length=255)
    size_class = models.CharField(
        "차량 크기 분류", max_length=10, choices=SIZE_CLASS_CHOICES
    )
    image_url = models.URLField("대표 이미지 URL")

    created_at = models.DateTimeField("생성일시", auto_now_add=True)
    updated_at = models.DateTimeField("수정일시", auto_now=True)

    class Meta:
        db_table = "vehicle_model"
        verbose_name = "차량 모델"
        verbose_name_plural = "차량 모델"

    def __str__(self):
        return f"{self.brand} {self.model_name}"


class Vehicle(models.Model):
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
        return self.license_plate
