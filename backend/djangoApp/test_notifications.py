#!/usr/bin/env python
"""
알림 시스템 테스트 스크립트
"""

import os
import django
import random
from datetime import datetime

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoApp.settings')
django.setup()

from accounts.models import User, Notification, PushSubscription
from accounts.utils import (
    send_vehicle_entry_notification, 
    send_parking_complete_notification, 
    send_grade_upgrade_notification
)

def get_test_user():
    """테스트용 사용자 가져오기 또는 생성"""
    try:
        # 첫 번째 사용자 가져오기
        user = User.objects.first()
        if user:
            print(f"[INFO] 테스트 사용자: {user.email} (ID: {user.id})")
            return user
        else:
            print("[ERROR] 테스트할 사용자가 없습니다.")
            return None
    except Exception as e:
        print(f"[ERROR] 사용자 조회 실패: {e}")
        return None

def test_vehicle_entry(user):
    """입차 알림 테스트"""
    print("\n=== 입차 알림 테스트 ===")
    
    entry_data = {
        'plate_number': '220로1284',
        'parking_lot': 'SSAFY 주차장',
        'entry_time': datetime.now().isoformat(),
        'test': True
    }
    
    try:
        send_vehicle_entry_notification(user, entry_data)
        print("[OK] 입차 알림 전송 성공")
        return True
    except Exception as e:
        print(f"[ERROR] 입차 알림 전송 실패: {e}")
        return False

def test_parking_complete(user):
    """주차 완료 알림 테스트"""
    print("\n=== 주차 완료 알림 테스트 ===")
    
    parking_data = {
        'plate_number': '220로1284',
        'parking_space': 'A5',
        'parking_time': datetime.now().isoformat(),
        'score': random.randint(70, 95),  # 랜덤 점수
        'test': True
    }
    
    try:
        send_parking_complete_notification(user, parking_data)
        print(f"[OK] 주차 완료 알림 전송 성공 (점수: {parking_data['score']}점)")
        return True
    except Exception as e:
        print(f"[ERROR] 주차 완료 알림 전송 실패: {e}")
        return False

def test_grade_upgrade(user):
    """등급 승급 알림 테스트"""
    print("\n=== 등급 승급 알림 테스트 ===")
    
    grade_levels = [
        ('초급자', '중급자'),
        ('중급자', '고급자'), 
        ('고급자', '전문가'),
        ('전문가', '마스터')
    ]
    
    old_grade, new_grade = random.choice(grade_levels)
    
    grade_data = {
        'old_grade': old_grade,
        'new_grade': new_grade,
        'current_score': 87,
        'upgrade_time': datetime.now().isoformat(),
        'test': True
    }
    
    try:
        send_grade_upgrade_notification(user, grade_data)
        print(f"[OK] 등급 승급 알림 전송 성공 ({old_grade} → {new_grade})")
        return True
    except Exception as e:
        print(f"[ERROR] 등급 승급 알림 전송 실패: {e}")
        return False

def check_notifications(user):
    """생성된 알림 확인"""
    print("\n=== 알림 목록 확인 ===")
    
    try:
        notifications = Notification.objects.filter(user=user).order_by('-created_at')[:10]
        
        print(f"총 {notifications.count()}개의 최신 알림:")
        for i, notif in enumerate(notifications, 1):
            status = "읽음" if notif.is_read else "안읽음"
            print(f"  {i}. [{notif.notification_type}] {notif.title}")
            print(f"     {notif.message} ({status})")
            print(f"     생성: {notif.created_at}")
            if notif.data:
                print(f"     데이터: {notif.data}")
            print()
            
    except Exception as e:
        print(f"[ERROR] 알림 조회 실패: {e}")

def check_push_subscriptions(user):
    """Push 구독 상태 확인"""
    print("\n=== Push 구독 상태 확인 ===")
    
    try:
        subscriptions = PushSubscription.objects.filter(user=user)
        print(f"사용자 {user.email}의 Push 구독: {subscriptions.count()}개")
        
        for sub in subscriptions:
            print(f"  - Endpoint: {sub.endpoint[:50]}...")
            print(f"    생성일: {sub.created_at}")
        
        # 사용자의 푸시 설정 확인
        print(f"\n푸시 알림 설정: {'ON' if user.push_enabled else 'OFF'}")
        
    except Exception as e:
        print(f"[ERROR] Push 구독 확인 실패: {e}")

def main():
    """메인 테스트 함수"""
    print("Push 알림 시스템 테스트")
    print("=" * 50)
    
    # 테스트 사용자 가져오기
    user = get_test_user()
    if not user:
        return
    
    # Push 구독 상태 확인
    check_push_subscriptions(user)
    
    # 기존 알림 확인
    print("\n=== 테스트 전 알림 상태 ===")
    initial_count = Notification.objects.filter(user=user).count()
    print(f"현재 알림 개수: {initial_count}개")
    
    # 알림 테스트 실행
    results = []
    results.append(test_vehicle_entry(user))
    results.append(test_parking_complete(user))
    results.append(test_grade_upgrade(user))
    
    # 테스트 후 알림 확인
    print("\n=== 테스트 후 알림 상태 ===")
    final_count = Notification.objects.filter(user=user).count()
    new_notifications = final_count - initial_count
    print(f"새로 생성된 알림: {new_notifications}개")
    
    # 최신 알림 확인
    check_notifications(user)
    
    # 결과 요약
    print("\n=== 테스트 결과 요약 ===")
    success_count = sum(results)
    total_tests = len(results)
    print(f"성공: {success_count}/{total_tests}")
    print(f"새로 생성된 알림: {new_notifications}개")
    
    if success_count == total_tests and new_notifications > 0:
        print("\n[SUCCESS] 모든 테스트 성공! 알림 시스템이 정상 작동합니다.")
        print("\n[NEXT STEPS] 다음 단계:")
        print("1. 브라우저에서 앱에 로그인")
        print("2. 푸시 알림 권한 허용")
        print("3. 헤더에서 푸시 알림 ON 설정")
        print("4. 알림함 확인")
    else:
        print(f"\n[ERROR] 일부 테스트 실패 ({success_count}/{total_tests})")

if __name__ == "__main__":
    main()