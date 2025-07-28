# accounts/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .api_views import SignupAPI
from .views import (
    test_methods,
    push_setting_view,
    update_push_setting,
    subscribe_push,
    unsubscribe_push,
)
from .jwt_views import EmailTokenObtainPairView

urlpatterns = [
    # 테스트용 페이지
    path("test_methods/", test_methods, name="test_methods"),
    # 회원가입 / 로그인 API
    path("api/signup/", SignupAPI.as_view(), name="api-signup"),
    # 기존 로그인 대신 JWT 토큰 발급
    path("api/token/", EmailTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # 푸시 알림 설정 페이지
    path("push/setting/", push_setting_view, name="push-setting"),
    # 푸시 알림 설정 업데이트 (AJAX)
    path("push/setting/update/", update_push_setting, name="push-setting-update"),
    # 푸시 구독 / 구독 해제
    path("push/subscribe/", subscribe_push, name="push-subscribe"),
    path("push/unsubscribe/", unsubscribe_push, name="push-unsubscribe"),
]
