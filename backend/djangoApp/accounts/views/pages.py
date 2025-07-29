# accounts/views.py
import random
import string

from django.shortcuts import redirect, render
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed


from decouple import config


def random_string(n=8):
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))


def test_methods_page(request):
    """
    템플릿 방식과 API 방식을 동시에 테스트하는 페이지 렌더
    """
    return render(request, "accounts/test_methods.html")


def push_setting_page(request):
    """
    Authorization 헤더에 Bearer <token> 이 있어야 페이지 열도록 검사
    """
    auth = JWTAuthentication()
    try:
        auth_result = auth.authenticate(request)
    except AuthenticationFailed:
        return redirect("test_methods")

    # 토큰 없으면 authenticate()가 None 반환
    if auth_result is None:
        return redirect("test_methods")

    # auth_result 가 (user, token) 튜플일 때만 진행
    user, token = auth_result

    # 여기서 request.user 등을 사용하려면 수동으로 설정
    request.user = user

    return render(
        request,
        "accounts/push_setting.html",
        {
            "VAPID_PUBLIC_KEY": config("VAPID_PUBLIC_KEY"),  # 필요 시
            "push_on": user.push_enabled,
        },
    )
