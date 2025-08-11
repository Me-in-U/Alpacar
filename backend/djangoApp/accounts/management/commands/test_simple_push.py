from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import User, Notification
from vehicles.models import Vehicle
from accounts.notification_helpers import (
    send_vehicle_entry_notification,
    send_parking_assigned_notification,
    send_parking_complete_notification,
    send_vehicle_exit_notification
)

class Command(BaseCommand):
    help = '단순 푸시 알림 시스템 테스트'

    def handle(self, *args, **options):
        self.stdout.write("="*50)
        self.stdout.write("관리자 액션 단순 푸시 알림 시스템 테스트")
        self.stdout.write("="*50)
        
        # 1. 테스트 사용자 및 차량 생성/조회
        try:
            user = User.objects.get(email="test@example.com")
            self.stdout.write(f"✅ 기존 테스트 사용자 사용: {user.email}")
        except User.DoesNotExist:
            user = User.objects.create_user(
                email="test@example.com",
                password="testpass123",
                full_name="테스트 사용자",
                nickname="tester",
                phone="010-1234-5678",
                push_enabled=True
            )
            self.stdout.write(f"✅ 새 테스트 사용자 생성: {user.email}")
        
        try:
            vehicle = Vehicle.objects.get(license_plate="12가3456")
            self.stdout.write(f"✅ 기존 테스트 차량 사용: {vehicle.license_plate}")
        except Vehicle.DoesNotExist:
            vehicle = Vehicle.objects.create(
                user=user,
                license_plate="12가3456",
                vehicle_type="sedan",
                color="white"
            )
            self.stdout.write(f"✅ 새 테스트 차량 생성: {vehicle.license_plate}")
        
        # 2. 입차 알림 테스트
        self.stdout.write("\n🚗 입차 알림 테스트...")
        entry_data = {
            'plate_number': vehicle.license_plate,
            'parking_lot': 'SSAFY 주차장',
            'entry_time': timezone.now().isoformat(),
            'admin_action': True,
            'action_url': '/parking-recommend',
            'action_type': 'navigate'
        }
        
        try:
            entry_result = send_vehicle_entry_notification(user, entry_data)
            self.stdout.write(f"   ✅ 입차 알림 생성 성공: {entry_result.id if hasattr(entry_result, 'id') else entry_result}")
        except Exception as e:
            self.stdout.write(f"   ❌ 입차 알림 실패: {str(e)}")
        
        # 3. 주차 배정 알림 테스트
        self.stdout.write("\n🅿️ 주차 배정 알림 테스트...")
        assignment_data = {
            'plate_number': vehicle.license_plate,
            'parking_space': 'A1',
            'assignment_time': timezone.now().isoformat(),
            'admin_action': True
        }
        
        try:
            assignment_result = send_parking_assigned_notification(user, assignment_data)
            self.stdout.write(f"   ✅ 주차 배정 알림 생성 성공: {assignment_result.id if hasattr(assignment_result, 'id') else assignment_result}")
        except Exception as e:
            self.stdout.write(f"   ❌ 주차 배정 알림 실패: {str(e)}")
        
        # 4. 주차 완료 알림 테스트
        self.stdout.write("\n✅ 주차 완료 알림 테스트...")
        parking_data = {
            'plate_number': vehicle.license_plate,
            'parking_space': 'A1',
            'parking_time': timezone.now().isoformat(),
            'score': 85,
            'admin_action': True
        }
        
        try:
            parking_result = send_parking_complete_notification(user, parking_data)
            self.stdout.write(f"   ✅ 주차 완료 알림 생성 성공: {parking_result.id if hasattr(parking_result, 'id') else parking_result}")
        except Exception as e:
            self.stdout.write(f"   ❌ 주차 완료 알림 실패: {str(e)}")
        
        # 5. 출차 알림 테스트
        self.stdout.write("\n🚙 출차 알림 테스트...")
        exit_data = {
            'plate_number': vehicle.license_plate,
            'parking_space': 'A1',
            'exit_time': timezone.now().isoformat(),
            'parking_duration': '2시간 30분',
            'admin_action': True
        }
        
        try:
            exit_result = send_vehicle_exit_notification(user, exit_data)
            self.stdout.write(f"   ✅ 출차 알림 생성 성공: {exit_result.id if hasattr(exit_result, 'id') else exit_result}")
        except Exception as e:
            self.stdout.write(f"   ❌ 출차 알림 실패: {str(e)}")
        
        # 6. 알림 데이터베이스 확인
        self.stdout.write("\n📋 알림 데이터베이스 확인...")
        recent_notifications = Notification.objects.filter(user=user).order_by('-created_at')[:5]
        
        if recent_notifications:
            self.stdout.write(f"   총 {len(recent_notifications)}개의 최근 알림:")
            for notif in recent_notifications:
                self.stdout.write(f"   - [{notif.notification_type}] {notif.title}")
                self.stdout.write(f"     메시지: {notif.message}")
                self.stdout.write(f"     생성시간: {notif.created_at}")
                self.stdout.write(f"     읽음여부: {'읽음' if notif.is_read else '미읽음'}")
                self.stdout.write("")
        else:
            self.stdout.write("   ❌ 최근 알림이 없습니다.")
        
        self.stdout.write("="*50)
        self.stdout.write("테스트 완료!")
        self.stdout.write("="*50)
        self.stdout.write("📌 주의사항:")
        self.stdout.write("- 이 테스트는 단순 동기 처리 방식을 사용합니다")
        self.stdout.write("- Redis나 Celery가 필요하지 않습니다")
        self.stdout.write("- 관리자 액션 시 즉시 알림이 생성되고 푸시가 전송됩니다")
        self.stdout.write("- 실제 푸시 수신을 위해서는 프론트엔드에서 Service Worker 구독이 필요합니다")