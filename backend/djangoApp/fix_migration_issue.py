#!/usr/bin/env python
"""
마이그레이션 문제 해결 및 테이블 강제 생성 스크립트
"""

import os
import django
import sys

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoApp.settings')
django.setup()

from django.core.management import call_command
from django.db import connection
from django.conf import settings

def check_migration_status():
    """마이그레이션 상태 확인"""
    print("=== 마이그레이션 상태 확인 ===")
    
    try:
        call_command('showmigrations', 'accounts', verbosity=2)
        print("\n✅ 마이그레이션 상태 확인 완료")
    except Exception as e:
        print(f"❌ 마이그레이션 상태 확인 실패: {e}")
        return False
    return True

def check_database_tables():
    """DB 테이블 존재 여부 확인"""
    print("\n=== 데이터베이스 테이블 확인 ===")
    
    with connection.cursor() as cursor:
        try:
            # MySQL/MariaDB인 경우
            if 'mysql' in settings.DATABASES['default']['ENGINE']:
                cursor.execute("SHOW TABLES;")
            # SQLite인 경우  
            elif 'sqlite' in settings.DATABASES['default']['ENGINE']:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            # PostgreSQL인 경우
            elif 'postgresql' in settings.DATABASES['default']['ENGINE']:
                cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname='public';")
            else:
                print("❌ 지원되지 않는 DB 엔진")
                return False
                
            tables = cursor.fetchall()
            table_names = [table[0] for table in tables]
            
            print(f"현재 DB 테이블 목록 ({len(table_names)}개):")
            for table in sorted(table_names):
                if 'notification' in table.lower():
                    print(f"  ✅ {table}")
                else:
                    print(f"  - {table}")
            
            # 알림 관련 테이블 확인
            notification_tables = [t for t in table_names if 'notification' in t.lower()]
            if notification_tables:
                print(f"\n✅ 알림 관련 테이블 발견: {notification_tables}")
                return True
            else:
                print("\n❌ 알림 관련 테이블이 없습니다!")
                return False
                
        except Exception as e:
            print(f"❌ 테이블 확인 실패: {e}")
            return False

def force_create_migration():
    """새로운 마이그레이션 파일 생성"""
    print("\n=== 새로운 마이그레이션 생성 ===")
    
    try:
        # makemigrations 강제 실행
        call_command('makemigrations', 'accounts', verbosity=2, interactive=False)
        print("✅ 새로운 마이그레이션 파일 생성 완료")
        return True
    except Exception as e:
        print(f"❌ 마이그레이션 파일 생성 실패: {e}")
        return False

def apply_migrations():
    """마이그레이션 적용"""
    print("\n=== 마이그레이션 적용 ===")
    
    try:
        # accounts 앱 마이그레이션만 적용
        call_command('migrate', 'accounts', verbosity=2, interactive=False)
        print("✅ accounts 앱 마이그레이션 적용 완료")
        
        # 전체 마이그레이션 적용
        call_command('migrate', verbosity=2, interactive=False)
        print("✅ 전체 마이그레이션 적용 완료")
        return True
    except Exception as e:
        print(f"❌ 마이그레이션 적용 실패: {e}")
        return False

def create_sql_manually():
    """SQL 직접 실행으로 테이블 생성"""
    print("\n=== 수동 테이블 생성 ===")
    
    # accounts_notification 테이블 생성 SQL
    create_notification_sql = """
    CREATE TABLE IF NOT EXISTS accounts_notification (
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
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    # accounts_push_subscription 테이블 생성 SQL  
    create_push_sql = """
    CREATE TABLE IF NOT EXISTS accounts_push_subscription (
        id BIGINT AUTO_INCREMENT PRIMARY KEY,
        endpoint VARCHAR(500) NOT NULL,
        p256dh VARCHAR(255) NOT NULL,
        auth VARCHAR(255) NOT NULL,
        created_at DATETIME(6) NOT NULL,
        user_id BIGINT NOT NULL,
        INDEX idx_user_id (user_id),
        INDEX idx_endpoint (endpoint(255)),
        FOREIGN KEY (user_id) REFERENCES accounts_user(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    with connection.cursor() as cursor:
        try:
            print("1. accounts_notification 테이블 생성 중...")
            cursor.execute(create_notification_sql)
            print("✅ accounts_notification 테이블 생성 완료")
            
            print("2. accounts_push_subscription 테이블 생성 중...")
            cursor.execute(create_push_sql)
            print("✅ accounts_push_subscription 테이블 생성 완료")
            
            return True
        except Exception as e:
            print(f"❌ 수동 테이블 생성 실패: {e}")
            return False

def verify_tables():
    """테이블 생성 확인"""
    print("\n=== 테이블 생성 확인 ===")
    
    with connection.cursor() as cursor:
        try:
            # accounts_notification 테이블 확인
            cursor.execute("DESCRIBE accounts_notification;")
            columns = cursor.fetchall()
            print("✅ accounts_notification 테이블 구조:")
            for col in columns:
                print(f"  - {col[0]} ({col[1]})")
            
            # 레코드 수 확인
            cursor.execute("SELECT COUNT(*) FROM accounts_notification;")
            count = cursor.fetchone()[0]
            print(f"현재 알림 레코드 수: {count}개")
            
            # accounts_push_subscription 테이블 확인
            cursor.execute("SELECT COUNT(*) FROM accounts_push_subscription;")
            push_count = cursor.fetchone()[0]
            print(f"Push 구독 레코드 수: {push_count}개")
            
            return True
        except Exception as e:
            print(f"❌ 테이블 확인 실패: {e}")
            return False

def main():
    """메인 실행 함수"""
    print("🔧 Push 알림 테이블 생성 문제 해결 스크립트")
    print("="*50)
    
    # 1단계: 마이그레이션 상태 확인
    if not check_migration_status():
        print("❌ 마이그레이션 상태 확인 실패")
        return
    
    # 2단계: 현재 테이블 확인
    tables_exist = check_database_tables()
    
    if not tables_exist:
        print("\n🛠️ 테이블이 없으므로 생성 작업을 시작합니다...")
        
        # 3단계: 새 마이그레이션 생성 시도
        if force_create_migration():
            # 4단계: 마이그레이션 적용 시도
            if apply_migrations():
                tables_exist = check_database_tables()
        
        # 5단계: 마이그레이션이 실패하면 수동 생성
        if not tables_exist:
            print("\n⚠️ 마이그레이션이 실패했습니다. 수동으로 테이블을 생성합니다...")
            if create_sql_manually():
                tables_exist = True
    
    # 6단계: 최종 확인
    if tables_exist:
        verify_tables()
        print("\n🎉 Push 알림 테이블 생성 완료!")
        print("\n다음 단계:")
        print("1. 알림 테스트 API 호출")
        print("2. 브라우저에서 알림 권한 허용")
        print("3. 헤더에서 푸시 알림 ON 설정")
    else:
        print("\n❌ 테이블 생성에 실패했습니다.")
        print("수동으로 DB 관리자 도구에서 테이블을 생성해주세요.")

if __name__ == "__main__":
    main()