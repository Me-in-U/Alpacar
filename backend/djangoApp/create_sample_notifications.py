#!/usr/bin/env python
"""
Sample notification creation script for testing
Run this after applying migrations to create sample notifications
"""

import os
import django
from datetime import datetime, timedelta
import json

# Django settings setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoApp.settings')
django.setup()

from accounts.models import User, Notification
from accounts.utils import create_notification

def create_sample_notifications():
    """Create sample notifications for testing"""
    
    # Get the first user (or create one if none exists)
    try:
        user = User.objects.filter(is_superuser=False).first()
        if not user:
            print("No regular users found. Creating sample notifications for admin users...")
            user = User.objects.filter(is_superuser=True).first()
        
        if not user:
            print("No users found in the database. Please create a user first.")
            return
            
        print(f"Creating sample notifications for user: {user.email}")
        
        # 1. 주차 완료 알림
        parking_data = {
            'parking_time': '2025-01-08T16:00:00Z',
            'parking_space': 'A4',
            'duration': '2시간 30분',
            'cost': '3000원'
        }
        notification1 = create_notification(
            user=user,
            title="주차 완료 알림",
            message="주차가 완료되었습니다.",
            notification_type='parking_complete',
            data=parking_data
        )
        print(f"Created parking notification: {notification1.id}")
        
        # 2. 등급 승급 알림
        grade_data = {
            'old_grade': '초급자',
            'new_grade': '중급자',
            'score_increase': 50,
            'achievement_date': '2025-01-07T14:30:00Z'
        }
        notification2 = create_notification(
            user=user,
            title="등급 승급 알림",
            message="주차 등급이 초급자에서 중급자로 승급되었습니다.",
            notification_type='grade_upgrade',
            data=grade_data
        )
        print(f"Created grade upgrade notification: {notification2.id}")
        
        # 3. 시스템 알림
        notification3 = create_notification(
            user=user,
            title="시스템 업데이트 안내",
            message="새로운 기능이 추가되었습니다. 앱을 업데이트해주세요.",
            notification_type='system',
            data={'version': '2.1.0', 'features': ['실시간 주차 현황', '음성 안내']}
        )
        print(f"Created system notification: {notification3.id}")
        
        # 4. 이전 주차 완료 알림 (시간 차이를 두기 위해)
        old_parking_data = {
            'parking_time': '2025-01-07T09:15:00Z',
            'parking_space': 'B2',
            'duration': '1시간 45분',
            'cost': '2500원'
        }
        notification4 = create_notification(
            user=user,
            title="주차 완료 알림",
            message="주차가 완료되었습니다.",
            notification_type='parking_complete',
            data=old_parking_data
        )
        # 이 알림을 읽음 처리
        notification4.is_read = True
        notification4.save()
        print(f"Created old parking notification (read): {notification4.id}")
        
        # 5. 점검 안내 알림
        maintenance_data = {
            'start_time': '2025-01-09T02:00:00Z',
            'end_time': '2025-01-09T06:00:00Z',
            'services_affected': ['푸시 알림', '실시간 현황']
        }
        notification5 = create_notification(
            user=user,
            title="시스템 점검 안내",
            message="1월 9일 오전 2시부터 6시까지 시스템 점검이 예정되어 있습니다.",
            notification_type='maintenance',
            data=maintenance_data
        )
        print(f"Created maintenance notification: {notification5.id}")
        
        print(f"\nSuccessfully created 5 sample notifications for {user.email}")
        print("Notifications created:")
        for notification in Notification.objects.filter(user=user).order_by('-created_at'):
            status = "읽음" if notification.is_read else "안읽음"
            print(f"  - {notification.title} ({status}) - {notification.created_at.strftime('%Y-%m-%d %H:%M')}")
            
    except Exception as e:
        print(f"Error creating sample notifications: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_sample_notifications()