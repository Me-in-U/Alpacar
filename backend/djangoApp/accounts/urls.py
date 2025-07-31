# accounts/urls.py
"""
URL 라우팅 설정
- 계정 관련 모든 API 엔드포인트 연결
"""

from django.urls import path

from accounts.views.auth import (
    LoginAPI,
    RefreshAPI,
    SignupAPI,
    check_email,
    check_nickname,
)
from accounts.views.google import google_callback, google_login
from accounts.views.password_reset import (
    PasswordResetConfirmAPIView,
    PasswordResetRequestAPIView,
    PasswordResetVerifyAPIView,
)
from accounts.views.profile import UserProfileAPI
from accounts.views.push import push_setting, subscribe_push, unsubscribe_push

urlpatterns = [
    # ─ 회원가입 / 로그인 / 토큰갱신 ──────────────────────────────────────────
    path(
        "api/auth/signup/",
        SignupAPI.as_view(),
        name="api-signup",
    ),  # POST: 회원가입
    path(
        "api/auth/login/",
        LoginAPI.as_view(),
        name="api-login",
    ),  # POST: 이메일/비밀번호로 JWT 발급
    path(
        "api/auth/token/refresh/",
        RefreshAPI.as_view(),
        name="api-token-refresh",
    ),  # POST: refresh 토큰으로 access 재발급
    # ─ 이메일/닉네임 중복 확인 ───────────────────────────────────────────────
    path(
        "api/auth/check-email/",
        check_email,
        name="api-check-email",
    ),  # GET: ?email=… → { exists: bool }
    path(
        "api/auth/check-nickname/",
        check_nickname,
        name="api-check-nickname",
    ),  # GET: ?nickname=… → { exists: bool }
    # ─ 비밀번호 재설정 ─────────────────────────────────────────────────────
    path(
        "api/auth/password-reset/request/",
        PasswordResetRequestAPIView.as_view(),
        name="password-reset-request",
    ),  # POST: 이름+이메일 검증 후 인증번호 발송
    path(
        "api/auth/password-reset/verify/",
        PasswordResetVerifyAPIView.as_view(),
        name="password-reset-verify",
    ),  # POST: {email, code} 인증번호만 검증
    path(
        "api/auth/password-reset/confirm/",
        PasswordResetConfirmAPIView.as_view(),
        name="password-reset-confirm",
    ),  # POST: {email, code, new_password, new_password2} 비밀번호 변경
    # ─ 내 프로필 조회·수정 ─────────────────────────────────────────────────
    path(
        "api/users/me/",
        UserProfileAPI.as_view(),
        name="user-me",
    ),  # GET/PUT: 내 프로필 및 VAPID 키 조회·수정
    # ─ 푸시 알림 설정 ──────────────────────────────────────────────────────
    path(
        "api/push/setting/",
        push_setting,
        name="api-push-setting",
    ),  # GET/POST: 푸시 수신 여부 조회·변경
    # ─ 푸시 구독 관리 ──────────────────────────────────────────────────────
    path(
        "api/push/subscribe/",
        subscribe_push,
        name="api-push-subscribe",
    ),  # POST: 구독 정보 등록/업데이트
    path(
        "api/push/unsubscribe/",
        unsubscribe_push,
        name="api-push-unsubscribe",
    ),  # POST: 구독 해제
    # ── 소셜 로그인 (Google) ──────────────────────────────────────────────
    path(
        "api/auth/social/google/login/",
        google_login,
        name="google_login",
    ),  # GET: Google OAuth 동의 화면으로 리다이렉트
    path(
        "api/auth/social/google/callback/",
        google_callback,
        name="google_callback",
    ),  # GET: Google 콜백 처리
]
