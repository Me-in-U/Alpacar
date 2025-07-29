# accounts/serializers/auth.py

from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from ..models import Member


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
