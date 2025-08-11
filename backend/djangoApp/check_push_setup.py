#!/usr/bin/env python
"""
Simple push notification setup check
"""

import os
import sys
import django

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoApp.settings')
django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model
from accounts.models import PushSubscription, Notification

def check_push_setup():
    """Check push notification setup"""
    
    print("=" * 50)
    print("PUSH NOTIFICATION SETUP CHECK")
    print("=" * 50)
    
    # 1. Check VAPID keys
    print("\n1. VAPID Keys:")
    vapid_public = getattr(settings, 'VAPID_PUBLIC_KEY', None)
    vapid_private = getattr(settings, 'VAPID_PRIVATE_KEY', None)
    
    print(f"   PUBLIC KEY: {'OK' if vapid_public else 'MISSING'}")
    print(f"   PRIVATE KEY: {'OK' if vapid_private else 'MISSING'}")
    
    # 2. Check users
    print("\n2. Users:")
    User = get_user_model()
    total_users = User.objects.count()
    push_enabled = User.objects.filter(push_enabled=True).count()
    
    print(f"   Total users: {total_users}")
    print(f"   Push enabled: {push_enabled}")
    
    # 3. Check subscriptions
    print("\n3. Push Subscriptions:")
    total_subs = PushSubscription.objects.count()
    print(f"   Total subscriptions: {total_subs}")
    
    # 4. Show user details
    print("\n4. User Details:")
    for user in User.objects.all()[:3]:
        subs = PushSubscription.objects.filter(user=user).count()
        print(f"   {user.email}: push_enabled={user.push_enabled}, subscriptions={subs}")
    
    # 5. Test notification
    print("\n5. Test Notification:")
    test_user = User.objects.first()
    if test_user:
        try:
            from accounts.utils import create_notification
            notification = create_notification(
                user=test_user,
                title="Test Push",
                message="Admin push notification test",
                notification_type='system',
                data={'test': True}
            )
            print(f"   Test notification created: ID {notification.id}")
        except Exception as e:
            print(f"   ERROR: {str(e)}")
    
    print("\n" + "=" * 50)

if __name__ == '__main__':
    check_push_setup()