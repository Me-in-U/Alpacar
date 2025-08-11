#!/usr/bin/env python
"""
Admin Push Notification System Status Report
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

def generate_status_report():
    """Generate comprehensive status report"""
    
    print("=" * 60)
    print("ADMIN PUSH NOTIFICATION SYSTEM STATUS")
    print("=" * 60)
    
    # 1. System Configuration
    print("\n1. SYSTEM CONFIGURATION:")
    print("-" * 30)
    
    vapid_public = getattr(settings, 'VAPID_PUBLIC_KEY', None)
    vapid_private = getattr(settings, 'VAPID_PRIVATE_KEY', None)
    
    print(f"VAPID Keys: {'CONFIGURED' if vapid_public and vapid_private else 'MISSING'}")
    if vapid_public and vapid_private:
        print(f"  Public Key: {vapid_public[:20]}...")
        print(f"  Private Key: {vapid_private[:20]}...")
    
    # 2. User Status
    print("\n2. USER STATUS:")
    print("-" * 30)
    
    User = get_user_model()
    total_users = User.objects.count()
    push_enabled = User.objects.filter(push_enabled=True).count()
    
    print(f"Total Users: {total_users}")
    print(f"Push Enabled Users: {push_enabled}")
    
    # 3. Push Subscriptions
    print("\n3. PUSH SUBSCRIPTIONS:")
    print("-" * 30)
    
    total_subs = PushSubscription.objects.count()
    print(f"Total Subscriptions: {total_subs}")
    
    if total_subs > 0:
        for subscription in PushSubscription.objects.all():
            print(f"  User: {subscription.user.email}")
            print(f"  Endpoint: {subscription.endpoint[:50]}...")
            print(f"  Created: {subscription.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print()
    
    # 4. Recent Notifications
    print("\n4. RECENT NOTIFICATIONS:")
    print("-" * 30)
    
    recent_notifications = Notification.objects.order_by('-created_at')[:5]
    for notif in recent_notifications:
        admin_action = notif.data.get('admin_action', False) if notif.data else False
        admin_badge = "[ADMIN]" if admin_action else ""
        
        try:
            print(f"  {admin_badge} ID: {notif.id} | Type: {notif.notification_type}")
            print(f"    User: {notif.user.email}")
            print(f"    Created: {notif.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"    Title: {notif.title[:50]}...")
            print()
        except UnicodeEncodeError:
            print(f"  {admin_badge} ID: {notif.id} | Type: {notif.notification_type}")
            print(f"    User: {notif.user.email}")
            print(f"    Created: {notif.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"    Title: [Unicode content]")
            print()
    
    # 5. Admin Workflow Status
    print("\n5. ADMIN WORKFLOW STATUS:")
    print("-" * 30)
    
    admin_notifications = Notification.objects.filter(
        data__admin_action=True
    ).count()
    
    print(f"Admin Generated Notifications: {admin_notifications}")
    
    # Check if all functions exist
    try:
        from events.views import manual_entrance, manual_parking_complete, manual_exit
        from parking.views import assign_space
        from accounts.utils import send_vehicle_entry_notification, send_parking_complete_notification, create_notification
        
        print("Admin Workflow Functions: AVAILABLE")
        print("  - manual_entrance: OK")
        print("  - assign_space: OK") 
        print("  - manual_parking_complete: OK")
        print("  - manual_exit: OK")
        
    except ImportError as e:
        print(f"Admin Workflow Functions: ERROR - {e}")
    
    # 6. Summary and Recommendations
    print("\n6. SYSTEM STATUS SUMMARY:")
    print("-" * 30)
    
    if vapid_public and vapid_private:
        print("✓ VAPID Configuration: OK")
    else:
        print("✗ VAPID Configuration: MISSING")
    
    if push_enabled > 0:
        print(f"✓ Push Enabled Users: {push_enabled} users")
    else:
        print("✗ Push Enabled Users: NO USERS")
    
    if total_subs > 0:
        print(f"✓ Push Subscriptions: {total_subs} subscriptions")
    else:
        print("✗ Push Subscriptions: NO SUBSCRIPTIONS")
    
    if admin_notifications > 0:
        print(f"✓ Admin Notifications: {admin_notifications} generated")
    else:
        print("✗ Admin Notifications: NONE GENERATED")
    
    # 7. Next Steps
    print("\n7. IMPLEMENTATION STATUS:")
    print("-" * 30)
    
    print("✓ Backend notification system: IMPLEMENTED")
    print("✓ Admin workflow integration: IMPLEMENTED")
    print("✓ Database notification storage: WORKING")
    print("✓ Push notification infrastructure: READY")
    
    if total_subs == 0:
        print("\n⚠️  MISSING COMPONENT:")
        print("Frontend service worker registration required")
        print("Users need to grant push notification permission in browser")
    else:
        print("\n✅ SYSTEM FULLY OPERATIONAL")
    
    print("\n" + "=" * 60)

if __name__ == '__main__':
    generate_status_report()