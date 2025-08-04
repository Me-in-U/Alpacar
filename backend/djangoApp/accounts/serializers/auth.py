# accounts/serializers/auth.py

from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import AuthenticationFailed
from ..models import User


class SignupSerializer(serializers.ModelSerializer):
    """
    사용자 입력(full_name, email, nickname, phone, password, password2) 검증 및 User 객체 생성
    """

    full_name = serializers.CharField(label="이름")  # 사용자 실명 입력 필드
    password = serializers.CharField(
        write_only=True, label="비밀번호"
    )  # 비밀번호 입력(쓰기 전용)
    password2 = serializers.CharField(
        write_only=True, label="비밀번호 확인"
    )  # 비밀번호 확인 입력
    email = serializers.EmailField(label="이메일")  # 이메일 입력 필드
    nickname = serializers.CharField(label="닉네임")  # 닉네임 입력 필드
    phone = serializers.CharField(label="전화번호")  # 전화번호 입력 필드

    class Meta:
        model = User
        fields = ["full_name", "email", "nickname", "phone", "password", "password2"]

    def validate(self, data):
        """
        비밀번호와 확인 비밀번호 일치 여부 검증
        """
        # 입력된 두 비밀번호가 다르면 예외 발생
        if data["password"] != data["password2"]:
            raise serializers.ValidationError(
                {"password2": "비밀번호가 일치하지 않습니다."}
            )  # 비밀번호 불일치 처리
        return data  # 검증 통과 시 데이터 반환

    def create(self, validated_data):
        """
        불필요한 password2 제거 후 UserManager.create_user로 사용자 생성
        """
        validated_data.pop("password2")  # 확인용 password 필드 제거
        return User.objects.create_user(**validated_data)  # 새 사용자 생성


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
