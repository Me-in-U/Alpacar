# accounts\views\profile.py
from django.conf import settings
from rest_framework import status
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
