# accounts/urls.py
from django.urls import path
from .views import (
    subscribe_push,
    test_methods,
    push_setting_view,
    unsubscribe_push,
    update_push_setting,
)
from .api_views import SignupAPI, LoginAPI

urlpatterns = [
    # 테스트용 페이지
    path("test_methods/", test_methods, name="test_methods"),
    path("api/signup/", SignupAPI.as_view(), name="api-signup"),
    path("api/login/", LoginAPI.as_view(), name="api-login"),
    path("push/setting/", push_setting_view, name="push-setting"),
    path("push/setting/update/", update_push_setting, name="push-setting-update"),
    path("push/subscribe/", subscribe_push, name="push-subscribe"),
    path("push/unsubscribe/", unsubscribe_push, name="push-unsubscribe"),
]
