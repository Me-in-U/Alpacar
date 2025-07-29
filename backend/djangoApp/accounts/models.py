# accounts/models.py
from django.db import models

from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager,
)


class MemberManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if not extra_fields.get("name"):
            extra_fields["name"] = "admin"
        return self.create_user(email, password, **extra_fields)


class Member(AbstractBaseUser, PermissionsMixin):
    name = models.CharField(max_length=50)
    nickname = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    plate_number = models.CharField(max_length=20, unique=True)
    push_enabled = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = MemberManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name", "nickname", "phone", "plate_number"]

    def __str__(self):
        return f"{self.nickname} <{self.email}>"


class PushSubscription(models.Model):
    """
    웹 푸시 구독 정보 모델
    - user: Member와 일대다(FK)
    - endpoint, p256dh, auth: Web Push 프로토콜 키
    """

    user = models.ForeignKey(
        Member, on_delete=models.CASCADE, related_name="subscriptions"
    )
    endpoint = models.URLField()  # 푸시 서버 URL
    p256dh = models.CharField(max_length=255)  # 클라이언트 공개 키
    auth = models.CharField(max_length=255)  # 인증 토큰

    def __str__(self):
        return f"Subscription for {self.user.email}"
