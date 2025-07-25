# accounts/serializers.py
from rest_framework import serializers
from .models import Member
import hashlib


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    plate_number = serializers.CharField()

    class Meta:
        model = Member
        fields = ["name", "nickname", "email", "password", "phone", "plate_number"]

    def create(self, validated_data):
        pw = validated_data.pop("password")
        validated_data["password_hash"] = hashlib.sha256(pw.encode()).hexdigest()
        return super().create(validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        pw_hash = hashlib.sha256(data["password"].encode()).hexdigest()
        try:
            user = Member.objects.get(email=data["email"], password_hash=pw_hash)
        except Member.DoesNotExist:
            raise serializers.ValidationError("이메일 또는 비밀번호가 틀립니다.")
        return {"user": user}
