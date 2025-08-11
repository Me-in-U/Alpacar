#!/usr/bin/env python
"""
푸시 알림 시스템 진단 스크립트
- VAPID 키 설정 확인
- 사용자 푸시 구독 상태 확인
- 푸시 알림 전송 테스트
"""

import os
import sys
import django

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoApp.settings')
django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model
from accounts.models import PushSubscription, Notification
from accounts.utils import send_push_notification, create_notification

def diagnose_push_system():
    """푸시 알림 시스템 진단"""
    
    print("=" * 60)
    print("[DIAGNOSIS] 푸시 알림 시스템 진단")
    print("=" * 60)
    
    # 1. VAPID 키 설정 확인
    print("\n1. VAPID 키 설정 확인:")
    print("-" * 40)
    
    vapid_public = getattr(settings, 'VAPID_PUBLIC_KEY', None)
    vapid_private = getattr(settings, 'VAPID_PRIVATE_KEY', None)
    
    if vapid_public and vapid_private:
        print(f"✅ VAPID PUBLIC KEY: {vapid_public[:20]}...")
        print(f"✅ VAPID PRIVATE KEY: {vapid_private[:20]}...")
        print("✅ VAPID 키 설정됨")
    else:
        print("❌ VAPID 키 누락!")
        print(f"   PUBLIC: {bool(vapid_public)}")
        print(f"   PRIVATE: {bool(vapid_private)}")
        return
    
    # 2. 사용자 푸시 활성화 상태 확인
    print("\n2. 사용자 푸시 활성화 상태:")
    print("-" * 40)
    
    User = get_user_model()
    total_users = User.objects.count()
    push_enabled_users = User.objects.filter(push_enabled=True).count()
    
    print(f"   총 사용자: {total_users}명")
    print(f"   푸시 활성화: {push_enabled_users}명")
    
    if push_enabled_users == 0:
        print("❌ 푸시 알림을 활성화한 사용자가 없습니다!")
        print("   해결 방법: 프론트엔드에서 푸시 알림 권한 요청 필요")
        return
    
    # 3. 푸시 구독 상태 확인
    print("\n3. 푸시 구독 상태:")
    print("-" * 40)
    
    total_subscriptions = PushSubscription.objects.count()
    print(f"   총 구독: {total_subscriptions}개")
    
    if total_subscriptions == 0:
        print("❌ 푸시 구독이 없습니다!")
        print("   해결 방법: 프론트엔드에서 service worker를 통한 구독 등록 필요")
        return
    
    # 4. 사용자별 구독 현황 확인
    print("\n4. 사용자별 구독 현황:")
    print("-" * 40)
    
    for user in User.objects.filter(push_enabled=True)[:5]:
        user_subscriptions = PushSubscription.objects.filter(user=user).count()
        print(f"   {user.email}: {user_subscriptions}개 구독")
    
    # 5. 테스트 푸시 알림 전송
    print("\n5. 테스트 푸시 알림 전송:")
    print("-" * 40)
    
    test_user = User.objects.filter(push_enabled=True).first()
    if test_user:
        try:
            create_notification(
                user=test_user,
                title="🧪 푸시 알림 테스트",
                message="관리자 페이지에서 푸시 알림 테스트를 실행했습니다.",
                notification_type='system',
                data={
                    'test': True,
                    'admin_action': True,
                    'action_url': '/parking-recommend',
                    'action_type': 'navigate'
                }
            )
            print(f"✅ 테스트 알림 전송됨: {test_user.email}")
        except Exception as e:
            print(f"❌ 테스트 알림 전송 실패: {str(e)}")
    else:
        print("❌ 테스트할 사용자가 없습니다")
    
    # 6. 최근 알림 현황
    print("\n6. 최근 알림 현황:")
    print("-" * 40)
    
    recent_notifications = Notification.objects.order_by('-created_at')[:3]
    for notification in recent_notifications:
        created_time = notification.created_at.strftime('%Y-%m-%d %H:%M:%S')
        print(f"   {notification.title} | {notification.user.email} | {created_time}")
    
    print("\n" + "=" * 60)
    print("✅ 푸시 알림 시스템 진단 완료")
    print("=" * 60)
    
    # 진단 결과 요약
    print("\n📋 진단 결과 요약:")
    print(f"   VAPID 키: {'✅' if vapid_public and vapid_private else '❌'}")
    print(f"   푸시 활성화 사용자: {'✅' if push_enabled_users > 0 else '❌'} ({push_enabled_users}명)")
    print(f"   푸시 구독: {'✅' if total_subscriptions > 0 else '❌'} ({total_subscriptions}개)")
    
    if vapid_public and vapid_private and push_enabled_users > 0 and total_subscriptions > 0:
        print("\n🎉 푸시 알림 시스템이 정상적으로 설정되었습니다!")
    else:
        print("\n⚠️  푸시 알림 시스템에 문제가 있습니다. 위의 결과를 확인해 주세요.")

if __name__ == '__main__':
    diagnose_push_system()