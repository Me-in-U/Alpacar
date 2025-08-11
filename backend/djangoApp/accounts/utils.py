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
    
    try:
        # 알림 생성
        notification = Notification.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            data=data
        )
        
        # Unicode-safe logging
        try:
            print(f"[NOTIFICATION] 알림 생성 성공: {notification.id} - {repr(title)}")
        except UnicodeEncodeError:
            print(f"[NOTIFICATION] 알림 생성 성공: {notification.id} - ID:{notification_type}")
        
        # 푸시 알림 전송 (사용자가 푸시 알림을 허용한 경우에만)
        if hasattr(user, 'push_enabled') and user.push_enabled:
            try:
                send_push_notification(user, title, message, data)
                print(f"[PUSH] 푸시 알림 전송 시도 완료: {user.email}")
            except Exception as push_error:
                try:
                    print(f"[PUSH ERROR] 푸시 전송 실패하지만 알림은 생성됨: {repr(str(push_error))}")
                except UnicodeEncodeError:
                    print("[PUSH ERROR] 푸시 전송 실패하지만 알림은 생성됨: Unicode error")
                # 푸시 전송 실패해도 알림 생성은 성공으로 처리
        else:
            print(f"[PUSH] 푸시 알림 비활성화 또는 설정 없음: {user.email}")
        
        return notification
        
    except Exception as e:
        try:
            print(f"[ERROR] 알림 생성 실패: {repr(str(e))}")
            print(f"[DEBUG] user={user.id}, title={repr(title)}, type={notification_type}")
        except UnicodeEncodeError:
            print(f"[ERROR] 알림 생성 실패: Unicode error")
            print(f"[DEBUG] user={user.id}, type={notification_type}")
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
            print(f"[PUSH] 사용자 {user.email}의 구독 정보가 없습니다.")
            return
        
        print(f"[PUSH] 구독 정보 {subscriptions.count()}개 찾음: {user.email}")
        
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
            print("[PUSH] VAPID 키가 설정되지 않았습니다.")
            print(f"[PUSH DEBUG] private_key_exists: {bool(vapid_private_key)}, public_key_exists: {bool(vapid_public_key)}")
            return
            
        print(f"[PUSH] VAPID 설정 확인됨")
        
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
            print(f"[PUSH] 푸시 알림 전송 성공: {user.email}")
        except WebPushException as ex:
            print(f"[PUSH] 푸시 알림 전송 실패: {user.email} - {ex}")
            # 만료된 구독 정보 삭제 (선택적)
            if ex.response.status_code in [404, 410]:
                print(f"[PUSH] 만료된 구독 정보 삭제: {subscription.endpoint}")
                subscription.delete()
        except Exception as ex:
            print(f"[PUSH] 예상치 못한 오류: {user.email} - {ex}")


def send_vehicle_entry_notification(user, entry_data):
    """
    입차 알림 전송
    
    Args:
        user: 알림을 받을 사용자
        entry_data: 입차 정보 (차량번호, 주차장명 등)
    """
    plate_number = entry_data.get('plate_number', '차량')
    parking_lot = entry_data.get('parking_lot', 'SSAFY 주차장')
    
    title = "🚗 입차 알림"
    message = f"{plate_number} 차량이 {parking_lot}에 입차하였습니다. 알림을 클릭하면 추천 주차자리를 안내드리겠습니다."
    
    # 입차 알림 데이터에 페이지 라우팅 정보 추가
    entry_data['action_url'] = '/parking-recommend'
    entry_data['action_type'] = 'navigate'
    
    create_notification(
        user=user,
        title=title,
        message=message,
        notification_type='vehicle_entry',
        data=entry_data
    )


def send_parking_complete_notification(user, parking_data):
    """
    주차 완료 알림 전송
    
    Args:
        user: 알림을 받을 사용자
        parking_data: 주차 정보 (시간, 위치, 점수 등)
    """
    plate_number = parking_data.get('plate_number', '차량')
    parking_space = parking_data.get('parking_space', 'A5')
    score = parking_data.get('score')
    
    title = "🅿️ 주차 완료"
    
    if score is not None:
        message = f"{plate_number} 차량이 {parking_space} 구역에 주차를 완료했습니다. 이번 주차의 점수는 {score}점입니다."
    else:
        message = f"{plate_number} 차량이 {parking_space} 구역에 주차를 완료했습니다."
    
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
    title = "🎉 등급 승급 축하!"
    old_grade = grade_data.get('old_grade', '이전 등급')
    new_grade = grade_data.get('new_grade', '새 등급')
    current_score = grade_data.get('current_score', user.score)
    
    message = f"축하드립니다! 주차 등급이 {old_grade}에서 {new_grade}로 승급되었습니다. (현재 점수: {current_score}점)"
    
    create_notification(
        user=user,
        title=title,
        message=message,
        notification_type='grade_upgrade',
        data=grade_data
    )