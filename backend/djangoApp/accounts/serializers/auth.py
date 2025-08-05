# accounts/serializers/auth.py
import re

from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from ..models import User


class SignupSerializer(serializers.ModelSerializer):
    """
    사용자 입력(full_name, email, nickname, phone, password, password2) 검증 및 User 객체 생성
    """

    full_name = serializers.CharField(label="이름")
    email = serializers.EmailField(label="이메일")
    nickname = serializers.CharField(label="닉네임")
    phone = serializers.CharField(label="전화번호")
    password = serializers.CharField(write_only=True, label="비밀번호")
    password2 = serializers.CharField(write_only=True, label="비밀번호 확인")

    class Meta:
        model = User
        fields = ["full_name", "email", "nickname", "phone", "password", "password2"]

    def validate_full_name(self, value):
        # 공백 없이 1~18자
        if " " in value or not (1 <= len(value) <= 18):
            raise serializers.ValidationError("이름은 공백 없이 1~18자여야 합니다.")
        return value

    def validate_phone(self, value):
        # 숫자만 10~11자리
        if not re.fullmatch(r"\d{10,11}", value):
            raise serializers.ValidationError("전화번호는 숫자 10~11자리여야 합니다.")
        return value

    def validate(self, data):
        # 비밀번호 일치 확인
        if data["password"] != data["password2"]:
            raise serializers.ValidationError(
                {"password2": "비밀번호가 일치하지 않습니다."}
            )

        pwd = data["password"]

        # 1) 길이 검사
        if not (8 <= len(pwd) <= 20):
            raise serializers.ValidationError(
                {"password": "비밀번호는 8~20자여야 합니다."}
            )
        # 2) 문자·숫자·특수문자 포함 검사
        if (
            not re.search(r"[A-Za-z]", pwd)
            or not re.search(r"\d", pwd)
            or not re.search(r"[$@!%*#?&/]", pwd)
        ):
            raise serializers.ValidationError(
                {"password": "문자·숫자·특수문자를 모두 포함해야 합니다."}
            )
        # 3) 동일문자 3연속 금지
        if re.search(r"(\w)\1\1", pwd):
            raise serializers.ValidationError(
                {"password": "동일 문자를 3회 연속 사용할 수 없습니다."}
            )
        # 4) 연속문자 3연속 금지
        for i in range(len(pwd) - 2):
            a, b, c = map(ord, pwd[i : i + 3])
            if (b == a + 1 and c == b + 1) or (b == a - 1 and c == b - 1):
                raise serializers.ValidationError(
                    {"password": "연속된 문자를 3회 이상 사용할 수 없습니다."}
                )

        return data

    def create(self, validated_data):
        validated_data.pop("password2")
        return User.objects.create_user(**validated_data)


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    이메일/비밀번호 인증 후 JWT access·refresh 토큰 발급
    """

    username_field = "email"  # 이메일 필드를 username으로 사용

    @classmethod
    def get_token(cls, user):
        """
        기본 토큰 발급 로직 호출 (refresh + access)
        """
        # TokenObtainPairSerializer의 get_token 메서드 호출
        return super().get_token(user)

    def validate(self, attrs):
        """
        이메일과 비밀번호로 사용자 인증 후 JWT 토큰 데이터 반환
        """
        email = attrs.get("email")
        password = attrs.get("password")
        # Django authenticate로 이메일·비밀번호 인증 시도
        user = authenticate(
            request=self.context.get("request"), username=email, password=password
        )
        if not user:
            # 인증 실패 시 에러 반환
            raise AuthenticationFailed("이메일 또는 비밀번호가 올바르지 않습니다.")
        # 부모 클래스의 validate 호출로 JWT 생성
        data = super().validate({"email": email, "password": password})
        return data  # 토큰 데이터 반환
