# accounts/models.py
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email은 필수 입력 항목입니다.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if not extra_fields.get("full_name"):
            extra_fields["full_name"] = "admin"
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField("이메일", unique=True)
    full_name = models.CharField("실명", max_length=50)
    nickname = models.CharField("닉네임", max_length=50, unique=True)
    phone = models.CharField("전화번호", max_length=20)
    push_enabled = models.BooleanField("푸시 수신 여부", default=False)
    score = models.IntegerField("주차 실력 점수", default=0)
    created_at = models.DateTimeField("생성일시", auto_now_add=True)
    updated_at = models.DateTimeField("수정일시", auto_now=True)

    is_active = models.BooleanField("활성 사용자", default=True)
    is_staff = models.BooleanField("관리자 권한", default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name", "nickname", "phone"]

    class Meta:
        db_table = "accounts_user"
        verbose_name = "사용자"
        verbose_name_plural = "사용자"

    def __str__(self):
        return f"{self.nickname} <{self.email}>"


class PushSubscription(models.Model):
    """
    웹 푸시 구독 정보 모델
    - user: User와 일대다(FK)
    - endpoint, p256dh, auth: Web Push 프로토콜 키
    """

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="subscriptions"
    )
    endpoint = models.URLField("엔드포인트 URL")
    p256dh = models.CharField("P256DH 키", max_length=255)
    auth = models.CharField("Auth 토큰", max_length=255)
    created_at = models.DateTimeField("구독일시", auto_now_add=True)

    class Meta:
        db_table = "accounts_push_subscription"
        verbose_name = "푸시 구독"
        verbose_name_plural = "푸시 구독"

    def __str__(self):
        return f"Subscription for {self.user.email}"
