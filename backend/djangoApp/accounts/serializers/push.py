# accounts/serializers/push.py

from rest_framework import serializers

from ..models import PushSubscription


class PushToggleSerializer(serializers.Serializer):
    push_on = serializers.BooleanField()


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PushSubscription
        fields = ["endpoint", "p256dh", "auth"]
