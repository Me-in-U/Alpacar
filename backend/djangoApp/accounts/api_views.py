# accounts/api_views.py
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import SignupSerializer


class SignupAPI(APIView):
    """
    회원가입 API
    - POST: 회원 정보(name, nickname, email, password, phone, plate_number) 수신
    - 유효하면 Member 생성 후 201 반환
    """

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "회원가입 성공"}, status=status.HTTP_201_CREATED)
        # 유효성 검사 실패 시 에러 메시지 반환
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
