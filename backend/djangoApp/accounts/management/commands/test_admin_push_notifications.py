# accounts/management/commands/test_admin_push_notifications.py
"""
관리자 페이지 이벤트별 푸시 알림 테스트 명령어
- 입차, 주차 배정, 주차 완료, 출차 등의 관리자 액션으로 발생하는 알림 테스트
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import User
from accounts.utils import (
    create_notification,
    send_vehicle_entry_notification,
    send_parking_complete_notification,
)


class Command(BaseCommand):
    help = "관리자 페이지 이벤트별 푸시 알림 테스트"

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            type=str,
            default="test@example.com",
            help="테스트할 사용자 이메일 (기본값: test@example.com)",
        )
        parser.add_argument(
            "--event",
            type=str,
            choices=["entry", "assignment", "reassignment", "complete", "exit", "all"],
            default="all",
            help="테스트할 이벤트 타입",
        )

    def handle(self, *args, **options):
        email = options["email"]
        event_type = options["event"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"사용자를 찾을 수 없습니다: {email}"))
            return

        self.stdout.write("=== 관리자 이벤트 푸시 알림 테스트 ===")
        self.stdout.write(f"테스트 사용자: {user.email} ({user.nickname})")
        self.stdout.write(f"푸시 알림 허용: {'예' if user.push_enabled else '아니오'}")
        self.stdout.write("")

        if event_type == "all" or event_type == "entry":
            self.test_vehicle_entry_notification(user)

        if event_type == "all" or event_type == "assignment":
            self.test_parking_assignment_notification(user)

        if event_type == "all" or event_type == "reassignment":
            self.test_parking_reassignment_notification(user)

        if event_type == "all" or event_type == "complete":
            self.test_parking_complete_notification(user)

        if event_type == "all" or event_type == "exit":
            self.test_vehicle_exit_notification(user)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("✅ 모든 테스트 완료"))

    def test_vehicle_entry_notification(self, user):
        """입차 알림 테스트"""
        self.stdout.write("1. 입차 알림 테스트...")

        entry_data = {
            "plate_number": "12가3456",
            "parking_lot": "SSAFY 주차장",
            "entry_time": timezone.now().isoformat(),
            "admin_action": True,
            "action_url": "/parking-recommend",
            "action_type": "navigate",
        }

        try:
            send_vehicle_entry_notification(user, entry_data)
            self.stdout.write(self.style.SUCCESS("   ✅ 입차 알림 전송 성공"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ 입차 알림 전송 실패: {str(e)}"))

    def test_parking_assignment_notification(self, user):
        """주차 배정 알림 테스트"""
        self.stdout.write("2. 주차 배정 알림 테스트...")

        assignment_data = {
            "plate_number": "12가3456",
            "assigned_space": "A5",
            "assignment_time": timezone.now().isoformat(),
            "admin_action": True,
            "action_url": "/parking-recommend",
            "action_type": "navigate",
        }

        try:
            create_notification(
                user=user,
                title="🅿️ 주차 구역 배정",
                message=f"{assignment_data['plate_number']} 차량이 {assignment_data['assigned_space']} 구역에 배정`되었습니다. 안내에 따라 주차해 주세요.",
                notification_type="parking_assigned",
                data=assignment_data,
            )
            self.stdout.write(self.style.SUCCESS("   ✅ 주차 배정 알림 전송 성공"))
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"   ❌ 주차 배정 알림 전송 실패: {str(e)}")
            )

    def test_parking_reassignment_notification(self, user):
        """주차 재배정 알림 테스트"""
        self.stdout.write("3. 주차 재배정 알림 테스트...")

        reassignment_data = {
            "plate_number": "12가3456",
            "old_space": "A5",
            "new_space": "B3",
            "reassignment_time": timezone.now().isoformat(),
            "admin_action": True,
            "action_url": "/parking-recommend",
            "action_type": "navigate",
        }

        try:
            create_notification(
                user=user,
                title="🔄 주차 구역 재배정",
                message=f"{reassignment_data['plate_number']} 차량의 주차 구역이 {reassignment_data['new_space']}로 변경되었습니다.",
                notification_type="parking_assigned",
                data=reassignment_data,
            )
            self.stdout.write(self.style.SUCCESS("   ✅ 주차 재배정 알림 전송 성공"))
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"   ❌ 주차 재배정 알림 전송 실패: {str(e)}")
            )

    def test_parking_complete_notification(self, user):
        """주차 완료 알림 테스트"""
        self.stdout.write("4. 주차 완료 알림 테스트...")

        parking_data = {
            "plate_number": "12가3456",
            "parking_space": "A5",
            "parking_time": timezone.now().isoformat(),
            "score": 85,
            "admin_action": True,
        }

        try:
            send_parking_complete_notification(user, parking_data)
            self.stdout.write(self.style.SUCCESS("   ✅ 주차 완료 알림 전송 성공"))
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"   ❌ 주차 완료 알림 전송 실패: {str(e)}")
            )

    def test_vehicle_exit_notification(self, user):
        """출차 완료 알림 테스트"""
        self.stdout.write("5. 출차 완료 알림 테스트...")

        exit_data = {
            "plate_number": "12가3456",
            "parking_space": "A5",
            "exit_time": timezone.now().isoformat(),
            "parking_duration": "2시간 30분",
            "admin_action": True,
            "action_url": "/parking-recommend",
            "action_type": "navigate",
        }

        try:
            create_notification(
                user=user,
                title="🚗 출차 완료",
                message=f"{exit_data['plate_number']} 차량이 {exit_data['parking_space']} 구역에서 출차 완료되었습니다. 주차 시간: {exit_data['parking_duration']}",
                notification_type="exit",
                data=exit_data,
            )
            self.stdout.write(self.style.SUCCESS("   ✅ 출차 완료 알림 전송 성공"))
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"   ❌ 출차 완료 알림 전송 실패: {str(e)}")
            )
