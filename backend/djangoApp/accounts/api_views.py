# accounts/api_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import SignupSerializer, LoginSerializer


class SignupAPI(APIView):
    def post(self, request):
        ser = SignupSerializer(data=request.data)
        if ser.is_valid():
            ser.save()
            return Response({"detail": "회원가입 성공"}, status=status.HTTP_201_CREATED)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginAPI(APIView):
    def post(self, request):
        ser = LoginSerializer(data=request.data)
        if ser.is_valid():
            user = ser.validated_data["user"]
            # 세션 설정 원하면 아래 주석 해제
            request.session["member_id"] = user.id
            return Response({"detail": "로그인 성공", "member_id": user.id})
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
