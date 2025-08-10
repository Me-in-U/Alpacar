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
from accounts.views.password_change import PasswordChangeAPI
from accounts.views.password_reset import (
    PasswordResetConfirmAPIView,
    PasswordResetRequestAPIView,
    PasswordResetVerifyAPIView,
)
from accounts.views.profile import UserProfileAPI, set_parking_skill
from accounts.views.push import push_setting, subscribe_push, unsubscribe_push
from accounts.views.email_verify import (
    SignupEmailVerifyRequestAPIView,
    SignupEmailVerifyVerifyAPIView,
)
from accounts.views.notifications import (
    notification_list,
    notification_detail, 
    notification_delete, 
    notification_delete_all, 
    notification_mark_all_read, 
    notification_unread_count,
    test_push_notification,
    test_vehicle_entry_notification,
    test_parking_complete_notification,
    test_grade_upgrade_notification,
    test_all_notifications
)

urlpatterns = [
    # ─ 회원가입 / 로그인 / 토큰갱신 ──────────────────────────────────────────
    path(
        "auth/signup/",
        SignupAPI.as_view(),
        name="api-signup",
    ),  # POST: 회원가입
    path(
        "auth/login/",
        LoginAPI.as_view(),
        name="api-login",
    ),  # POST: 이메일/비밀번호로 JWT 발급
    path(
        "auth/token/refresh/",
        RefreshAPI.as_view(),
        name="api-token-refresh",
    ),  # POST: refresh 토큰으로 access 재발급
    # ─ 이메일/닉네임 중복 확인 ───────────────────────────────────────────────
    path(
        "auth/check-email/",
        check_email,
        name="api-check-email",
    ),  # GET: ?email=… → { exists: bool }
    path(
        "auth/check-nickname/",
        check_nickname,
        name="api-check-nickname",
    ),  # GET: ?nickname=… → { exists: bool }
    # ─ 회원가입시 이메일 인증 ─────────────────────────────────────────────────────
    path(
        "auth/email-verify/request/",
        SignupEmailVerifyRequestAPIView.as_view(),
        name="email-verify-request",
    ),
    path(
        "auth/email-verify/verify/",
        SignupEmailVerifyVerifyAPIView.as_view(),
        name="email-verify-verify",
    ),
    # ── 비밀번호 변경 ───────────────────────────
    path(
        "auth/password-change/",
        PasswordChangeAPI.as_view(),
        name="api-password-change",
    ),
    # ─ 비밀번호 재설정 ─────────────────────────────────────────────────────
    path(
        "auth/password-reset/request/",
        PasswordResetRequestAPIView.as_view(),
        name="password-reset-request",
    ),  # POST: 이름+이메일 검증 후 인증번호 발송
    path(
        "auth/password-reset/verify/",
        PasswordResetVerifyAPIView.as_view(),
        name="password-reset-verify",
    ),  # POST: {email, code} 인증번호만 검증
    path(
        "auth/password-reset/confirm/",
        PasswordResetConfirmAPIView.as_view(),
        name="password-reset-confirm",
    ),  # POST: {email, code, new_password, new_password2} 비밀번호 변경
    # ─ 내 프로필 조회·수정 ─────────────────────────────────────────────────
    path(
        "users/me/",
        UserProfileAPI.as_view(),
        name="user-me",
    ),  # GET/PUT: 내 프로필 및 VAPID 키 조회·수정
    # ─ 푸시 알림 설정 ──────────────────────────────────────────────────────
    path(
        "push/setting/",
        push_setting,
        name="api-push-setting",
    ),  # GET/POST: 푸시 수신 여부 조회·변경
    # ─ 푸시 구독 관리 ──────────────────────────────────────────────────────
    path(
        "push/subscribe/",
        subscribe_push,
        name="api-push-subscribe",
    ),  # POST: 구독 정보 등록/업데이트
    path(
        "push/unsubscribe/",
        unsubscribe_push,
        name="api-push-unsubscribe",
    ),  # POST: 구독 해제
    # ── 소셜 로그인 (Google) ──────────────────────────────────────────────
    path(
        "auth/social/google/login/",
        google_login,
        name="google_login",
    ),  # GET: Google OAuth 동의 화면으로 리다이렉트
    path(
        "auth/social/google/callback/",
        google_callback,
        name="google_callback",
    ),  # GET: Google 콜백 처리
    # ── 주차 실력 설정 ──────────────────────────────────────────────
    path(
        "user/parking-skill/",
        set_parking_skill,
        name="set-parking-skill",
    ),  # POST: 사용자 주차 실력과 점수 설정
    # ── 알림 관리 ──────────────────────────────────────────────
    path(
        "notifications/",
        notification_list,
        name="notification-list",
    ),  # GET: 알림 목록 조회
    path(
        "notifications/<int:notification_id>/",
        notification_detail,
        name="notification-detail",
    ),  # GET/PUT: 알림 상세 조회/업데이트
    path(
        "notifications/<int:notification_id>/delete/",
        notification_delete,
        name="notification-delete",
    ),  # DELETE: 특정 알림 삭제
    path(
        "notifications/delete-all/",
        notification_delete_all,
        name="notification-delete-all",
    ),  # DELETE: 모든 알림 삭제
    path(
        "notifications/mark-all-read/",
        notification_mark_all_read,
        name="notification-mark-all-read",
    ),  # PUT: 모든 알림 읽음 처리
    path(
        "notifications/unread-count/",
        notification_unread_count,
        name="notification-unread-count",
    ),  # GET: 읽지 않은 알림 개수
    path(
        "notifications/test-push/",
        test_push_notification,
        name="test-push-notification",
    ),  # POST: 테스트 푸시 알림 전송
    path(
        "notifications/test-entry/",
        test_vehicle_entry_notification,
        name="test-vehicle-entry-notification",
    ),  # POST: 테스트 입차 알림 전송
    path(
        "notifications/test-parking/",
        test_parking_complete_notification,
        name="test-parking-complete-notification",
    ),  # POST: 테스트 주차 완료 알림 전송
    path(
        "notifications/test-grade/",
        test_grade_upgrade_notification,
        name="test-grade-upgrade-notification",
    ),  # POST: 테스트 등급 승급 알림 전송
    path(
        "notifications/test-all/",
        test_all_notifications,
        name="test-all-notifications",
    ),  # POST: 모든 알림 타입 순차 테스트
]
