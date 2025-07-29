# accounts\serializers\profile.py
from rest_framework import serializers

from accounts.models import User


class ProfileSerializer(serializers.ModelSerializer):
    # 모델 필드명이 full_name으로 바뀌었으니 source도 변경할 것
    name = serializers.CharField(source="full_name")
    push_on = serializers.BooleanField(source="push_enabled")

    class Meta:
        model = User
        fields = ["email", "name", "nickname", "phone", "push_on", "score"]
        read_only_fields = ["email", "score"]
