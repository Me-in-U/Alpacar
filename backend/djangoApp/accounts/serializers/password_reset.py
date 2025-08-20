# accounts/serializers/password_reset.py

from accounts.models import VerificationCode
from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    이름·이메일 검증 후 User 인스턴스 조회
    """

    name = serializers.CharField(max_length=50)  # 사용자 이름 입력 필드
    email = serializers.EmailField()  # 이메일 입력 필드

    def validate(self, attrs):
        """
        입력된 이름과 이메일로 사용자 조회 후 attrs에 저장
        """
        name = attrs.get("name")
        email = attrs.get("email")
        try:
            user = User.objects.get(full_name=name, email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                "이름 또는 이메일이 일치하는 사용자가 없습니다."
            )  # 사용자 미존재 처리
        attrs["user"] = user  # 조회된 User 객체 저장
        return attrs  # 검증된 attrs 반환


class VerificationCodeSerializer(serializers.Serializer):
    """
    이메일, 코드 일치 및 만료 여부 검증
    """

    email = serializers.EmailField()  # 인증 요청된 이메일
    code = serializers.CharField(max_length=6)  # 전송된 6자리 코드

    def validate(self, attrs):
        """
        최신 VerificationCode 조회, 만료 및 일치 여부 검증
        """
        # 최근 인증 코드 불러오기
        try:
            vc = VerificationCode.objects.filter(email=attrs["email"]).latest(
                "created_at"
            )
        except VerificationCode.DoesNotExist:
            # 요청 기록 없으면 에러
            raise serializers.ValidationError("인증번호 요청이 없습니다.")

        # 코드 만료 여부 확인 (10분 기준)
        if vc.is_expired():
            raise serializers.ValidationError("인증번호가 만료되었습니다.")

        # 코드 불일치 처리
        if vc.code != attrs["code"]:
            raise serializers.ValidationError("인증번호가 일치하지 않습니다.")

        attrs["verification_code"] = vc  # 검증된 코드 객체 저장
        return attrs  # 검증된 attrs 반환


class PasswordChangeSerializer(serializers.Serializer):
    """
    인증 코드 검증 후 새 비밀번호 일치 여부 확인
    """

    email = serializers.EmailField()  # 비밀번호 변경 대상 이메일
    code = serializers.CharField(max_length=6)  # 인증 코드
    new_password = serializers.CharField(min_length=8)  # 새 비밀번호
    new_password2 = serializers.CharField(min_length=8)  # 새 비밀번호 확인

    def validate(self, attrs):
        """
        VerificationCodeSerializer로 코드 검증 및 새 비밀번호 일치 여부 검증
        """
        # 인증코드 유효성 검증 수행
        ver_ser = VerificationCodeSerializer(
            data={"email": attrs["email"], "code": attrs["code"]}
        )
        ver_ser.is_valid(raise_exception=True)

        # 검증된 VerificationCode 인스턴스를 attrs에 저장
        attrs["verification_code"] = ver_ser.validated_data["verification_code"]

        # 새 비밀번호 일치 여부 검증
        if attrs["new_password"] != attrs["new_password2"]:
            raise serializers.ValidationError("새 비밀번호와 확인이 일치하지 않습니다.")
        return attrs  # 최종 검증된 attrs 반환
