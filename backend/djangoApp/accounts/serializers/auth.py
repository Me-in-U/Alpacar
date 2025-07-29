# accounts/serializers/auth.py

from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from ..models import User


class SignupSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(label="이름")
    password = serializers.CharField(write_only=True, label="비밀번호")
    password2 = serializers.CharField(write_only=True, label="비밀번호 확인")
    email = serializers.EmailField(label="이메일")
    nickname = serializers.CharField(label="닉네임")
    phone = serializers.CharField(label="전화번호")

    class Meta:
        model = User
        fields = ["full_name", "email", "nickname", "phone", "password", "password2"]

    def validate(self, data):
        if data["password"] != data["password2"]:
            raise serializers.ValidationError(
                {"password2": "비밀번호가 일치하지 않습니다."}
            )
        return data

    def create(self, validated_data):
        # password2는 create_user에 필요 없으므로 제거
        validated_data.pop("password2")
        return User.objects.create_user(**validated_data)


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
