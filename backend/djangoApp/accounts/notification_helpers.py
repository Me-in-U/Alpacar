# accounts/notification_helpers.py
"""
관리자 액션에 따른 푸시 알림 전용 헬퍼 함수들
"""
from typing import Dict, Any, Optional
from django.contrib.auth import get_user_model
from .utils import create_notification

User = get_user_model()


def send_vehicle_entry_notification(user, data: Dict[str, Any]):
    """
    차량 입차 알림 전송
    
    Args:
        user: 대상 사용자
        data: 입차 관련 데이터
            - plate_number: 번호판
            - parking_lot: 주차장명
            - entry_time: 입차 시간
            - admin_action: 관리자 액션 여부
            - action_url: 클릭 시 이동할 URL (선택)
    """
    plate_number = data.get('plate_number', '')
    parking_lot = data.get('parking_lot', 'SSAFY 주차장')
    entry_time = data.get('entry_time', '')
    admin_action = data.get('admin_action', False)
    
    if admin_action:
        title = "🚗 관리자 입차 처리"
        message = f"관리자가 {plate_number} 차량의 입차를 처리했습니다."
    else:
        title = "🚗 차량 입차 알림"
        message = f"{plate_number} 차량이 {parking_lot}에 입차되었습니다."
    
    notification_data = {
        'plate_number': plate_number,
        'parking_lot': parking_lot,
        'entry_time': entry_time,
        'admin_action': admin_action,
        'action_url': data.get('action_url', '/parking-recommend'),
        'action_type': data.get('action_type', 'navigate')
    }
    
    return create_notification(
        user=user,
        title=title,
        message=message,
        notification_type='vehicle_entry',
        data=notification_data,
        use_celery=False
    )


def send_parking_assigned_notification(user, data: Dict[str, Any]):
    """
    주차 배정 알림 전송
    
    Args:
        user: 대상 사용자
        data: 배정 관련 데이터
            - plate_number: 번호판
            - parking_space: 배정된 주차 구역
            - assignment_time: 배정 시간
            - admin_action: 관리자 액션 여부
    """
    plate_number = data.get('plate_number', '')
    parking_space = data.get('parking_space', '')
    assignment_time = data.get('assignment_time', '')
    admin_action = data.get('admin_action', False)
    
    if admin_action:
        title = "🅿️ 관리자 주차 배정"
        message = f"관리자가 {plate_number} 차량을 {parking_space} 구역에 배정했습니다."
    else:
        title = "🅿️ 주차 배정 완료"
        message = f"{plate_number} 차량이 {parking_space} 구역에 배정되었습니다."
    
    notification_data = {
        'plate_number': plate_number,
        'parking_space': parking_space,
        'assignment_time': assignment_time,
        'admin_action': admin_action,
        'action_url': '/admin/parking-status',
        'action_type': 'navigate'
    }
    
    return create_notification(
        user=user,
        title=title,
        message=message,
        notification_type='parking_assigned',
        data=notification_data,
        use_celery=False
    )


def send_parking_complete_notification(user, data: Dict[str, Any]):
    """
    주차 완료 알림 전송
    
    Args:
        user: 대상 사용자
        data: 주차 완료 관련 데이터
            - plate_number: 번호판
            - parking_space: 주차 구역
            - parking_time: 주차 완료 시간
            - score: 주차 점수 (선택)
            - admin_action: 관리자 액션 여부
    """
    plate_number = data.get('plate_number', '')
    parking_space = data.get('parking_space', '')
    parking_time = data.get('parking_time', '')
    score = data.get('score')
    admin_action = data.get('admin_action', False)
    
    if admin_action:
        title = "✅ 관리자 주차 완료 처리"
        if score:
            message = f"관리자가 {plate_number} 차량의 주차를 완료 처리했습니다. ({parking_space} 구역, {score}점)"
        else:
            message = f"관리자가 {plate_number} 차량의 주차를 완료 처리했습니다. ({parking_space} 구역)"
    else:
        title = "✅ 주차 완료"
        if score:
            message = f"{plate_number} 차량이 {parking_space} 구역에 주차 완료되었습니다. ({score}점)"
        else:
            message = f"{plate_number} 차량이 {parking_space} 구역에 주차 완료되었습니다."
    
    notification_data = {
        'plate_number': plate_number,
        'parking_space': parking_space,
        'parking_time': parking_time,
        'score': score,
        'admin_action': admin_action,
        'action_url': '/parking-history',
        'action_type': 'navigate'
    }
    
    return create_notification(
        user=user,
        title=title,
        message=message,
        notification_type='parking_complete',
        data=notification_data,
        use_celery=False
    )


def send_vehicle_exit_notification(user, data: Dict[str, Any]):
    """
    차량 출차 알림 전송
    
    Args:
        user: 대상 사용자
        data: 출차 관련 데이터
            - plate_number: 번호판
            - parking_space: 주차했던 구역
            - exit_time: 출차 시간
            - parking_duration: 주차 시간 (선택)
            - admin_action: 관리자 액션 여부
    """
    plate_number = data.get('plate_number', '')
    parking_space = data.get('parking_space', '')
    exit_time = data.get('exit_time', '')
    parking_duration = data.get('parking_duration')
    admin_action = data.get('admin_action', False)
    
    if admin_action:
        title = "🚙 관리자 출차 처리"
        if parking_duration:
            message = f"관리자가 {plate_number} 차량의 출차를 처리했습니다. ({parking_space} 구역에서 {parking_duration} 주차)"
        else:
            message = f"관리자가 {plate_number} 차량의 출차를 처리했습니다. ({parking_space} 구역)"
    else:
        title = "🚙 차량 출차 완료"
        if parking_duration:
            message = f"{plate_number} 차량이 출차 완료되었습니다. ({parking_space} 구역에서 {parking_duration} 주차)"
        else:
            message = f"{plate_number} 차량이 출차 완료되었습니다. ({parking_space} 구역)"
    
    notification_data = {
        'plate_number': plate_number,
        'parking_space': parking_space,
        'exit_time': exit_time,
        'parking_duration': parking_duration,
        'admin_action': admin_action,
        'action_url': '/parking-history',
        'action_type': 'navigate'
    }
    
    return create_notification(
        user=user,
        title=title,
        message=message,
        notification_type='vehicle_exit',
        data=notification_data,
        use_celery=False
    )