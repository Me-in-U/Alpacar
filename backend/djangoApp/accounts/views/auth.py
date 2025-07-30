# accounts/views/auth.py
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from accounts.serializers.auth import EmailTokenObtainPairSerializer, SignupSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from accounts.models import User


class SignupAPI(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # 회원가입만 처리하고, 사용자 정보(or 메시지)만 반환
        return Response(
            {"message": "회원가입 성공"},
            status=status.HTTP_201_CREATED,
        )


class LoginAPI(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = EmailTokenObtainPairSerializer  # email 필드 기반


class RefreshAPI(TokenRefreshView):
    permission_classes = [AllowAny]


@api_view(["GET"])
@permission_classes([AllowAny])
def check_email(request):
    """
    GET /api/auth/check-email/?email=...
    → { exists: true } or { exists: false }
    """
    email = request.query_params.get("email")
    if email is None:
        return Response(
            {"detail": "email 파라미터가 필요합니다."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    exists = User.objects.filter(email=email).exists()
    return Response({"exists": exists})


@api_view(["GET"])
@permission_classes([AllowAny])
def check_nickname(request):
    """
    GET /api/auth/check-nickname/?nickname=...
    → { exists: true } or { exists: false }
    """
    nickname = request.query_params.get("nickname")
    if nickname is None:
        return Response(
            {"detail": "nickname 파라미터가 필요합니다."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    exists = User.objects.filter(nickname=nickname).exists()
    return Response({"exists": exists})
