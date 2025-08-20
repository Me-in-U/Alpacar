# accounts/utils.py

import json

from django.conf import settings
from pywebpush import WebPushException, webpush

from .models import Notification, PushSubscription


def create_notification(user, title, message, notification_type="system", data=None):
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
            data=data,
        )

        # 푸시 알림 전송 (사용자가 푸시 알림을 허용한 경우에만)
        if user.push_enabled:
            try:
                send_push_notification(user, title, message, data, notification_type)
                print(f"[PUSH] 푸시 알림 전송 시도: {user.email} - {title}")
            except Exception as push_error:
                print(
                    f"[PUSH ERROR] 푸시 알림 전송 실패: {user.email} - {str(push_error)}"
                )

        return notification

    except Exception as e:
        print(e)  # 예외 발생 시 로깅
        raise e


import json
from typing import Dict, Optional, Tuple


def _build_payload(
    title: str, message: str, data: Optional[Dict], notification_type: str
) -> Dict:
    return {
        "title": title,
        "body": message,
        "icon": "/icons/favicon-32x32.png",
        "badge": "/icons/favicon-16x16.png",
        "tag": f"notification-{notification_type}",
        "requireInteraction": True,
        "type": notification_type,
        "data": data or {},
    }


def _get_vapid() -> Tuple[Optional[str], Optional[str], Dict]:
    private_key = getattr(settings, "VAPID_PRIVATE_KEY", None)
    public_key = getattr(settings, "VAPID_PUBLIC_KEY", None)
    claims = {"sub": "mailto:admin@i13e102.p.ssafy.io"}
    return private_key, public_key, claims


def _send_one(
    subscription, payload: Dict, vapid_private_key: str, vapid_claims: Dict
) -> None:
    """단일 구독으로 푸시 전송 & 예외 처리(삭제 여부 포함)"""
    try:
        print(f"[PUSH] 전송 시도 중: {subscription.endpoint[:50]}...")
        webpush(
            subscription_info={
                "endpoint": subscription.endpoint,
                "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth},
            },
            data=json.dumps(payload),
            vapid_private_key=vapid_private_key,
            vapid_claims=vapid_claims,
        )
        print("[PUSH] 전송 성공")
    except WebPushException as ex:
        status = getattr(getattr(ex, "response", None), "status_code", None)
        if status is not None:
            # 응답 있는 실패 (404/410 → 구독 만료)
            print(f"[PUSH ERROR] WebPush 실패: {status} - {ex}")
            if status in (404, 410):
                subscription.delete()
                print(f"[PUSH] 만료된 구독 삭제: {subscription.endpoint[:50]}...")
            return
        # 응답 없는 실패
        print(f"[PUSH ERROR] WebPush 실패 (응답 없음): {ex}")
        if "test-endpoint" in subscription.endpoint:
            subscription.delete()
            print(f"[PUSH] 테스트 구독 삭제: {subscription.endpoint[:50]}...")
    except Exception as ex:
        print(f"[PUSH ERROR] 일반 오류: {ex}")


def send_push_notification(
    user, title, message, data=None, notification_type: str = "system"
):
    """특정 사용자에게 푸시 알림 전송 (인지 복잡도 감소 버전)"""
    # 구독 조회 + 가드 절
    subscriptions = PushSubscription.objects.filter(user=user)
    if not subscriptions.exists():
        print(f"[PUSH] 구독 정보 없음: {getattr(user, 'email', user)}")
        return
    print(f"[PUSH] 구독 {subscriptions.count()}개 발견: {getattr(user, 'email', user)}")

    # 페이로드 & VAPID
    payload = _build_payload(title, message, data, notification_type)
    vapid_private_key, vapid_public_key, vapid_claims = _get_vapid()
    if not (vapid_private_key and vapid_public_key):
        print(
            f"[PUSH ERROR] VAPID 키 설정 누락 - private:{bool(vapid_private_key)} public:{bool(vapid_public_key)}"
        )
        return
    print("[PUSH] VAPID 확인, 페이로드 준비 완료")

    # 전송
    for sub in subscriptions:
        _send_one(sub, payload, vapid_private_key, vapid_claims)


def send_vehicle_entry_notification(user, entry_data):
    """
    입차 알림 전송

    Args:
        user: 알림을 받을 사용자
        entry_data: 입차 정보 (차량번호, 주차장명 등)
    """
    plate_number = entry_data.get("plate_number", "차량")
    parking_lot = entry_data.get("parking_lot", "SSAFY 주차장")

    # 이모지 인코딩 문제 해결
    title = "입차 알림"
    message = f"{plate_number} 차량이 {parking_lot}에 입차하였습니다. 알림을 클릭하면 추천 주차자리를 안내드리겠습니다."

    # 입차 알림 데이터에 페이지 라우팅 정보 추가
    entry_data["action_url"] = "/parking-recommend"
    entry_data["action_type"] = "navigate"

    create_notification(
        user=user,
        title=title,
        message=message,
        notification_type="entry",
        data=entry_data,
    )


def send_parking_complete_notification(user, parking_data):
    """
    주차 완료 알림 전송

    Args:
        user: 알림을 받을 사용자
        parking_data: 주차 정보 (시간, 위치, 점수 등)
    """
    plate_number = parking_data.get("plate_number", "차량")
    parking_space = parking_data.get("parking_space", "A5")
    score = parking_data.get("score")

    # 이모지 인코딩 문제 해결 - 간단한 텍스트 사용
    title = "주차 완료"

    if score is not None:
        message = f"{plate_number} 차량이 {parking_space} 구역에 주차를 완료했습니다. 이번 주차의 점수는 {score}점입니다."
    else:
        message = f"{plate_number} 차량이 {parking_space} 구역에 주차를 완료했습니다."

    # 주차 완료 알림 타입을 parking_complete로 변경
    create_notification(
        user=user,
        title=title,
        message=message,
        notification_type="parking_complete",  # parking_complete 타입으로 변경하여 Service Worker에서 올바른 라우팅
        data=parking_data,
    )


def send_grade_upgrade_notification(user, grade_data):
    """
    등급 승급 알림 전송

    Args:
        user: 알림을 받을 사용자
        grade_data: 등급 정보 (이전 등급, 새 등급 등)
    """
    # 이모지 인코딩 문제 해결
    title = "등급 승급 축하!"
    old_grade = grade_data.get("old_grade", "이전 등급")
    new_grade = grade_data.get("new_grade", "새 등급")
    current_score = grade_data.get("current_score", user.score)

    message = f"축하드립니다! 주차 등급이 {old_grade}에서 {new_grade}로 승급되었습니다. (현재 점수: {current_score}점)"

    create_notification(
        user=user,
        title=title,
        message=message,
        notification_type="general",
        data=grade_data,
    )
