# accounts\serializers\profile.py
from rest_framework import serializers

from accounts.models import Member


class ProfileSerializer(serializers.ModelSerializer):
    push_on = serializers.BooleanField(source="push_enabled")

    class Meta:
        model = Member
        fields = ["email", "name", "nickname", "phone", "plate_number", "push_on"]
        read_only_fields = ["email"]
