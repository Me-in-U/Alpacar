# accounts/utils.py
import json
from pywebpush import webpush, WebPushException
from django.conf import settings

from .models import Notification, PushSubscription


def create_notification(user, title, message, notification_type='system', data=None):
    """
    알림 생성 및 푸시 알림 전송
    
    Args:
        user: 알림을 받을 사용자
        title: 알림 제목
        message: 알림 내용
        notification_type: 알림 타입
        data: 추가 데이터 (선택)
    
    Returns:
        생성된 알림 객체
    """
    if data is None:
        data = {}
    
    # 알림 생성
    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        data=data
    )
    
    # 푸시 알림 전송 (사용자가 푸시 알림을 허용한 경우에만)
    if user.push_enabled:
        send_push_notification(user, title, message, data)
    
    return notification


def send_push_notification(user, title, message, data=None):
    """
    특정 사용자에게 푸시 알림 전송
    
    Args:
        user: 알림을 받을 사용자
        title: 알림 제목
        message: 알림 내용
        data: 추가 데이터 (선택)
    """
    if data is None:
        data = {}
        
    # 사용자의 모든 구독 정보 조회
    subscriptions = PushSubscription.objects.filter(user=user)
    
    if not subscriptions.exists():
        print(f"[PUSH] 사용자 {user.email}의 구독 정보가 없습니다.")
        return
    
    # 푸시 알림 페이로드 구성
    payload = {
        'title': title,
        'body': message,
        'icon': '/icons/favicon-32x32.png',  # PWA 아이콘
        'badge': '/icons/favicon-16x16.png',
        'tag': 'notification',
        'requireInteraction': True,
        'data': data
    }
    
    # VAPID 설정
    vapid_private_key = getattr(settings, 'VAPID_PRIVATE_KEY', None)
    vapid_public_key = getattr(settings, 'VAPID_PUBLIC_KEY', None)
    vapid_claims = {
        'sub': 'mailto:admin@i13e102.p.ssafy.io'
    }
    
    if not vapid_private_key or not vapid_public_key:
        print("[PUSH] VAPID 키가 설정되지 않았습니다.")
        return
    
    # 각 구독 정보에 푸시 알림 전송
    for subscription in subscriptions:
        try:
            webpush(
                subscription_info={
                    'endpoint': subscription.endpoint,
                    'keys': {
                        'p256dh': subscription.p256dh,
                        'auth': subscription.auth
                    }
                },
                data=json.dumps(payload),
                vapid_private_key=vapid_private_key,
                vapid_claims=vapid_claims
            )
            print(f"[PUSH] 푸시 알림 전송 성공: {user.email}")
        except WebPushException as ex:
            print(f"[PUSH] 푸시 알림 전송 실패: {user.email} - {ex}")
            # 만료된 구독 정보 삭제 (선택적)
            if ex.response.status_code in [404, 410]:
                print(f"[PUSH] 만료된 구독 정보 삭제: {subscription.endpoint}")
                subscription.delete()
        except Exception as ex:
            print(f"[PUSH] 예상치 못한 오류: {user.email} - {ex}")


def send_parking_complete_notification(user, parking_data):
    """
    주차 완료 알림 전송
    
    Args:
        user: 알림을 받을 사용자
        parking_data: 주차 정보 (시간, 위치 등)
    """
    title = "주차 완료 알림"
    message = f"주차 일시: {parking_data.get('parking_time', '')}\n주차 공간: {parking_data.get('parking_space', '')}"
    
    create_notification(
        user=user,
        title=title,
        message=message,
        notification_type='parking_complete',
        data=parking_data
    )


def send_grade_upgrade_notification(user, grade_data):
    """
    등급 승급 알림 전송
    
    Args:
        user: 알림을 받을 사용자
        grade_data: 등급 정보 (이전 등급, 새 등급 등)
    """
    title = "등급 승급 알림"
    old_grade = grade_data.get('old_grade', '')
    new_grade = grade_data.get('new_grade', '')
    message = f"주차 등급이 {old_grade}에서 {new_grade}로 승급되었습니다"
    
    create_notification(
        user=user,
        title=title,
        message=message,
        notification_type='grade_upgrade',
        data=grade_data
    )