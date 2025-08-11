# accounts/utils.py
import json
from typing import Dict, Any, Optional

from pywebpush import webpush, WebPushException
from django.conf import settings

from .models import Notification, PushSubscription


def create_notification(user, title, message, notification_type='system', data=None, use_celery=False):
    """
    알림 생성 및 푸시 알림 전송 (동기 처리)
    
    Args:
        user: 알림을 받을 사용자
        title: 알림 제목
        message: 알림 내용
        notification_type: 알림 타입
        data: 추가 데이터 (선택)
        use_celery: 이전 버전 호환성을 위한 매개변수 (무시됨)
    
    Returns:
        생성된 알림 객체
    """
    if data is None:
        data = {}
    
    try:
        # 알림 생성
        notification = Notification.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            data=data
        )
        
        # 알림 생성 로그
        print(f"[NOTIFICATION] 알림 생성: {notification.id}")
        
        # 푸시 알림 전송 (사용자가 푸시 알림을 허용한 경우에만)
        if hasattr(user, 'push_enabled') and user.push_enabled:
            try:
                send_push_notification(user, title, message, data)
                print(f"[PUSH] 푸시 알림 전송 요청: {user.email} - {title}")
            except Exception as push_error:
                print(f"[PUSH ERROR] 푸시 전송 실패: {str(push_error)}")
                # 푸시 전송 실패해도 알림 생성은 성공으로 처리
        else:
            print(f"[PUSH] 푸시 알림 비활성화됨: {user.email} (push_enabled={getattr(user, 'push_enabled', 'N/A')})")
        
        return notification
        
    except Exception as e:
        print(f"[ERROR] 알림 생성 실패: {str(e)}")
        raise e


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
    
    try:
        # 사용자의 모든 구독 정보 조회
        subscriptions = PushSubscription.objects.filter(user=user)
        
        if not subscriptions.exists():
            print(f"[PUSH] 구독 정보 없음: {user.email} - 프론트엔드에서 service worker 구독 등록 필요")
            return
        
    except Exception as e:
        print(f"[PUSH ERROR] 구독 정보 조회 실패: {str(e)}")
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
    
    try:
        # VAPID 설정
        vapid_private_key = getattr(settings, 'VAPID_PRIVATE_KEY', None)
        vapid_public_key = getattr(settings, 'VAPID_PUBLIC_KEY', None)
        vapid_claims = {
            'sub': 'mailto:admin@i13e102.p.ssafy.io'
        }
        
        if not vapid_private_key or not vapid_public_key:
            print("[PUSH] VAPID 키 누락")
            return
        
    except Exception as e:
        print(f"[PUSH ERROR] VAPID 설정 확인 중 오류: {str(e)}")
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
            print(f"[PUSH SUCCESS] 푸시 전송 성공: {user.email}")
        except WebPushException as ex:
            if ex.response.status_code in [404, 410]:
                subscription.delete()
        except Exception as ex:
            print(f"[PUSH ERROR] {ex}")


# 알림 전송 관련 함수들은 accounts/notification_helpers.py로 이동됨