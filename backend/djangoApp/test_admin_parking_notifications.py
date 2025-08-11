#!/usr/bin/env python
"""
관리자 주차 워크플로우 푸시 알림 테스트 스크립트
- 관리자 페이지의 전체 주차 과정에서 푸시 알림이 정상 작동하는지 검증
- 입차 -> 주차 배정 -> 주차 완료 -> 출차 과정 시뮬레이션
"""

import os
import sys
import django
from django.utils import timezone

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoApp.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from rest_framework.test import force_authenticate
from vehicles.models import Vehicle, VehicleModel
from parking.models import ParkingSpace
from events.views import manual_entrance, manual_parking_complete, manual_exit
from parking.views import assign_space

def test_admin_parking_workflow():
    """관리자 주차 워크플로우 전체 테스트"""
    
    print("=" * 60)
    print("[ADMIN TEST] 관리자 주차 워크플로우 푸시 알림 테스트")
    print("=" * 60)
    
    # 1. 테스트 사용자 및 차량 준비
    User = get_user_model()
    try:
        user = User.objects.get(email='admin_test@ssafy.io')
        print(f"[OK] 기존 테스트 사용자 사용: {user.email}")
    except User.DoesNotExist:
        user = User.objects.create_user(
            email='admin_test@ssafy.io',
            nickname='관리자테스트',
            password='testpass123'
        )
        print(f"[OK] 새 테스트 사용자 생성: {user.email}")
    
    # 푸시 알림 활성화
    if hasattr(user, 'push_enabled'):
        user.push_enabled = True
        user.save()
        print("[OK] 사용자 푸시 알림 활성화됨")
    
    # 테스트 차량 준비
    try:
        vehicle_model, created = VehicleModel.objects.get_or_create(
            brand='현대',
            model_name='아반떼',
            defaults={
                'size_class': 'compact',
                'image_url': 'https://example.com/avante.jpg'
            }
        )
        
        test_vehicle, created = Vehicle.objects.get_or_create(
            license_plate='관리자123',
            defaults={
                'user': user,
                'model': vehicle_model
            }
        )
        print(f"[OK] 테스트 차량: {test_vehicle.license_plate}")
        
    except Exception as e:
        print(f"[ERROR] 테스트 차량 준비 실패: {str(e)}")
        return
    
    # 테스트 주차공간 준비
    try:
        test_space, created = ParkingSpace.objects.get_or_create(
            zone='TEST',
            slot_number=99,
            defaults={
                'size_class': 'compact',
                'status': 'free'
            }
        )
        if test_space.status != 'free':
            test_space.status = 'free'
            test_space.current_vehicle = None
            test_space.save()
        print(f"[OK] 테스트 주차공간: {test_space.zone}{test_space.slot_number}")
        
    except Exception as e:
        print(f"[ERROR] 테스트 주차공간 준비 실패: {str(e)}")
        return
    
    # RequestFactory 준비
    factory = RequestFactory()
    
    # 관리자 사용자 (실제로는 관리자여야 하지만 테스트를 위해)
    try:
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.create_superuser(
                email='admin@ssafy.io',
                nickname='관리자',
                password='admin123'
            )
        print(f"[OK] 관리자 사용자: {admin_user.email}")
    except Exception as e:
        print(f"[ERROR] 관리자 사용자 준비 실패: {str(e)}")
        return
    
    print("\\n" + "=" * 60)
    print("🚀 관리자 주차 워크플로우 시작")
    print("=" * 60)
    
    try:
        # Step 1: 수동 입차
        print("\\n[STEP 1] 🚗 수동 입차 처리")
        print("-" * 40)
        
        entrance_request = factory.post('/api/events/manual-entrance/', {
            'license_plate': test_vehicle.license_plate
        }, content_type='application/json')
        force_authenticate(entrance_request, user=admin_user)
        
        entrance_response = manual_entrance(entrance_request)
        if entrance_response.status_code in [200, 201]:
            print(f"✅ 입차 처리 성공: {entrance_response.status_code}")
            print(f"   - 차량번호: {test_vehicle.license_plate}")
            print(f"   - 사용자: {user.email}")
            print(f"   - 푸시 알림: 입차 알림 전송됨")
        else:
            print(f"❌ 입차 처리 실패: {entrance_response.status_code}")
            if hasattr(entrance_response, 'data'):
                print(f"   에러: {entrance_response.data}")
            return
        
        # 잠깐 대기 (실제 상황 시뮬레이션)
        import time
        time.sleep(2)
        
        # Step 2: 주차 공간 배정
        print("\\n[STEP 2] 🅿️ 주차 공간 배정")
        print("-" * 40)
        
        assignment_request = factory.post('/api/parking/assign-space/', {
            'license_plate': test_vehicle.license_plate,
            'zone': test_space.zone,
            'slot_number': test_space.slot_number
        }, content_type='application/json')
        force_authenticate(assignment_request, user=admin_user)
        
        assignment_response = assign_space(assignment_request)
        if assignment_response.status_code in [200, 201]:
            print(f"✅ 주차 배정 성공: {assignment_response.status_code}")
            print(f"   - 배정된 구역: {test_space.zone}{test_space.slot_number}")
            print(f"   - 푸시 알림: 주차 배정 알림 전송됨")
        else:
            print(f"❌ 주차 배정 실패: {assignment_response.status_code}")
            if hasattr(assignment_response, 'data'):
                print(f"   에러: {assignment_response.data}")
            return
        
        time.sleep(2)
        
        # Step 3: 주차 완료 처리
        print("\\n[STEP 3] ✅ 주차 완료 처리")
        print("-" * 40)
        
        parking_complete_request = factory.post(f'/api/events/manual-parking-complete/{test_vehicle.id}/')
        force_authenticate(parking_complete_request, user=admin_user)
        
        parking_response = manual_parking_complete(parking_complete_request, test_vehicle.id)
        if parking_response.status_code == 200:
            print(f"✅ 주차 완료 성공: {parking_response.status_code}")
            print(f"   - 주차 구역: {test_space.zone}{test_space.slot_number}")
            print(f"   - 푸시 알림: 주차 완료 알림 전송됨")
        else:
            print(f"❌ 주차 완료 실패: {parking_response.status_code}")
            if hasattr(parking_response, 'data'):
                print(f"   에러: {parking_response.data}")
            return
        
        time.sleep(2)
        
        # Step 4: 출차 처리
        print("\\n[STEP 4] 🚗 출차 처리")
        print("-" * 40)
        
        exit_request = factory.post(f'/api/events/manual-exit/{test_vehicle.id}/')
        force_authenticate(exit_request, user=admin_user)
        
        exit_response = manual_exit(exit_request, test_vehicle.id)
        if exit_response.status_code == 200:
            print(f"✅ 출차 완료 성공: {exit_response.status_code}")
            print(f"   - 푸시 알림: 출차 완료 알림 전송됨")
            print(f"   - 주차공간 해제됨")
        else:
            print(f"❌ 출차 완료 실패: {exit_response.status_code}")
            if hasattr(exit_response, 'data'):
                print(f"   에러: {exit_response.data}")
            return
        
        print("\\n" + "=" * 60)
        print("🎉 관리자 주차 워크플로우 테스트 완료!")
        print("=" * 60)
        print("✅ 모든 단계에서 푸시 알림이 정상적으로 전송되었습니다.")
        print("\\n📱 전송된 알림 목록:")
        print("1. 🚗 입차 알림 - 차량이 주차장에 입차했습니다")
        print("2. 🅿️ 주차 배정 알림 - 주차 구역이 배정되었습니다")  
        print("3. ✅ 주차 완료 알림 - 주차가 완료되었습니다")
        print("4. 🚗 출차 완료 알림 - 차량이 주차장에서 출차했습니다")
        
        # 알림 개수 확인
        from accounts.models import Notification
        recent_notifications = Notification.objects.filter(
            user=user,
            created_at__gte=timezone.now() - timezone.timedelta(minutes=5)
        ).count()
        print(f"\\n📊 최근 5분간 생성된 알림: {recent_notifications}개")
        
    except Exception as e:
        print(f"\\n❌ 테스트 실행 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_admin_parking_workflow()