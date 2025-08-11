#!/usr/bin/env python
"""
관리자용 푸시 알림 발송 현황 요약 API
- 관리자가 최근 발송된 푸시 알림들을 확인할 수 있는 기능
"""

import os
import sys
import django

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoApp.settings')
django.setup()

from django.utils import timezone
from accounts.models import Notification

def get_admin_notification_summary():
    """관리자용 알림 발송 현황 요약"""
    
    print("=" * 60)
    print("[ADMIN] 푸시 알림 발송 현황 요약")
    print("=" * 60)
    
    # 최근 24시간 알림 통계
    since_24h = timezone.now() - timezone.timedelta(hours=24)
    recent_notifications = Notification.objects.filter(
        created_at__gte=since_24h
    )
    
    print(f"📊 최근 24시간 알림 통계:")
    print(f"   - 총 발송: {recent_notifications.count()}개")
    
    # 알림 타입별 통계
    notification_types = recent_notifications.values_list('notification_type', flat=True)
    type_counts = {}
    for ntype in notification_types:
        type_counts[ntype] = type_counts.get(ntype, 0) + 1
    
    print(f"\\n📱 알림 타입별 발송 현황:")
    for ntype, count in sorted(type_counts.items()):
        type_name = {
            'vehicle_entry': '🚗 입차 알림',
            'parking_assignment': '🅿️ 주차 배정',
            'parking_reassignment': '🔄 주차 재배정',
            'parking_complete': '✅ 주차 완료',
            'vehicle_exit': '🚗 출차 완료',
            'system': '🔧 시스템 알림',
        }.get(ntype, f'📱 {ntype}')
        
        print(f"   - {type_name}: {count}개")
    
    # 관리자 액션으로 발송된 알림 확인
    admin_notifications = recent_notifications.filter(
        data__admin_action=True
    ).count()
    
    print(f"\\n🔧 관리자 액션으로 발송된 알림: {admin_notifications}개")
    
    # 최근 10개 알림 상세
    print(f"\\n📋 최근 발송된 알림 (최대 10개):")
    latest_notifications = recent_notifications.order_by('-created_at')[:10]
    
    for i, notification in enumerate(latest_notifications, 1):
        created_time = notification.created_at.strftime('%m-%d %H:%M')
        admin_badge = "🔧" if notification.data.get('admin_action') else ""
        print(f"   {i:2d}. {admin_badge} {notification.title}")
        print(f"       {notification.user.email} | {created_time}")
        if notification.data.get('plate_number'):
            print(f"       차량: {notification.data.get('plate_number')}")
        print()
    
    # 사용자별 알림 수신 현황
    print(f"👥 사용자별 최근 24시간 알림 수신 현황:")
    user_counts = recent_notifications.values_list('user__email', flat=True)
    user_stats = {}
    for email in user_counts:
        user_stats[email] = user_stats.get(email, 0) + 1
    
    for email, count in sorted(user_stats.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   - {email}: {count}개")
    
    print("\\n" + "=" * 60)
    print("✅ 관리자 푸시 알림 현황 요약 완료")
    print("=" * 60)

if __name__ == '__main__':
    get_admin_notification_summary()