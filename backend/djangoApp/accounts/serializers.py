# accounts/serializers.py
import hashlib

from rest_framework import serializers

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


class LoginSerializer(serializers.Serializer):
    """
    로그인용 Serializer
    - email / password 입력받아 검증 후 Member 인스턴스를 반환
    """

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        # 입력 비밀번호 해시화
        pw_hash = hashlib.sha256(data["password"].encode()).hexdigest()
        # 이메일+해시로 사용자 조회
        try:
            user = Member.objects.get(email=data["email"], password_hash=pw_hash)
        except Member.DoesNotExist:
            # 인증 실패 시 에러
            raise serializers.ValidationError("이메일 또는 비밀번호가 틀립니다.")
        # 성공 시 사용자 정보 반환
        return {"user": user}
