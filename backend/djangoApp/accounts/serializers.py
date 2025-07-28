# accounts/serializers.py
import hashlib

from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Member


class SignupSerializer(serializers.ModelSerializer):
    """
    회원가입용 Serializer
    - password: write_only, 해시화 후 password_hash 필드에 저장
    - plate_number: 번호판 필드
    """

    password = serializers.CharField(write_only=True)
    plate_number = serializers.CharField()

    class Meta:
        model = Member
        fields = [
            "name",  # 실명
            "nickname",  # 별명
            "email",  # 로그인 이메일
            "password",  # 비밀번호 (write_only)
            "phone",  # 연락처
            "plate_number",  # 차량 번호판
        ]

    def create(self, validated_data):
        # 비밀번호 추출
        raw_password = validated_data.pop("password")
        # SHA-256 해시 생성
        validated_data["password_hash"] = hashlib.sha256(
            raw_password.encode()
        ).hexdigest()
        # 나머지 필드로 Member 객체 생성
        return super().create(validated_data)
