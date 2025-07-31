# accounts/views/password_reset.py

import random
import string

from django.core.mail import send_mail
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User, VerificationCode
from accounts.serializers.password_reset import (
    PasswordChangeSerializer,
    PasswordResetRequestSerializer,
    VerificationCodeSerializer,
)


class PasswordResetRequestAPIView(APIView):
    """
    비밀번호 재설정 요청 API View
    - POST: 이름·이메일 검증 후 6자리 인증번호 생성 및 이메일 전송
    """

    permission_classes = [AllowAny]  # 인증 없이 접근 허용

    def post(self, request):
        """
        클라이언트로부터 이름·이메일을 받아 인증번호 생성·전송 후 결과 반환
        """
        ser = PasswordResetRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)  # 이름·이메일 검증 수행

        user = ser.validated_data["user"]  # 조회된 User
        email = ser.validated_data["email"]  # 대상 이메일
        code = "".join(random.choices(string.digits, k=6))  # 6자리 난수 코드 생성
        VerificationCode.objects.create(email=email, code=code)  # 코드 DB 저장

        # 이메일 발송
        send_mail(
            "[Alpacar] 비밀번호 재설정 인증번호",
            f"{user.full_name}님,\n\n 비밀번호 재설정을 위해 아래 인증번호를 입력해주세요\n\n 인증번호: {code}\n(10분간 유효)",
            None,
            [email],
            fail_silently=False,
        )  # send_mail로 메일 전송
        return Response({"detail": "인증번호를 이메일로 전송했습니다."})  # 응답 반환


class PasswordResetVerifyAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """
        POST { email, code } 로 인증번호만 검증
        """
        ser = VerificationCodeSerializer(data=request.data)
        try:
            ser.is_valid(raise_exception=True)
        except serializers.ValidationError as e:
            return Response({"detail": e.detail}, status=status.HTTP_400_BAD_REQUEST)
        ser.is_valid(raise_exception=True)
        return Response({"detail": "인증번호 확인 완료"}, status=status.HTTP_200_OK)


class PasswordResetConfirmAPIView(APIView):
    """
    비밀번호 재설정 확인 API View
    - POST: 인증번호 및 새 비밀번호 확인 후 비밀번호 변경
    """

    permission_classes = [AllowAny]  # 인증 없이 접근 허용

    def post(self, request):
        """
        인증번호와 새 비밀번호를 검증한 뒤, 비밀번호 업데이트 및 코드 삭제
        """
        ser = PasswordChangeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)  # 코드 및 새 비밀번호 검증

        email = ser.validated_data["email"]  # 대상 이메일
        new_pw = ser.validated_data["new_password"]  # 새 비밀번호

        # 사용자 조회 및 비밀번호 변경
        user = User.objects.get(email=email)
        user.set_password(new_pw)  # 비밀번호 해시 저장
        user.save()  # DB에 반영

        # 사용된 인증 코드 삭제
        ser.validated_data["verification_code"].delete()

        return Response(
            {"detail": "비밀번호가 성공적으로 변경되었습니다."}
        )  # 응답 반환
