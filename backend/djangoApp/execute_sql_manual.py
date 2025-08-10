#!/usr/bin/env python
"""
MySQL에 직접 SQL 실행하는 스크립트
"""

import os
import django
import pymysql
from django.conf import settings

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoApp.settings')
django.setup()

def execute_sql_file():
    """SQL 파일을 직접 실행"""
    
    # Django 설정에서 DB 정보 가져오기
    db_config = settings.DATABASES['default']
    
    print("=== MySQL 직접 연결 및 테이블 생성 ===")
    print(f"HOST: {db_config['HOST']}")
    print(f"PORT: {db_config['PORT']}")
    print(f"DATABASE: {db_config['NAME']}")
    print(f"USER: {db_config['USER']}")
    
    try:
        # PyMySQL 연결
        connection = pymysql.connect(
            host=db_config['HOST'],
            port=int(db_config['PORT']),
            user=db_config['USER'],
            password=db_config['PASSWORD'],
            database=db_config['NAME'],
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        print("\n[OK] MySQL 연결 성공")
        
        # SQL 스크립트들을 개별적으로 실행
        sql_statements = [
            # 1. accounts_notification 테이블 생성
            """
            DROP TABLE IF EXISTS accounts_notification
            """,
            """
            CREATE TABLE accounts_notification (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(100) NOT NULL COMMENT '알림 제목',
                message TEXT NOT NULL COMMENT '알림 내용',
                notification_type VARCHAR(20) NOT NULL DEFAULT 'system' COMMENT '알림 타입',
                data JSON COMMENT '추가 데이터 (JSON 형태)',
                is_read BOOLEAN NOT NULL DEFAULT FALSE COMMENT '읽음 여부',
                created_at DATETIME(6) NOT NULL COMMENT '생성 시간',
                user_id BIGINT NOT NULL COMMENT '사용자 ID (외래키)',
                
                INDEX idx_user_id (user_id),
                INDEX idx_created_at (created_at),
                INDEX idx_is_read (is_read),
                INDEX idx_notification_type (notification_type),
                INDEX idx_user_read (user_id, is_read),
                
                FOREIGN KEY (user_id) REFERENCES accounts_user(id) ON DELETE CASCADE
                
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='사용자 알림 테이블'
            """,
            
            # 2. accounts_push_subscription 테이블 생성
            """
            DROP TABLE IF EXISTS accounts_push_subscription
            """,
            """
            CREATE TABLE accounts_push_subscription (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                endpoint VARCHAR(500) NOT NULL COMMENT 'Push 구독 엔드포인트',
                p256dh VARCHAR(255) NOT NULL COMMENT 'P256DH 키',
                auth VARCHAR(255) NOT NULL COMMENT 'Auth 키',
                created_at DATETIME(6) NOT NULL COMMENT '구독 생성 시간',
                user_id BIGINT NOT NULL COMMENT '사용자 ID (외래키)',
                
                INDEX idx_user_id (user_id),
                INDEX idx_endpoint (endpoint(255)),
                INDEX idx_created_at (created_at),
                
                UNIQUE KEY uk_user_endpoint (user_id, endpoint(255)),
                
                FOREIGN KEY (user_id) REFERENCES accounts_user(id) ON DELETE CASCADE
                
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Push 알림 구독 정보'
            """
        ]
        
        # SQL 문 실행
        for i, sql in enumerate(sql_statements, 1):
            try:
                cursor.execute(sql)
                connection.commit()
                print(f"[OK] SQL {i} 실행 완료")
            except Exception as e:
                print(f"[ERROR] SQL {i} 실행 실패: {e}")
                print(f"SQL: {sql[:100]}...")
        
        # 생성된 테이블 확인
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
        
        # 테이블 구조 확인
        if notification_found:
            print("\n=== accounts_notification 테이블 구조 ===")
            cursor.execute("DESCRIBE accounts_notification")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  - {col[0]} ({col[1]})")
        
        if push_found:
            print("\n=== accounts_push_subscription 테이블 구조 ===")
            cursor.execute("DESCRIBE accounts_push_subscription")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  - {col[0]} ({col[1]})")
        
        # 레코드 수 확인
        if notification_found and push_found:
            cursor.execute("SELECT COUNT(*) FROM accounts_notification")
            notif_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM accounts_push_subscription")
            push_count = cursor.fetchone()[0]
            
            print(f"\n[INFO] accounts_notification: {notif_count}개")
            print(f"[INFO] accounts_push_subscription: {push_count}개")
        
        cursor.close()
        connection.close()
        
        if notification_found and push_found:
            print("\n[SUCCESS] 모든 테이블이 성공적으로 생성되었습니다!")
            return True
        else:
            print("\n[ERROR] 일부 테이블 생성에 실패했습니다.")
            return False
            
    except Exception as e:
        print(f"\n[ERROR] MySQL 연결 또는 실행 실패: {e}")
        return False

def test_django_models():
    """Django 모델로 테이블 접근 테스트"""
    print("\n=== Django 모델 테스트 ===")
    
    try:
        from accounts.models import Notification, PushSubscription
        
        # 모델 쿼리 테스트
        notif_count = Notification.objects.count()
        push_count = PushSubscription.objects.count()
        
        print(f"[OK] Notification 모델: {notif_count}개 레코드")
        print(f"[OK] PushSubscription 모델: {push_count}개 레코드")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Django 모델 테스트 실패: {e}")
        return False

if __name__ == "__main__":
    print("MySQL 직접 테이블 생성 스크립트")
    print("=" * 50)
    
    # SQL 직접 실행
    sql_success = execute_sql_file()
    
    if sql_success:
        # Django 모델 테스트
        django_success = test_django_models()
        
        if django_success:
            print("\n[FINAL] 테이블 생성 및 Django 연동 완료!")
            print("\n다음 단계:")
            print("1. Django 서버 재시작")
            print("2. 알림 API 테스트 실행")
            print("3. 브라우저에서 푸시 알림 테스트")
        else:
            print("\n[WARNING] 테이블은 생성되었지만 Django 모델 연동에 문제가 있습니다.")
    else:
        print("\n[FAIL] 테이블 생성에 실패했습니다.")