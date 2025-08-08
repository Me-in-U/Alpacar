# accounts/serializers/notifications.py
from rest_framework import serializers
from ..models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """
    알림 시리얼라이저
    - 알림 목록 조회 및 상세 정보 제공
    """

    class Meta:
        model = Notification
        fields = [
            'id',
            'title',
            'message',
            'notification_type',
            'data',
            'is_read',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class NotificationUpdateSerializer(serializers.ModelSerializer):
    """
    알림 업데이트 시리얼라이저 (읽음 상태 변경 등)
    """

    class Meta:
        model = Notification
        fields = ['is_read']