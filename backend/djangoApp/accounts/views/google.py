# accounts/views/google.py

from urllib.parse import urlencode

import requests
from allauth.socialaccount.models import SocialAccount
from decouple import config
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import User

# ── 환경／상수 ───────────────────────────────────────────────────────────
BASE_URL = "http://localhost:8000"  # API 서버 기본 URL
CALLBACK_PATH = "/api/auth/social/google/callback/"  # 구글 콜백 엔드포인트
CALLBACK_URI = BASE_URL + CALLBACK_PATH  # 전체 콜백 URI
GOOGLE_AUTH_URI = "https://accounts.google.com/o/oauth2/v2/auth"  # 구글 인증 URL
GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"  # 토큰 발급 URL
GOOGLE_USERINFO_URI = (
    "https://www.googleapis.com/oauth2/v1/userinfo"  # 사용자 정보 조회 URL
)
GOOGLE_SCOPE = "https://www.googleapis.com/auth/userinfo.email"  # 요청할 OAuth2 범위


def issue_tokens(user):
    """
    주어진 user에게 access/refresh JWT 토큰 발급
    """
    refresh = RefreshToken.for_user(user)  # RefreshToken 인스턴스 생성
    return {
        "refresh": str(refresh),  # 문자열화된 refresh 토큰
        "access": str(refresh.access_token),  # 문자열화된 access 토큰
    }


def google_login(request):
    """
    구글 OAuth 동의 화면으로 리다이렉트
    """
    client_id = config("GOOGLE_CLIENT_ID")  # .env에서 클라이언트 ID 가져오기
    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": CALLBACK_URI,
        "scope": GOOGLE_SCOPE,
        "access_type": "online",
        "prompt": "consent",  # 사용자 동의 화면 강제 표시
    }
    # authorization code를 얻기 위해 구글 인증 페이지로 리다이렉트
    return redirect(f"{GOOGLE_AUTH_URI}?{urlencode(params)}")


def google_callback(request):
    """
    구글 콜백 처리:
    - code로 access_token 요청
    - 사용자 정보 조회
    - User 조회/생성 및 SocialAccount 보장
    - JWT 발급 후 HTML 반환
    """
    code = request.GET.get("code")
    if not code:
        # 인증 코드 없으면 Bad Request
        return JsonResponse({"error": "missing code"}, status=400)

    # authorization code로 access_token 요청
    data = {
        "client_id": config("GOOGLE_CLIENT_ID"),
        "client_secret": config("GOOGLE_CLIENT_SECRET"),
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": CALLBACK_URI,
    }
    token_res = requests.post(GOOGLE_TOKEN_URI, data=data)  # 토큰 교환 요청
    token_json = token_res.json()
    if token_res.status_code != 200 or "error" in token_json:
        # 실패 시 원본 응답 반환
        return JsonResponse(token_json, status=token_res.status_code)

    access_token = token_json["access_token"]  # access_token 저장

    # 발급된 토큰으로 구글 사용자 정보 조회
    userinfo_res = requests.get(
        GOOGLE_USERINFO_URI, params={"access_token": access_token}
    )  # OAuth2 사용자 정보 요청
    if userinfo_res.status_code != 200:
        return JsonResponse({"error": "failed to fetch userinfo"}, status=400)
    email = userinfo_res.json().get("email")
    if not email:
        return JsonResponse({"error": "email not provided"}, status=400)

    # User 조회 또는 생성 (닉네임 충돌 처리 + 비밀번호 unusable 설정)
    email_local = email.split("@", 1)[0]  # 이메일 로컬 파트
    base_nickname = f"g_{email_local}"
    nickname = base_nickname
    suffix = 0

    # 트랜잭션 안에서 조회 & 생성 안전하게 처리
    with transaction.atomic():  # 트랜잭션 보장
        try:
            user = User.objects.get(email=email)  # 이미 가입된 사용자 조회
        except User.DoesNotExist:
            # 닉네임 중복 시 suffix 부여
            while User.objects.filter(nickname=nickname).exists():
                suffix += 1
                nickname = f"{base_nickname}_{suffix}"
            user = User(
                email=email,
                full_name=email_local,
                nickname=nickname,
                phone="",  # 전화번호는 빈 문자열로 초기화
            )
            user.set_unusable_password()  # 소셜 로그인용 사용자에 비밀번호 설정 금지
            user.save()  # DB 저장

        # SocialAccount 레코드 보장
        SocialAccount.objects.get_or_create(
            user=user,
            provider="google",
            uid=email,
            defaults={"extra_data": userinfo_res.json()},
        )

    # 4) JWT 토큰 발급 및 HTML 반환
    tokens = issue_tokens(user)
    html = f"""
    <!DOCTYPE html>
    <html><head><meta charset="utf-8"></head><body>
      <script>
        localStorage.setItem('access_token', '{tokens["access"]}');
        localStorage.setItem('refresh_token', '{tokens["refresh"]}');
        window.location.href = '/static/accounts/push_setting.html';
      </script>
    </body></html>
    """
    return HttpResponse(html, content_type="text/html")


# dj-rest-auth 소셜 로그인 엔드포인트
from allauth.socialaccount.providers.google import views as google_views
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView


class GoogleLogin(SocialLoginView):
    adapter_class = google_views.GoogleOAuth2Adapter  # 구글 OAuth2 어댑터
    client_class = OAuth2Client  # OAuth2 클라이언트 라이브러리
    callback_url = CALLBACK_URI  # 콜백 URL 설정
