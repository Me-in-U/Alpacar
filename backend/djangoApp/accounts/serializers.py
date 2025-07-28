# accounts/serializers.py

import hashlib

from rest_framework import serializers

from .models import Member


class SignupSerializer(serializers.ModelSerializer):
    """
    DRF 회원가입 Serializer:
     - password: write_only 으로 받고
     - create() 에서 create_user() 호출
    """

    password = serializers.CharField(write_only=True)

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
        # create_user() 내부에서 set_password() 가 호출됩니다.
        return Member.objects.create_user(**validated_data)
