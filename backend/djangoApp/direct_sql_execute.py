#!/usr/bin/env python
"""
Django DB 연결을 통한 직접 SQL 실행
"""

import os
import django

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoApp.settings')
django.setup()

from django.db import connection

def execute_direct_sql():
    """Django 연결을 통해 직접 SQL 실행"""
    
    print("Django DB 연결을 통한 테이블 생성")
    print("=" * 50)
    
    with connection.cursor() as cursor:
        try:
            # 1. accounts_notification 테이블 삭제 후 생성
            print("1. accounts_notification 테이블 생성 중...")
            
            cursor.execute("DROP TABLE IF EXISTS accounts_notification")
            
            create_notification_sql = """
            CREATE TABLE accounts_notification (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(100) NOT NULL,
                message TEXT NOT NULL,
                notification_type VARCHAR(20) NOT NULL DEFAULT 'system',
                data JSON,
                is_read BOOLEAN NOT NULL DEFAULT FALSE,
                created_at DATETIME(6) NOT NULL,
                user_id BIGINT NOT NULL,
                
                INDEX idx_user_id (user_id),
                INDEX idx_created_at (created_at),
                INDEX idx_is_read (is_read),
                INDEX idx_notification_type (notification_type),
                
                FOREIGN KEY (user_id) REFERENCES accounts_user(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            
            cursor.execute(create_notification_sql)
            print("[OK] accounts_notification 테이블 생성 완료")
            
            # 2. accounts_push_subscription 테이블 삭제 후 생성
            print("2. accounts_push_subscription 테이블 생성 중...")
            
            cursor.execute("DROP TABLE IF EXISTS accounts_push_subscription")
            
            create_push_sql = """
            CREATE TABLE accounts_push_subscription (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                endpoint VARCHAR(500) NOT NULL,
                p256dh VARCHAR(255) NOT NULL,
                auth VARCHAR(255) NOT NULL,
                created_at DATETIME(6) NOT NULL,
                user_id BIGINT NOT NULL,
                
                INDEX idx_user_id (user_id),
                INDEX idx_endpoint (endpoint(255)),
                
                FOREIGN KEY (user_id) REFERENCES accounts_user(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            
            cursor.execute(create_push_sql)
            print("[OK] accounts_push_subscription 테이블 생성 완료")
            
            # 3. 생성된 테이블 확인
            print("\n=== 테이블 생성 확인 ===")
            cursor.execute("SHOW TABLES LIKE 'accounts_%'")
            tables = cursor.fetchall()
            
            notification_found = False
            push_found = False
            
            for table in tables:
                table_name = table[0]
                print(f"  - {table_name}")
                if 'notification' in table_name:
                    notification_found = True
                if 'push' in table_name:
                    push_found = True
            
            # 4. 테이블 구조 확인
            if notification_found:
                print("\n=== accounts_notification 구조 ===")
                cursor.execute("DESCRIBE accounts_notification")
                columns = cursor.fetchall()
                for col in columns:
                    print(f"  - {col[0]} ({col[1]})")
            
            if push_found:
                print("\n=== accounts_push_subscription 구조 ===")
                cursor.execute("DESCRIBE accounts_push_subscription")
                columns = cursor.fetchall()
                for col in columns:
                    print(f"  - {col[0]} ({col[1]})")
            
            # 5. 레코드 수 확인
            if notification_found:
                cursor.execute("SELECT COUNT(*) FROM accounts_notification")
                notif_count = cursor.fetchone()[0]
                print(f"\n[INFO] accounts_notification: {notif_count}개 레코드")
            
            if push_found:
                cursor.execute("SELECT COUNT(*) FROM accounts_push_subscription")
                push_count = cursor.fetchone()[0]
                print(f"[INFO] accounts_push_subscription: {push_count}개 레코드")
            
            if notification_found and push_found:
                print("\n[SUCCESS] 모든 테이블이 성공적으로 생성되었습니다!")
                return True
            else:
                print("\n[ERROR] 테이블 생성에 실패했습니다.")
                return False
                
        except Exception as e:
            print(f"\n[ERROR] SQL 실행 실패: {e}")
            return False

def test_django_models():
    """Django 모델 테스트"""
    print("\n=== Django 모델 연동 테스트 ===")
    
    try:
        from accounts.models import Notification, PushSubscription
        
        # 모델 쿼리 테스트
        notif_count = Notification.objects.count()
        push_count = PushSubscription.objects.count()
        
        print(f"[OK] Notification 모델: {notif_count}개 레코드")
        print(f"[OK] PushSubscription 모델: {push_count}개 레코드")
        
        # 테스트 알림 생성 (선택사항)
        from accounts.models import User
        user = User.objects.first()
        
        if user:
            test_notification = Notification.objects.create(
                user=user,
                title="테스트 알림",
                message="테이블 생성 테스트입니다.",
                notification_type="system"
            )
            print(f"[OK] 테스트 알림 생성됨 (ID: {test_notification.id})")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Django 모델 테스트 실패: {e}")
        return False

if __name__ == "__main__":
    # 1. 직접 SQL로 테이블 생성
    sql_success = execute_direct_sql()
    
    # 2. Django 모델 테스트
    if sql_success:
        django_success = test_django_models()
        
        if django_success:
            print("\n[FINAL SUCCESS] 테이블 생성 및 Django 연동 완료!")
            print("\n다음 단계:")
            print("1. 알림 테스트 실행: python test_notifications.py")
            print("2. Django 서버 재시작")
            print("3. 브라우저에서 푸시 알림 테스트")
        else:
            print("\n[WARNING] 테이블은 생성되었지만 Django 모델 연동 실패")
    else:
        print("\n[FAIL] 테이블 생성 실패")