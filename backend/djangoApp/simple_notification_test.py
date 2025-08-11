#!/usr/bin/env python
"""
간단한 푸시 알림 테스트 도구
- 기본적인 알림 테스트 기능만 포함
- 불필요한 복잡성 제거
"""

import os
import sys
import django

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoApp.settings')
django.setup()

from accounts.models import User
from accounts.utils import create_notification

def test_notifications():
    """간단한 알림 테스트"""
    print("[TEST] 푸시 알림 테스트 시작...")
    
    # 첫 번째 사용자 가져오기
    user = User.objects.first()
    if not user:
        print("[ERROR] 사용자가 없습니다.")
        return
    
    print(f"[OK] 사용자: {user.email}")
    
    # 테스트 알림 생성
    try:
        notification = create_notification(
            user=user,
            title="테스트 알림",
            message="간단한 테스트 알림입니다.",
            notification_type='system',
            data={'test': True, 'simple': True}
        )
        print(f"[OK] 알림 생성 성공 (ID: {notification.id})")
        
    except Exception as e:
        print(f"[ERROR] 알림 생성 실패: {e}")

if __name__ == "__main__":
    test_notifications()