#!/usr/bin/env python
"""
DB 테이블 확인 스크립트
"""

import os
import django

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoApp.settings')
django.setup()

from django.db import connection
from accounts.models import Notification, PushSubscription

def check_tables():
    """DB 테이블 확인"""
    print("=== 데이터베이스 테이블 확인 ===")
    
    with connection.cursor() as cursor:
        try:
            # 모든 테이블 목록 가져오기
            cursor.execute("SHOW TABLES;")
            tables = cursor.fetchall()
            table_names = [table[0] for table in tables]
            
            print(f"총 {len(table_names)}개의 테이블이 있습니다:")
            for table in sorted(table_names):
                if 'notification' in table.lower() or 'push' in table.lower():
                    print(f"  [OK] {table}")
                else:
                    print(f"  - {table}")
            
            # 알림 관련 테이블 확인
            notification_tables = [t for t in table_names if 'notification' in t.lower()]
            push_tables = [t for t in table_names if 'push' in t.lower()]
            
            if notification_tables:
                print(f"\n[OK] 알림 테이블: {notification_tables}")
                
                # accounts_notification 테이블 구조 확인
                if 'accounts_notification' in table_names:
                    cursor.execute("DESCRIBE accounts_notification;")
                    columns = cursor.fetchall()
                    print("\n[INFO] accounts_notification 테이블 구조:")
                    for col in columns:
                        print(f"  - {col[0]} ({col[1]})")
                        
                    # 레코드 수 확인
                    cursor.execute("SELECT COUNT(*) FROM accounts_notification;")
                    count = cursor.fetchone()[0]
                    print(f"\n[INFO] 현재 알림 레코드 수: {count}개")
            else:
                print("\n[ERROR] 알림 테이블이 없습니다!")
            
            if push_tables:
                print(f"\n[OK] Push 구독 테이블: {push_tables}")
                
                # accounts_push_subscription 테이블 구조 확인
                if 'accounts_push_subscription' in table_names:
                    cursor.execute("SELECT COUNT(*) FROM accounts_push_subscription;")
                    push_count = cursor.fetchone()[0]
                    print(f"[INFO] Push 구독 레코드 수: {push_count}개")
            else:
                print("\n[ERROR] Push 구독 테이블이 없습니다!")
                
        except Exception as e:
            print(f"[ERROR] 테이블 확인 실패: {e}")
            return False

def check_models():
    """Django 모델 확인"""
    print("\n=== Django 모델 확인 ===")
    
    try:
        # Notification 모델 확인
        print("[OK] Notification 모델 로드됨")
        print(f"  - 테이블명: {Notification._meta.db_table}")
        
        # PushSubscription 모델 확인
        print("[OK] PushSubscription 모델 로드됨")
        print(f"  - 테이블명: {PushSubscription._meta.db_table}")
        
        # 실제 DB 쿼리 테스트
        try:
            notification_count = Notification.objects.count()
            print(f"[INFO] Notification 레코드 수: {notification_count}개")
        except Exception as e:
            print(f"[ERROR] Notification 쿼리 실패: {e}")
            
        try:
            push_count = PushSubscription.objects.count()
            print(f"[INFO] PushSubscription 레코드 수: {push_count}개")
        except Exception as e:
            print(f"[ERROR] PushSubscription 쿼리 실패: {e}")
            
    except Exception as e:
        print(f"[ERROR] 모델 확인 실패: {e}")

if __name__ == "__main__":
    check_tables()
    check_models()