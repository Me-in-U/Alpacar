# accounts/views.py

import random
import string

from decouple import config
from django.shortcuts import redirect, render
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication


def push_setting_page(request):
    """
    푸시 알림 설정 페이지 렌더링
    - JWTAuthentication으로 요청 인증 검사
    - Authorization 헤더에 Bearer <토큰>이 없거나 유효하지 않으면 'test_methods' 뷰로 리다이렉트
    - 인증 성공 시 'accounts/push_setting.html' 템플릿에 필요한 컨텍스트 전달
    """
    auth = JWTAuthentication()  # JWT 인증 객체 생성
    try:
        auth_result = auth.authenticate(request)  # 헤더에서 토큰 추출 및 검증
    except AuthenticationFailed:
        return redirect("test_methods")  # 인증 실패 시 리다이렉트

    if auth_result is None:
        # 토큰이 없거나 authenticate()가 None을 반환하면 리다이렉트
        return redirect("test_methods")

    user, _ = auth_result  # 인증된 user와 token 분해
    request.user = user  # 뷰 내에서 request.user 사용 가능하도록 설정

    # 인증된 사용자 정보와 VAPID 공개키를 템플릿에 전달하여 렌더링
    return render(
        request,
        "accounts/push_setting.html",
        {
            "VAPID_PUBLIC_KEY": config(
                "VAPID_PUBLIC_KEY"
            ),  # 환경변수에서 VAPID 공개키 로드
            "push_on": user.push_enabled,  # 사용자의 현재 푸시 수신 설정 상태
        },
    )
