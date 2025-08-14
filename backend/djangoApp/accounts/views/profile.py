# accounts\views\profile.py
from allauth.socialaccount.models import SocialAccount
from django.conf import settings
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.serializers.profile import ProfileSerializer


class UserProfileAPI(APIView):
    """
    사용자 프로필 조회 및 수정 API View
    - GET: 현재 로그인한 사용자의 프로필 및 VAPID public key 반환
    - PUT: 프로필 정보(partial)를 업데이트
    """

    permission_classes = [IsAuthenticated]  # 로그인된 사용자만 접근 허용

    def get(self, request):
        """
        GET /api/users/me/ → 프로필 데이터 + VAPID public key 반환
        """
        user = request.user  # 인증된 사용자 객체
        serializer = ProfileSerializer(user)  # User 객체 직렬화
        data = serializer.data  # 직렬화된 프로필 데이터 취득
        # DEBUG: 프로필 데이터 로그 출력
        print(f"[DEBUG] PROFILE GET for {user.email} → {data!r}")

        # 소셜 로그인 사용자 여부 확인 (user_id 기반)
        is_social_user = SocialAccount.objects.filter(user_id=user.id).exists()
        data["is_social_user"] = is_social_user

        data["vapid_public_key"] = settings.VAPID_PUBLIC_KEY
        # DEBUG: VAPID 키 로그 출력
        print(f"[DEBUG]   + vapid_public_key → {data['vapid_public_key']}")
        return Response(data)  # 프로필 및 키 포함 응답 반환

    def put(self, request):
        """
        PUT /api/users/me/ → 부분 업데이트된 프로필 데이터 반환
        """
        user = request.user  # 인증된 사용자
        # partial=True: 부분 필드 업데이트 허용
        serializer = ProfileSerializer(user, data=request.data, partial=True)
        # 입력 데이터 검증
        if serializer.is_valid():
            serializer.save()  # 변경 내용 저장
            return Response(serializer.data)  # 업데이트된 프로필 반환
        # 검증 실패 시 오류 및 400 응답
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method="post",
    operation_description="사용자의 주차 실력과 점수를 설정합니다.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "parking_skill": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="주차 실력 (beginner, intermediate, advanced)",
                enum=["beginner", "intermediate", "advanced"],
            ),
            "score": openapi.Schema(
                type=openapi.TYPE_INTEGER, description="주차 점수 (0-100)"
            ),
        },
        required=["parking_skill", "score"],
    ),
    responses={
        200: openapi.Response(
            description="주차 실력 설정 성공",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "message": openapi.Schema(type=openapi.TYPE_STRING),
                    "parking_skill": openapi.Schema(type=openapi.TYPE_STRING),
                    "score": openapi.Schema(type=openapi.TYPE_INTEGER),
                },
            ),
        ),
        400: "잘못된 요청 데이터",
        401: "인증되지 않은 사용자",
    },
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def set_parking_skill(request):
    """
    POST /api/user/parking-skill/
    → 사용자의 주차 실력과 점수를 설정
    """
    parking_skill = request.data.get("parking_skill")
    score = request.data.get("score")

    if not parking_skill or score is None:
        return Response(
            {"detail": "parking_skill과 score는 필수입니다."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # 유효한 주차 실력인지 확인
    valid_skills = ["beginner", "intermediate", "advanced"]
    if parking_skill not in valid_skills:
        return Response(
            {"detail": f"parking_skill은 {valid_skills} 중 하나여야 합니다."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # 점수 범위 확인
    try:
        score = int(score)
        if score < 0 or score > 100:
            return Response(
                {"detail": "score는 0-100 범위의 정수여야 합니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )
    except (ValueError, TypeError):
        return Response(
            {"detail": "score는 정수여야 합니다."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # 사용자 정보 업데이트
    user = request.user
    user.score = score
    user.save()

    return Response(
        {
            "message": "주차 실력이 설정되었습니다.",
            "parking_skill": parking_skill,
            "score": score,
        }
    )
