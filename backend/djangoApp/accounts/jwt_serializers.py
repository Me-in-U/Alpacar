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

    @classmethod
    def get_token(cls, user):
        return super().get_token(user)

    def validate(self, attrs):
        # attrs: {"email": "...", "password": "..."}
        email = attrs.get("email")
        password = attrs.get("password")
        user = authenticate(
            request=self.context.get("request"), username=email, password=password
        )
        if not user:
            raise serializers.ValidationError(
                {"detail": "이메일 또는 비밀번호가 올바르지 않습니다."},
                code="authorization",
            )
        # super().validate()를 호출하면 user를 self.user로 설정하고
        # refresh/access 토큰을 생성해 줍니다.
        data = super().validate({"email": email, "password": password})
        return data
