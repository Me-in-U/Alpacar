# accounts/urls.py
from django.urls import path

from accounts.views.auth import LoginAPI, RefreshAPI, SignupAPI
from accounts.views.push import push_setting, subscribe_push, unsubscribe_push

urlpatterns = [
    # 회원가입 / 로그인 / 토큰갱신
    path("api/signup/", SignupAPI.as_view(), name="api-signup"),
    path("api/login/", LoginAPI.as_view(), name="api-login"),
    path("api/token/refresh/", RefreshAPI.as_view(), name="api-token-refresh"),
    # 푸시 설정(조회·변경)
    path("api/push/setting/", push_setting, name="api-push-setting"),
    # 구독/구독해제
    path("api/push/subscribe/", subscribe_push, name="api-push-subscribe"),
    path("api/push/unsubscribe/", unsubscribe_push, name="api-push-unsubscribe"),
]
