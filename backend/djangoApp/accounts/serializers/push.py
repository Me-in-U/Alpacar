# accounts/serializers/push.py

from rest_framework import serializers

from ..models import PushSubscription


class PushToggleSerializer(serializers.Serializer):
    """
    클라이언트로부터 푸시 수신 여부(on/off)만 전달받는 Serializer
    """

    # 클라이언트가 푸시 수신 여부(true/false)만 전달
    push_on = serializers.BooleanField()


class SubscriptionSerializer(serializers.ModelSerializer):
    """
    Web Push 구독 정보(endpoint, p256dh, auth)를 직렬화/역직렬화하는 Serializer
    """

    class Meta:
        model = PushSubscription  # PushSubscription 모델과 매핑
        fields = ["endpoint", "p256dh", "auth"]  # 저장·전송할 필드 지정
