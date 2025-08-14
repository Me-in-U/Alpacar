# accounts\serializers\profile.py

from rest_framework import serializers

from accounts.models import User
from djangoApp import settings


class ProfileSerializer(serializers.ModelSerializer):
    """
    사용자 프로필 정보 직렬화/역직렬화
    - 이메일, 이름(name), 닉네임, 전화번호, 푸시 설정(push_on), 점수(score) 필드 노출
    """

    # internal full_name 필드를 외부 API에서는 name으로 노출
    name = serializers.CharField(source="full_name")  # 사용자 실명 매핑 필드
    # internal push_enabled 필드를 외부 API에서는 push_on으로 노출
    push_on = serializers.BooleanField(
        source="push_enabled"
    )  # 푸시 수신 여부 매핑 필드
    # VAPID 공개키 추가 (settings에서 가져옴)
    vapid_public_key = serializers.SerializerMethodField()

    def get_vapid_public_key(self, obj):
        """
        VAPID 공개키 반환
        """
        return settings.VAPID_PUBLIC_KEY
    
    class Meta:
        model = User
        # API에 노출할 필드 목록 (vapid_public_key 추가)
        fields = ["email", "name", "nickname", "phone", "push_on", "score", "is_staff", "vapid_public_key"]
        # email과 vapid_public_key는 사용자가 수정할 수 없도록 읽기 전용
        read_only_fields = ["email", "is_staff", "vapid_public_key"]
