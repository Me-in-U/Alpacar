#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
푸시 알림 테스트 도구

Django 프로젝트에서 푸시 알림 시스템을 테스트하기 위한 종합적인 도구입니다.
- 다양한 알림 타입 테스트
- 배치 알림 전송
- 시나리오 시뮬레이션
- 상태 모니터링

사용 방법:
    python notification_tester.py
    python notification_tester.py --scenario parking_flow
    python notification_tester.py --custom "테스트 제목" "테스트 메시지"
    python notification_tester.py --status
"""

import os
import sys
import django

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)
import requests
import json
import argparse
import time
from datetime import datetime

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoApp.settings')
django.setup()

from accounts.models import User, Notification, PushSubscription
from accounts.utils import create_notification

# API 베이스 URL (로컬 개발 환경 기준)
BASE_URL = "http://localhost:8000/api"

class NotificationTester:
    """푸시 알림 테스트 클래스"""
    
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.user = None
        
    def login(self, email=None, password=None):
        """API 로그인"""
        if not email:
            # 첫 번째 사용자 자동 선택
            try:
                self.user = User.objects.first()
                if not self.user:
                    print("❌ 사용자가 없습니다. 먼저 사용자를 생성하세요.")
                    return False
                print(f"✅ 사용자 자동 선택: {self.user.email}")
                return True
            except Exception as e:
                print(f"❌ 사용자 조회 실패: {e}")
                return False
        
        # API 로그인 (토큰 방식 사용 시)
        login_data = {
            "email": email,
            "password": password
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/login/", json=login_data)
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token')
                if self.token:
                    self.session.headers.update({
                        'Authorization': f'Bearer {self.token}'
                    })
                    print(f"✅ 로그인 성공: {email}")
                    return True
            
            print(f"❌ 로그인 실패: {response.status_code}")
            print(response.text)
            return False
            
        except Exception as e:
            print(f"❌ 로그인 요청 실패: {e}")
            return False
    
    def test_basic_notifications(self):
        """기본 알림 타입 테스트"""
        print("\n🔔 기본 알림 타입 테스트 시작...")
        
        tests = [
            ("system", "시스템 테스트", "🔧 시스템 테스트 알림"),
            ("vehicle_entry", "입차 테스트", "🚗 테스트용 입차 알림"),
            ("parking_complete", "주차완료 테스트", "🅿️ 테스트용 주차 완료 알림"),
            ("grade_upgrade", "등급승급 테스트", "🎉 테스트용 등급 승급 알림")
        ]
        
        results = []
        for ntype, title, message in tests:
            try:
                notification = create_notification(
                    user=self.user,
                    title=title,
                    message=message,
                    notification_type=ntype,
                    data={"test": True, "tester": True}
                )
                results.append({"type": ntype, "status": "✅", "id": notification.id})
                print(f"  ✅ {ntype}: 알림 생성됨 (ID: {notification.id})")
                time.sleep(1)
                
            except Exception as e:
                results.append({"type": ntype, "status": "❌", "error": str(e)})
                print(f"  ❌ {ntype}: 실패 - {e}")
        
        print(f"\n📊 결과: {len([r for r in results if r['status'] == '✅'])}/{len(tests)} 성공")
        return results
    
    def test_custom_notification(self, title, message, ntype="system"):
        """사용자 정의 알림 테스트"""
        print(f"\n✨ 사용자 정의 알림 테스트: {title}")
        
        try:
            notification = create_notification(
                user=self.user,
                title=title,
                message=message,
                notification_type=ntype,
                data={
                    "test": True,
                    "custom": True,
                    "tester": True,
                    "timestamp": datetime.now().isoformat()
                }
            )
            print(f"✅ 알림 생성 성공 (ID: {notification.id})")
            print(f"   제목: {notification.title}")
            print(f"   내용: {notification.message}")
            print(f"   타입: {notification.notification_type}")
            return notification
            
        except Exception as e:
            print(f"❌ 알림 생성 실패: {e}")
            return None
    
    def test_batch_notifications(self, count=5, delay=2):
        """배치 알림 테스트"""
        print(f"\n📦 배치 알림 테스트 ({count}개, {delay}초 간격)...")
        
        notifications = []
        for i in range(count):
            try:
                notification = create_notification(
                    user=self.user,
                    title=f"🔔 배치 알림 #{i+1}",
                    message=f"이것은 {i+1}번째 배치 테스트 알림입니다.",
                    notification_type="system",
                    data={
                        "test": True,
                        "batch": True,
                        "batch_index": i,
                        "batch_total": count
                    }
                )
                notifications.append(notification)
                print(f"  ✅ #{i+1} 생성됨 (ID: {notification.id})")
                
                if i < count - 1:
                    time.sleep(delay)
                    
            except Exception as e:
                print(f"  ❌ #{i+1} 실패: {e}")
        
        print(f"\n📊 배치 결과: {len(notifications)}/{count} 성공")
        return notifications
    
    def simulate_parking_scenario(self, delay=3):
        """주차 시나리오 시뮬레이션"""
        print(f"\n🚗 주차 플로우 시나리오 시뮬레이션 ({delay}초 간격)...")
        
        scenario_steps = [
            {
                "title": "🚗 차량 입차 감지",
                "message": "220로1284 차량이 SSAFY 주차장에 입차하였습니다.",
                "type": "vehicle_entry",
                "data": {"plate_number": "220로1284", "parking_lot": "SSAFY 주차장"}
            },
            {
                "title": "📍 추천 구역 안내",
                "message": "A5 구역을 추천합니다. 거리: 20m, 예상 소요시간: 1분",
                "type": "system",
                "data": {"recommended_space": "A5", "distance": "20m"}
            },
            {
                "title": "🅿️ 주차 완료",
                "message": "A5 구역에 주차가 완료되었습니다. 점수: 87점",
                "type": "parking_complete",
                "data": {"parking_space": "A5", "score": 87}
            }
        ]
        
        results = []
        for i, step in enumerate(scenario_steps):
            try:
                step_data = step["data"].copy()
                step_data.update({
                    "test": True,
                    "scenario": "parking_flow",
                    "step": i + 1
                })
                
                notification = create_notification(
                    user=self.user,
                    title=step["title"],
                    message=step["message"],
                    notification_type=step["type"],
                    data=step_data
                )
                
                results.append({"step": i+1, "status": "✅", "id": notification.id})
                print(f"  ✅ 단계 {i+1}: {step['title']}")
                
                if i < len(scenario_steps) - 1:
                    time.sleep(delay)
                    
            except Exception as e:
                results.append({"step": i+1, "status": "❌", "error": str(e)})
                print(f"  ❌ 단계 {i+1}: 실패 - {e}")
        
        print(f"\n📊 시나리오 결과: {len([r for r in results if r['status'] == '✅'])}/{len(scenario_steps)} 성공")
        return results
    
    def get_status(self):
        """테스트 상태 조회"""
        print("\n📊 푸시 알림 테스트 상태...")
        
        if not self.user:
            print("❌ 사용자 정보가 없습니다.")
            return
        
        # 사용자 정보
        print(f"\n👤 사용자 정보:")
        print(f"   이메일: {self.user.email}")
        print(f"   닉네임: {self.user.nickname}")
        print(f"   푸시 설정: {'✅ ON' if self.user.push_enabled else '❌ OFF'}")
        print(f"   점수: {self.user.score}점")
        
        # 푸시 구독 현황
        subscriptions = PushSubscription.objects.filter(user=self.user)
        print(f"\n📱 푸시 구독:")
        print(f"   구독 수: {subscriptions.count()}개")
        for i, sub in enumerate(subscriptions[:3]):
            print(f"   #{i+1}: {sub.endpoint[:50]}...")
        
        # 알림 통계
        total_notifications = Notification.objects.filter(user=self.user).count()
        test_notifications = Notification.objects.filter(
            user=self.user, 
            data__test=True
        ).count()
        unread_count = Notification.objects.filter(
            user=self.user, 
            is_read=False
        ).count()
        
        print(f"\n📬 알림 통계:")
        print(f"   전체 알림: {total_notifications}개")
        print(f"   테스트 알림: {test_notifications}개")
        print(f"   읽지 않은 알림: {unread_count}개")
        
        # 최근 알림
        recent_notifications = Notification.objects.filter(
            user=self.user
        ).order_by('-created_at')[:5]
        
        print(f"\n📋 최근 알림 (최대 5개):")
        for notif in recent_notifications:
            status_icon = "📖" if notif.is_read else "🆕"
            test_icon = "🧪" if notif.data.get('test') else ""
            print(f"   {status_icon}{test_icon} {notif.title} ({notif.notification_type})")
            print(f"        {notif.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    
    def clear_test_notifications(self):
        """테스트 알림 삭제"""
        print("\n🧹 테스트 알림 삭제 중...")
        
        deleted_count = Notification.objects.filter(
            user=self.user,
            data__test=True
        ).delete()[0]
        
        print(f"✅ {deleted_count}개의 테스트 알림이 삭제되었습니다.")
        return deleted_count


def main():
    parser = argparse.ArgumentParser(description="푸시 알림 테스트 도구")
    parser.add_argument("--basic", action="store_true", help="기본 알림 타입 테스트")
    parser.add_argument("--custom", nargs=2, metavar=("TITLE", "MESSAGE"), help="사용자 정의 알림 테스트")
    parser.add_argument("--batch", type=int, default=5, metavar="COUNT", help="배치 알림 테스트 (개수)")
    parser.add_argument("--scenario", choices=["parking_flow"], help="시나리오 시뮬레이션")
    parser.add_argument("--status", action="store_true", help="테스트 상태 조회")
    parser.add_argument("--clear", action="store_true", help="테스트 알림 삭제")
    parser.add_argument("--delay", type=int, default=3, help="작업 간 지연 시간(초)")
    parser.add_argument("--email", help="로그인 이메일")
    parser.add_argument("--password", help="로그인 비밀번호")
    
    args = parser.parse_args()
    
    # 테스터 초기화
    tester = NotificationTester()
    
    # 로그인
    if not tester.login(args.email, args.password):
        print("❌ 로그인 실패. 프로그램을 종료합니다.")
        sys.exit(1)
    
    # 명령 실행
    try:
        if args.status:
            tester.get_status()
        elif args.clear:
            tester.clear_test_notifications()
        elif args.basic:
            tester.test_basic_notifications()
        elif args.custom:
            tester.test_custom_notification(args.custom[0], args.custom[1])
        elif args.batch:
            tester.test_batch_notifications(args.batch, args.delay)
        elif args.scenario == "parking_flow":
            tester.simulate_parking_scenario(args.delay)
        else:
            # 기본 실행: 종합 테스트
            print("🚀 푸시 알림 종합 테스트 시작!")
            tester.get_status()
            tester.test_basic_notifications()
            time.sleep(2)
            tester.simulate_parking_scenario(args.delay)
            print("\n✅ 종합 테스트 완료!")
    
    except KeyboardInterrupt:
        print("\n\n⏹️ 테스트가 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 테스트 실행 중 오류: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()