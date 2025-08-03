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
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class SignupAPI(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="새로운 사용자를 등록합니다.",
        request_body=SignupSerializer,
        responses={
            201: openapi.Response(
                description="회원가입 성공",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: "잘못된 요청 데이터"
        }
    )
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

    @swagger_auto_schema(
        operation_description="이메일과 비밀번호로 로그인합니다.",
        request_body=EmailTokenObtainPairSerializer,
        responses={
            200: openapi.Response(
                description="로그인 성공",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'access': openapi.Schema(type=openapi.TYPE_STRING),
                        'refresh': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            401: "인증 실패"
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class RefreshAPI(TokenRefreshView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="리프레시 토큰으로 새로운 액세스 토큰을 발급받습니다.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'refresh': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
        responses={
            200: openapi.Response(
                description="토큰 갱신 성공",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'access': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            401: "토큰이 유효하지 않음"
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


@swagger_auto_schema(
    method='get',
    operation_description="이메일이 이미 등록되어 있는지 확인합니다.",
    manual_parameters=[
        openapi.Parameter(
            'email',
            openapi.IN_QUERY,
            description="확인할 이메일",
            type=openapi.TYPE_STRING,
            required=True
        )
    ],
    responses={
        200: openapi.Response(
            description="이메일 존재 여부",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'exists': openapi.Schema(type=openapi.TYPE_BOOLEAN)
                }
            )
        ),
        400: "email 파라미터가 없음"
    }
)
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


@swagger_auto_schema(
    method='get',
    operation_description="닉네임이 이미 등록되어 있는지 확인합니다.",
    manual_parameters=[
        openapi.Parameter(
            'nickname',
            openapi.IN_QUERY,
            description="확인할 닉네임",
            type=openapi.TYPE_STRING,
            required=True
        )
    ],
    responses={
        200: openapi.Response(
            description="닉네임 존재 여부",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'exists': openapi.Schema(type=openapi.TYPE_BOOLEAN)
                }
            )
        ),
        400: "nickname 파라미터가 없음"
    }
)
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
