# accounts/views/auth.py

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from accounts.models import User
from accounts.serializers.auth import EmailTokenObtainPairSerializer, SignupSerializer


class SignupAPI(APIView):
    """
    사용자 회원가입 요청 처리 View
    - POST: 사용자 입력 검증 후 새 User 생성 및 성공 메시지 반환
    """

    permission_classes = [AllowAny]  # 로그인 없이 접근 허용

    def post(self, request):
        """
        회원가입 데이터를 받아 User 생성 후 성공 메시지 반환
        """
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)  # 입력 데이터 검증
        user = serializer.save()  # User 객체 생성
        # 회원가입 성공 메시지 반환
        return Response(
            {"message": "회원가입 성공"},
            status=status.HTTP_201_CREATED,
        )


class LoginAPI(TokenObtainPairView):
    """
    이메일/비밀번호 기반 JWT 토큰 발급 API View
    - access 및 refresh 토큰 생성
    """

    permission_classes = [AllowAny]  # 인증 없이 접근 허용
    serializer_class = EmailTokenObtainPairSerializer  # 이메일 로그인용 Serializer


class RefreshAPI(TokenRefreshView):
    """
    refresh 토큰으로 새로운 access 토큰을 발급하는 API View
    """

    permission_classes = [AllowAny]  # 인증 없이 접근 허용


@api_view(["GET"])
@permission_classes([AllowAny])
def check_email(request):
    """
    이메일 중복 확인 엔드포인트
    - 쿼리 파라미터 'email'을 받아 DB 존재 여부 반환
    """
    email = request.query_params.get("email")
    if email is None:
        # email 파라미터 누락 시 오류 반환
        return Response(
            {"detail": "email 파라미터가 필요합니다."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    exists = User.objects.filter(email=email).exists()  # DB에 이메일 존재 여부 조회
    return Response({"exists": exists})  # {exists: true/false} 반환


@api_view(["GET"])
@permission_classes([AllowAny])
def check_nickname(request):
    """
    닉네임 중복 확인 엔드포인트
    - 쿼리 파라미터 'nickname'을 받아 DB 존재 여부 반환
    """
    nickname = request.query_params.get("nickname")
    if nickname is None:
        # nickname 파라미터 누락 시 오류 반환
        return Response(
            {"detail": "nickname 파라미터가 필요합니다."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    exists = User.objects.filter(
        nickname=nickname
    ).exists()  # DB에 닉네임 존재 여부 조회
    return Response({"exists": exists})  # {exists: true/false} 반환
