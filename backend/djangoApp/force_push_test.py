#!/usr/bin/env python
"""
Force test admin parking workflow push notifications
"""

import os
import sys
import django

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoApp.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.utils import create_notification

def test_admin_notifications():
    """Test admin parking workflow notifications"""
    
    print("=" * 50)
    print("ADMIN PARKING WORKFLOW NOTIFICATION TEST")
    print("=" * 50)
    
    User = get_user_model()
    
    # Get a test user
    test_user = User.objects.filter(push_enabled=True).first()
    if not test_user:
        test_user = User.objects.first()
        if test_user:
            test_user.push_enabled = True
            test_user.save()
            print(f"Enabled push for user: {test_user.email}")
    
    if not test_user:
        print("No test user available!")
        return
    
    print(f"Testing with user: {test_user.email}")
    print(f"Push enabled: {test_user.push_enabled}")
    
    # Test 1: Manual Entry
    print("\n1. Testing Manual Entry Notification...")
    entry_data = {
        'plate_number': '123가4567',
        'parking_lot': 'SSAFY 주차장',
        'entry_time': '2025-08-11T10:30:00Z',
        'admin_action': True,
        'action_url': '/parking-recommend',
        'action_type': 'navigate'
    }
    
    try:
        notification1 = create_notification(
            user=test_user,
            title="🚗 입차 알림",
            message="123가4567 차량이 SSAFY 주차장에 입차하였습니다. 알림을 클릭하면 추천 주차자리를 안내드리겠습니다.",
            notification_type='vehicle_entry',
            data=entry_data
        )
        print(f"   ✓ Entry notification created: {notification1.id}")
    except Exception as e:
        print(f"   ✗ Entry notification failed: {e}")
    
    # Test 2: Parking Assignment
    print("\n2. Testing Parking Assignment Notification...")
    assignment_data = {
        'plate_number': '123가4567',
        'assigned_space': 'A5',
        'assignment_time': '2025-08-11T10:35:00Z',
        'admin_action': True,
        'action_url': '/parking-recommend',
        'action_type': 'navigate'
    }
    
    try:
        notification2 = create_notification(
            user=test_user,
            title="🅿️ 주차 구역 배정",
            message="123가4567 차량에 A5 구역이 배정되었습니다. 안내에 따라 주차해 주세요.",
            notification_type='parking_assignment',
            data=assignment_data
        )
        print(f"   ✓ Assignment notification created: {notification2.id}")
    except Exception as e:
        print(f"   ✗ Assignment notification failed: {e}")
    
    # Test 3: Parking Complete
    print("\n3. Testing Parking Complete Notification...")
    complete_data = {
        'plate_number': '123가4567',
        'parking_space': 'A5',
        'parking_time': '2025-08-11T10:40:00Z',
        'score': 85,
        'admin_action': True
    }
    
    try:
        notification3 = create_notification(
            user=test_user,
            title="🅿️ 주차 완료",
            message="123가4567 차량이 A5 구역에 주차를 완료했습니다. 이번 주차의 점수는 85점입니다.",
            notification_type='parking_complete',
            data=complete_data
        )
        print(f"   ✓ Complete notification created: {notification3.id}")
    except Exception as e:
        print(f"   ✗ Complete notification failed: {e}")
    
    # Test 4: Vehicle Exit
    print("\n4. Testing Vehicle Exit Notification...")
    exit_data = {
        'plate_number': '123가4567',
        'parking_space': 'A5',
        'exit_time': '2025-08-11T11:20:00Z',
        'parking_duration': '40분',
        'admin_action': True,
        'action_url': '/parking-recommend',
        'action_type': 'navigate'
    }
    
    try:
        notification4 = create_notification(
            user=test_user,
            title="🚗 출차 완료",
            message="123가4567 차량이 A5 구역에서 출차 완료되었습니다. 주차 시간: 40분",
            notification_type='vehicle_exit',
            data=exit_data
        )
        print(f"   ✓ Exit notification created: {notification4.id}")
    except Exception as e:
        print(f"   ✗ Exit notification failed: {e}")
    
    print("\n" + "=" * 50)
    print("TEST COMPLETE")
    print("=" * 50)
    
    # Check recent notifications
    from accounts.models import Notification
    recent = Notification.objects.filter(user=test_user).order_by('-created_at')[:4]
    print(f"\nRecent notifications for {test_user.email}:")
    for notif in recent:
        print(f"  - {notif.title} | {notif.notification_type} | {notif.created_at.strftime('%H:%M:%S')}")

if __name__ == '__main__':
    test_admin_notifications()