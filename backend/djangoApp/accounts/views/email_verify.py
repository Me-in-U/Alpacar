# accounts/views/email_verify.py

import random
import string

from django.core.mail import send_mail
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import VerificationCode


class SignupEmailVerifyRequestAPIView(APIView):
    """
    회원가입 전용 이메일 인증번호 발송
    - POST { email }
    """

    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response(
                {"detail": "이메일을 입력해주세요."}, status=status.HTTP_400_BAD_REQUEST
            )

        # 6자리 난수 생성
        code = "".join(random.choices(string.digits, k=6))
        # 기존에 남아있는 코드는 삭제하거나 그냥 덮어쓰기
        VerificationCode.objects.create(email=email, code=code)

        # 이메일 전송
        send_mail(
            "[Alpacar] 회원가입 인증번호",
            f"안녕하세요,\n\n회원가입을 위해 아래 인증번호를 입력해주세요.\n\n인증번호: {code}\n(10분간 유효)",
            None,
            [email],
            fail_silently=False,
        )
        return Response({"detail": "인증번호를 이메일로 발송했습니다."})


class SignupEmailVerifyVerifyAPIView(APIView):
    """
    회원가입 전용 인증번호 검증
    - POST { email, code }
    """

    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        code = request.data.get("code")
        if not email or not code:
            return Response(
                {"detail": "이메일과 인증번호를 모두 입력해주세요."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            vc = VerificationCode.objects.filter(email=email).latest("created_at")
        except VerificationCode.DoesNotExist:
            return Response(
                {"detail": "인증번호 요청 기록이 없습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if vc.is_expired():
            vc.delete()
            return Response(
                {"detail": "인증번호가 만료되었습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if vc.code != code:
            return Response(
                {"detail": "인증번호가 일치하지 않습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 검증 완료된 코드는 삭제해 버리는 것이 안전합니다.
        vc.delete()
        return Response({"detail": "이메일 인증이 완료되었습니다."})
