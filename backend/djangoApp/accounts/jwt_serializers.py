# accounts/jwt_serializers.py

import hashlib

from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Member


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    이메일(field name)과 비밀번호로 로그인할 수 있도록
    username_field를 'email'로 지정합니다.
    """

    username_field = "email"

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        # 비밀번호 해시화
        pw_hash = hashlib.sha256(password.encode()).hexdigest()

        # Member 직접 조회
        try:
            user = Member.objects.get(email=email, password_hash=pw_hash)
        except Member.DoesNotExist:
            raise serializers.ValidationError(
                {"non_field_errors": ["이메일 또는 비밀번호가 올바르지 않습니다."]},
                code="authorization",
            )

        # 토큰 생성 (부모 메서드의 get_token 사용)
        token = self.get_token(user)
        return {
            "refresh": str(token),
            "access": str(token.access_token),
        }
