# accounts/models.py
from datetime import timedelta

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    """
    커스텀 UserManager
    - create_user: 이메일 필수, normalize_email 후 비밀번호 설정 및 저장
    - create_superuser: is_staff, is_superuser 플래그 설정 후 생성
    """

    def create_user(self, email, password=None, **extra_fields):
        """
        일반 사용자 생성
        """
        if not email:
            raise ValueError("Email은 필수 입력 항목입니다.")  # 이메일 필수 검증
        email = self.normalize_email(email)  # 도메인 부분 소문자 변환
        user = self.model(email=email, **extra_fields)  # User 인스턴스 생성
        user.set_password(password)  # 비밀번호 해시 설정
        user.save(using=self._db)  # DB에 저장
        return user  # 생성된 User 반환

    def create_superuser(self, email, password=None, **extra_fields):
        """
        슈퍼유저 생성
        """
        extra_fields.setdefault("is_staff", True)  # 관리자 권한 부여
        extra_fields.setdefault("is_superuser", True)  # 슈퍼유저 권한 부여
        if not extra_fields.get("full_name"):
            extra_fields["full_name"] = "admin"  # 실명이 없으면 'admin'으로 설정
        return self.create_user(email, password, **extra_fields)  # User 생성 호출


class User(AbstractBaseUser, PermissionsMixin):
    """
    커스텀 User 모델
    - email을 USERNAME_FIELD로 사용
    - full_name, nickname, phone 등의 추가 필드 지원
    """

    email = models.EmailField("이메일", unique=True)  # 로그인용 이메일
    full_name = models.CharField("실명", max_length=50)  # 사용자 실명
    nickname = models.CharField("닉네임", max_length=50, unique=True)  # 고유 닉네임
    phone = models.CharField("전화번호", max_length=20)  # 연락처
    push_enabled = models.BooleanField(
        "푸시 수신 여부", default=False
    )  # 푸시 알림 허용 여부
    score = models.IntegerField("주차 실력 점수", default=0)  # 사용자 점수
    created_at = models.DateTimeField("생성일시", auto_now_add=True)  # 생성 타임스탬프
    updated_at = models.DateTimeField("수정일시", auto_now=True)  # 수정 타임스탬프

    is_active = models.BooleanField("활성 사용자", default=True)  # 계정 활성화 여부
    is_staff = models.BooleanField(
        "관리자 권한", default=False
    )  # 관리자 사이트 접근 권한

    objects = UserManager()  # 커스텀 매니저 지정

    USERNAME_FIELD = "email"  # 이메일을 기본 로그인 필드로 사용
    REQUIRED_FIELDS = [
        "full_name",
        "nickname",
        "phone",
    ]  # superuser 생성 시 추가 입력 필드

    class Meta:
        db_table = "accounts_user"  # 테이블명 지정
        verbose_name = "사용자"
        verbose_name_plural = "사용자"

    def __str__(self):
        return f"{self.nickname} <{self.email}>"  # 객체 표현 시 닉네임과 이메일 출력


class PushSubscription(models.Model):
    """
    웹 푸시 구독 정보 모델
    - user: 구독자(User)와 일대다 관계
    - endpoint, p256dh, auth: Web Push 프로토콜 키 정보
    """

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="subscriptions"
    )  # 사용자 외래키
    endpoint = models.URLField("엔드포인트 URL")  # 푸시 서비스 URL
    p256dh = models.CharField("P256DH 키", max_length=255)  # 공개 키
    auth = models.CharField("Auth 토큰", max_length=255)  # 인증 토큰
    created_at = models.DateTimeField("구독일시", auto_now_add=True)  # 구독 등록 시각

    class Meta:
        db_table = "accounts_push_subscription"  # 테이블명 지정
        verbose_name = "푸시 구독"
        verbose_name_plural = "푸시 구독"

    def __str__(self):
        return f"Subscription for {self.user.email}"  # 표현 시 사용자 이메일 포함


class Notification(models.Model):
    """
    사용자 알림 모델
    - user: 알림을 받을 사용자(FK)
    - title: 알림 제목
    - message: 알림 내용
    - notification_type: 알림 종류 (주차완료, 등급승급, 시스템 등)
    - data: 추가 데이터 (JSON 형태)
    - is_read: 읽음 상태
    - created_at: 생성 시각
    """

    NOTIFICATION_TYPES = [
        ("vehicle_entry", "입차 알림"),
        ("parking_assignment", "주차 배정"),
        ("parking_reassignment", "주차 재배정"),
        ("parking_complete", "주차 완료"),
        ("vehicle_exit", "출차 완료"),
        ("grade_upgrade", "등급 승급"),
        ("system", "시스템"),
        ("maintenance", "점검"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )  # 사용자 외래키
    title = models.CharField("알림 제목", max_length=100)  # 알림 제목
    message = models.TextField("알림 내용")  # 알림 상세 내용
    notification_type = models.CharField(
        "알림 종류", max_length=20, choices=NOTIFICATION_TYPES, default="system"
    )  # 알림 종류
    data = models.JSONField("추가 데이터", default=dict, blank=True)  # 추가 정보 JSON
    is_read = models.BooleanField("읽음 상태", default=False)  # 읽음 여부
    created_at = models.DateTimeField("생성일시", auto_now_add=True)  # 생성 시각

    class Meta:
        db_table = "accounts_notification"  # 테이블명 지정
        verbose_name = "알림"
        verbose_name_plural = "알림"
        ordering = ["-created_at"]  # 최신순 정렬

    def __str__(self):
        return f"{self.user.nickname}: {self.title}"  # 표현 시 사용자와 제목 포함


class VerificationCode(models.Model):
    """
    이메일 기반 인증 코드 모델
    - 이메일, 코드, 생성일시
    - is_expired(): 10분 후 만료 여부 검사
    """

    email = models.EmailField()  # 코드 전송 대상 이메일
    code = models.CharField(max_length=6)  # 6자리 인증 코드
    created_at = models.DateTimeField(auto_now_add=True)  # 생성 시각 저장

    def is_expired(self):
        """
        코드 만료 여부 반환
        """
        return timezone.now() > self.created_at + timedelta(
            minutes=10
        )  # 10분 경과 시 True

    def __str__(self):
        return f"{self.email} → {self.code}"  # 코드 문자열 표현