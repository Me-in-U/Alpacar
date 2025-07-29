# accounts/urls.py
from django.urls import path

from accounts.views.auth import LoginAPI, RefreshAPI, SignupAPI
from accounts.views.google import GoogleLogin, google_callback, google_login
from accounts.views.profile import UserProfileAPI
from accounts.views.push import push_setting, subscribe_push, unsubscribe_push

urlpatterns = [
    # 회원가입 / 로그인 / 토큰갱신
    path("api/signup/", SignupAPI.as_view(), name="api-signup"),
    path("api/login/", LoginAPI.as_view(), name="api-login"),
    path("api/token/refresh/", RefreshAPI.as_view(), name="api-token-refresh"),
    # 내 프로필 조회·수정
    path("api/user/profile/", UserProfileAPI.as_view(), name="api-user-profile"),
    # 푸시 설정(조회·변경)
    path("api/push/setting/", push_setting, name="api-push-setting"),
    # 구독/구독해제
    path("api/push/subscribe/", subscribe_push, name="api-push-subscribe"),
    path("api/push/unsubscribe/", unsubscribe_push, name="api-push-unsubscribe"),
    # ▼ 소셜 로그인 엔드포인트 ▼
    # 구글 소셜로그인
    path("api/social/google/login/", google_login, name="google_login"),
    path("api/social/google/callback/", google_callback, name="google_callback"),
    path(
        "api/social/google/login/finish/",
        GoogleLogin.as_view(),
        name="google_login_todjango",
    ),
]
