#!/usr/bin/env python
"""
Create test push subscription for testing
"""

import os
import sys
import django

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoApp.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import PushSubscription

def create_test_subscription():
    """Create test push subscription"""
    
    User = get_user_model()
    test_user = User.objects.filter(push_enabled=True).first()
    
    if not test_user:
        print("No user with push enabled found")
        return
    
    # Create test subscription (these are dummy values for testing)
    test_subscription, created = PushSubscription.objects.get_or_create(
        user=test_user,
        defaults={
            'endpoint': 'https://fcm.googleapis.com/fcm/send/test-endpoint',
            'p256dh': 'test-p256dh-key',
            'auth': 'test-auth-key'
        }
    )
    
    if created:
        print(f"Created test subscription for {test_user.email}")
    else:
        print(f"Test subscription already exists for {test_user.email}")
    
    # Test notification
    from accounts.utils import create_notification
    
    try:
        notification = create_notification(
            user=test_user,
            title="Test Push Notification",
            message="Testing push notification system with subscription",
            notification_type='system',
            data={'test': True}
        )
        print(f"Test notification created: {notification.id}")
    except Exception as e:
        print(f"Error creating notification: {e}")

if __name__ == '__main__':
    create_test_subscription()