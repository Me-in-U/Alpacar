# accounts/urls.py
from django.urls import path

from accounts.views.auth import (
    LoginAPI,
    RefreshAPI,
    SignupAPI,
    check_email,
    check_nickname,
)
from accounts.views.google import GoogleLogin, google_callback, google_login
from accounts.views.profile import UserProfileAPI
from accounts.views.push import push_setting, subscribe_push, unsubscribe_push

urlpatterns = [
    # 회원가입 / 로그인 / 토큰갱신
    path("api/auth/signup/", SignupAPI.as_view(), name="api-signup"),
    path("api/auth/login/", LoginAPI.as_view(), name="api-login"),
    path("api/auth/token/refresh/", RefreshAPI.as_view(), name="api-token-refresh"),
    #  이메일/닉네임 중복확인
    path("api/auth/check-email/", check_email, name="api-check-email"),
    path("api/auth/check-nickname/", check_nickname, name="api-check-nickname"),
    # 내 프로필 조회·수정
    path("api/users/me/", UserProfileAPI.as_view(), name="user-me"),
    # 푸시 설정(조회·변경)
    path("api/push/setting/", push_setting, name="api-push-setting"),
    # 구독/구독해제
    path("api/push/subscribe/", subscribe_push, name="api-push-subscribe"),
    path("api/push/unsubscribe/", unsubscribe_push, name="api-push-unsubscribe"),
    # ▼ 소셜 로그인 엔드포인트 ▼
    # 구글 소셜로그인
    path("api/auth/social/google/login/", google_login, name="google_login"),
    path("api/auth/social/google/callback/", google_callback, name="google_callback"),
    path(
        "api/auth/social/google/login/finish/",
        GoogleLogin.as_view(),
        name="google_login_todjango",
    ),
]
