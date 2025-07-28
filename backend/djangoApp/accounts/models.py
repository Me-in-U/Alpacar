# accounts/models.py
from django.db import models


class Member(models.Model):
    """
    회원 기본 정보 모델
    - 이메일(email)로 로그인
    - plate_number: 차량 번호판 (고유)
    - push_enabled: 푸시 알림 수신 여부
    """

    name = models.CharField(max_length=50)  # 실명
    nickname = models.CharField(max_length=50)  # 별명
    email = models.EmailField(unique=True)  # 로그인 이메일 (고유)
    password_hash = models.CharField(max_length=128)  # SHA-256 해시된 비밀번호
    phone = models.CharField(max_length=20)  # 연락처
    plate_number = models.CharField(max_length=20, unique=True)  # 차량 번호판 (고유)
    push_enabled = models.BooleanField(default=False)  # 푸시 알림 수신 설정

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
