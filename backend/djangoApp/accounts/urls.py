# accounts/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.api_views import SignupAPI
from accounts.jwt_views import LoginAPI

from .views import (
    push_setting_view,
    subscribe_push,
    test_methods,
    unsubscribe_push,
    update_push_setting,
)

urlpatterns = [
    # 테스트용 페이지
    path("accounts/test_methods/", test_methods, name="test_methods"),
    # 회원가입
    path("api/signup/", SignupAPI.as_view(), name="api-signup"),
    # 로그인 (JWT 발급)
    path("api/login/", LoginAPI.as_view(), name="api-login"),
    # JWT 리프레시
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # 푸시 알림 설정 페이지
    path("push/setting/", push_setting_view, name="push-setting"),
    # 푸시 알림 설정 업데이트 (AJAX)
    path("push/setting/update/", update_push_setting, name="push-setting-update"),
    # 푸시 구독 / 구독 해제
    path("push/subscribe/", subscribe_push, name="push-subscribe"),
    path("push/unsubscribe/", unsubscribe_push, name="push-unsubscribe"),
]
