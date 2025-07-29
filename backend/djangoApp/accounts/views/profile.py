# accounts\views\profile.py
from django.conf import settings
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.serializers.profile import ProfileSerializer


class UserProfileAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        GET /api/users/me/
        → 현재 로그인한 사용자의 프로필과 VAPID public key 반환
        """
        user = request.user
        serializer = ProfileSerializer(user)
        data = serializer.data
        print(f"[DEBUG] PROFILE GET for {user.email} → {data!r}")
        data["vapid_public_key"] = settings.VAPID_PUBLIC_KEY
        print(f"[DEBUG]   + vapid_public_key → {data['vapid_public_key']}")
        return Response(data)

    def put(self, request):
        """
        PUT /api/users/me/
        → full_name, nickname, phone, plate_number 수정
        """
        user = request.user
        serializer = ProfileSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
