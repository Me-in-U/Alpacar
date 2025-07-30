# accounts\serializers\profile.py
from rest_framework import serializers

from accounts.models import User


class ProfileSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="full_name")
    push_on = serializers.BooleanField(source="push_enabled")

    class Meta:
        model = User
        fields = ["email", "name", "nickname", "phone", "push_on", "score"]
        read_only_fields = ["email"]
