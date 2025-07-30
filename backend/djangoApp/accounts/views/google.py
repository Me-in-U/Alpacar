# accounts/views/google.py

import requests
from urllib.parse import urlencode
from django.shortcuts import redirect
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from decouple import config

from accounts.models import User
from allauth.socialaccount.models import SocialAccount

# ── 환경／상수 ───────────────────────────────────────────────────────────
BASE_URL = "http://localhost:8000"
CALLBACK_PATH = "/api/auth/social/google/callback/"
CALLBACK_URI = BASE_URL + CALLBACK_PATH
GOOGLE_AUTH_URI = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URI = "https://www.googleapis.com/oauth2/v1/userinfo"
GOOGLE_SCOPE = "https://www.googleapis.com/auth/userinfo.email"


def issue_tokens(user):
    """주어진 user에게 access/refresh JWT 토큰 발급"""
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


# ── 1) 구글 로그인 시작: 동의 화면으로 리다이렉트 ───────────────────────────
def google_login(request):
    client_id = config("GOOGLE_CLIENT_ID")
    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": CALLBACK_URI,
        "scope": GOOGLE_SCOPE,
        "access_type": "online",
        "prompt": "consent",
    }
    return redirect(f"{GOOGLE_AUTH_URI}?{urlencode(params)}")


# ── 2) 콜백 처리: code → access_token → 이메일 조회 → 회원가입/로그인 → 토큰 발행 ─────
def google_callback(request):
    code = request.GET.get("code")
    if not code:
        return JsonResponse({"error": "missing code"}, status=400)

    # 2‑1) access_token 교환
    data = {
        "client_id": config("GOOGLE_CLIENT_ID"),
        "client_secret": config("GOOGLE_CLIENT_SECRET"),
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": CALLBACK_URI,
    }
    token_res = requests.post(GOOGLE_TOKEN_URI, data=data)
    token_json = token_res.json()
    if token_res.status_code != 200 or "error" in token_json:
        return JsonResponse(token_json, status=token_res.status_code)

    access_token = token_json["access_token"]

    # 2‑2) 이메일 조회
    userinfo_res = requests.get(
        GOOGLE_USERINFO_URI, params={"access_token": access_token}
    )
    if userinfo_res.status_code != 200:
        return JsonResponse({"error": "failed to fetch userinfo"}, status=400)
    email = userinfo_res.json().get("email")
    if not email:
        return JsonResponse({"error": "email not provided"}, status=400)

    # 3) 회원 조회／생성 (닉네임 충돌 처리 + unusable password)
    email_local = email.split("@", 1)[0]
    base_nickname = f"g_{email_local}"
    nickname = base_nickname
    suffix = 0

    # 트랜잭션 안에서 조회 & 생성 안전하게 처리
    with transaction.atomic():
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # 닉네임 중복 확인
            while User.objects.filter(nickname=nickname).exists():
                suffix += 1
                nickname = f"{base_nickname}_{suffix}"
            user = User(
                email=email,
                full_name=email_local,
                nickname=nickname,
                phone="",
            )
            user.set_unusable_password()
            user.save()

        # 4) SocialAccount 보장
        SocialAccount.objects.get_or_create(
            user=user,
            provider="google",
            uid=email,
            defaults={"extra_data": userinfo_res.json()},
        )

    # 5) JWT 발행 후 클라이언트에 HTML로 전달 (토큰 저장 & 리다이렉트)
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


# ── 3) dj-rest-auth SocialLoginView (POST: code/id_token → JWT) ─────────────
from allauth.socialaccount.providers.google import views as google_views
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView


class GoogleLogin(SocialLoginView):
    adapter_class = google_views.GoogleOAuth2Adapter
    client_class = OAuth2Client
    callback_url = CALLBACK_URI
