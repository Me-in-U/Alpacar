#!/usr/bin/env python
"""
마이그레이션 상태 확인 및 적용 스크립트
"""

import os
import django
from django.core.management import execute_from_command_line

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoApp.settings')
django.setup()

from django.core.management import call_command
from django.db import connection

def check_and_apply_migrations():
    """마이그레이션 상태 확인 및 적용"""
    
    print("=== 마이그레이션 상태 확인 ===")
    
    # 1. 현재 테이블 목록 확인
    with connection.cursor() as cursor:
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        
        print(f"현재 DB 테이블 목록: {table_names}")
        
        # Notification 테이블 존재 확인
        if 'accounts_notification' in table_names:
            print("✅ accounts_notification 테이블이 이미 존재합니다.")
            
            # 테이블 구조 확인
            cursor.execute("DESCRIBE accounts_notification;")
            columns = cursor.fetchall()
            print("테이블 구조:")
            for col in columns:
                print(f"  - {col[0]} ({col[1]})")
                
        else:
            print("❌ accounts_notification 테이블이 존재하지 않습니다.")
    
    # 2. 마이그레이션 상태 확인
    print("\n=== 마이그레이션 상태 ===")
    call_command('showmigrations', 'accounts')
    
    # 3. 마이그레이션 적용
    print("\n=== 마이그레이션 적용 ===")
    try:
        call_command('migrate', 'accounts')
        print("✅ 마이그레이션 적용 완료")
    except Exception as e:
        print(f"❌ 마이그레이션 적용 실패: {e}")
    
    # 4. 적용 후 테이블 재확인
    print("\n=== 적용 후 테이블 확인 ===")
    with connection.cursor() as cursor:
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        
        if 'accounts_notification' in table_names:
            print("✅ accounts_notification 테이블 확인됨")
            
            # 레코드 수 확인
            cursor.execute("SELECT COUNT(*) FROM accounts_notification;")
            count = cursor.fetchone()[0]
            print(f"현재 알림 레코드 수: {count}개")
            
        else:
            print("❌ accounts_notification 테이블이 여전히 없습니다.")

if __name__ == "__main__":
    check_and_apply_migrations()