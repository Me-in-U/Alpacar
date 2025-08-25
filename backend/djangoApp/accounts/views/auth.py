# accounts/views/auth.py

from accounts.models import User
from accounts.serializers.auth import EmailTokenObtainPairSerializer, SignupSerializer
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


class SignupAPI(APIView):
    """
    사용자 회원가입 요청 처리 View
    - POST: 사용자 입력 검증 후 새 User 생성 및 성공 메시지 반환
    """

    permission_classes = [AllowAny]  # 로그인 없이 접근 허용

    @swagger_auto_schema(
        operation_description="새로운 사용자를 등록합니다.",
        request_body=SignupSerializer,
        responses={
            201: openapi.Response(
                description="회원가입 성공",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={"message": openapi.Schema(type=openapi.TYPE_STRING)},
                ),
            ),
            400: "잘못된 요청 데이터",
        },
    )
    def post(self, request):
        """
        회원가입 데이터를 받아 User 생성 후 성공 메시지 반환
        """
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)  # 입력 데이터 검증
        serializer.save()  # User 객체 생성
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

    @swagger_auto_schema(
        operation_description="이메일과 비밀번호로 로그인합니다.",
        request_body=EmailTokenObtainPairSerializer,
        responses={
            200: openapi.Response(
                description="로그인 성공",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "access": openapi.Schema(type=openapi.TYPE_STRING),
                        "refresh": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
            401: "인증 실패",
        },
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class RefreshAPI(TokenRefreshView):
    """
    refresh 토큰으로 새로운 access 토큰을 발급하는 API View
    """

    permission_classes = [AllowAny]  # 인증 없이 접근 허용

    @swagger_auto_schema(
        operation_description="리프레시 토큰으로 새로운 액세스 토큰을 발급받습니다.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={"refresh": openapi.Schema(type=openapi.TYPE_STRING)},
        ),
        responses={
            200: openapi.Response(
                description="토큰 갱신 성공",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={"access": openapi.Schema(type=openapi.TYPE_STRING)},
                ),
            ),
            401: "토큰이 유효하지 않음",
        },
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


@swagger_auto_schema(
    method="get",
    operation_description="이메일이 이미 등록되어 있는지 확인합니다.",
    manual_parameters=[
        openapi.Parameter(
            "email",
            openapi.IN_QUERY,
            description="확인할 이메일",
            type=openapi.TYPE_STRING,
            required=True,
        )
    ],
    responses={
        200: openapi.Response(
            description="이메일 존재 여부",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={"exists": openapi.Schema(type=openapi.TYPE_BOOLEAN)},
            ),
        ),
        400: "email 파라미터가 없음",
    },
)
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


@swagger_auto_schema(
    method="get",
    operation_description="닉네임이 이미 등록되어 있는지 확인합니다.",
    manual_parameters=[
        openapi.Parameter(
            "nickname",
            openapi.IN_QUERY,
            description="확인할 닉네임",
            type=openapi.TYPE_STRING,
            required=True,
        )
    ],
    responses={
        200: openapi.Response(
            description="닉네임 존재 여부",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={"exists": openapi.Schema(type=openapi.TYPE_BOOLEAN)},
            ),
        ),
        400: "nickname 파라미터가 없음",
    },
)
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
