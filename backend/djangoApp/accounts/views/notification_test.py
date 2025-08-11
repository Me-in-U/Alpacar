# accounts/views/notification_test.py
"""
푸시 알림 테스트를 위한 고급 API 엔드포인트
- 다양한 알림 타입 테스트
- 커스텀 알림 생성
- 배치 알림 전송
- 알림 시뮬레이션
"""

import json
import random
import time
from datetime import datetime, timedelta
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import Notification, PushSubscription
from ..utils import create_notification, send_push_notification
from ..serializers.notifications import NotificationSerializer


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_custom_notification(request):
    """
    사용자 정의 알림 생성 및 전송
    """
    user = request.user
    data = request.data
    
    # 필수 필드 검증
    required_fields = ['title', 'message']
    for field in required_fields:
        if not data.get(field):
            return Response({
                'error': f'{field} 필드는 필수입니다.'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    # 선택적 필드
    notification_type = data.get('notification_type', 'system')
    extra_data = data.get('data', {})
    
    # 테스트 태그 추가
    extra_data['test'] = True
    extra_data['custom'] = True
    extra_data['created_by'] = 'api_test'
    extra_data['timestamp'] = timezone.now().isoformat()
    
    try:
        notification = create_notification(
            user=user,
            title=data['title'],
            message=data['message'],
            notification_type=notification_type,
            data=extra_data
        )
        
        return Response({
            'success': True,
            'message': '사용자 정의 알림이 생성되었습니다.',
            'notification': {
                'id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'type': notification.notification_type,
                'data': notification.data,
                'created_at': notification.created_at.isoformat()
            },
            'push_sent': user.push_enabled,
            'push_subscriptions': PushSubscription.objects.filter(user=user).count()
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': f'알림 생성 실패: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def send_batch_notifications(request):
    """
    여러 개의 알림을 배치로 전송
    """
    user = request.user
    data = request.data
    
    notifications_data = data.get('notifications', [])
    if not notifications_data:
        return Response({
            'error': 'notifications 배열이 필요합니다.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if len(notifications_data) > 10:
        return Response({
            'error': '한 번에 최대 10개의 알림만 전송할 수 있습니다.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    results = []
    delay = data.get('delay', 2)  # 알림 간 간격 (초)
    
    try:
        for i, notification_data in enumerate(notifications_data):
            if i > 0 and delay > 0:
                time.sleep(delay)
            
            # 필수 필드 확인
            if not all(key in notification_data for key in ['title', 'message']):
                results.append({
                    'index': i,
                    'status': 'error',
                    'error': 'title과 message 필드가 필요합니다.'
                })
                continue
            
            # 알림 생성
            extra_data = notification_data.get('data', {})
            extra_data.update({
                'test': True,
                'batch': True,
                'batch_index': i,
                'batch_total': len(notifications_data),
                'timestamp': timezone.now().isoformat()
            })
            
            notification = create_notification(
                user=user,
                title=notification_data['title'],
                message=notification_data['message'],
                notification_type=notification_data.get('notification_type', 'system'),
                data=extra_data
            )
            
            results.append({
                'index': i,
                'status': 'success',
                'notification_id': notification.id,
                'title': notification.title
            })
        
        success_count = len([r for r in results if r['status'] == 'success'])
        
        return Response({
            'success': True,
            'message': f'{success_count}/{len(notifications_data)}개의 알림이 전송되었습니다.',
            'results': results,
            'delay_used': delay,
            'push_enabled': user.push_enabled
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': f'배치 알림 전송 실패: {str(e)}',
            'partial_results': results
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def simulate_scenario(request):
    """
    특정 시나리오를 시뮬레이션하여 연속적인 알림 생성
    """
    user = request.user
    scenario_type = request.data.get('scenario', 'parking_flow')
    
    scenarios = {
        'parking_flow': _simulate_parking_flow,
        'daily_usage': _simulate_daily_usage,
        'emergency_alerts': _simulate_emergency_alerts,
        'grade_progression': _simulate_grade_progression
    }
    
    if scenario_type not in scenarios:
        return Response({
            'error': f'지원하지 않는 시나리오입니다. 가능한 시나리오: {list(scenarios.keys())}'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        results = scenarios[scenario_type](user, request.data)
        
        return Response({
            'success': True,
            'scenario': scenario_type,
            'message': f'{scenario_type} 시나리오가 실행되었습니다.',
            'results': results,
            'notifications_created': len([r for r in results if r.get('status') == 'success'])
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': f'시나리오 실행 실패: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _simulate_parking_flow(user, params):
    """주차장 이용 플로우 시뮬레이션"""
    results = []
    delay = params.get('delay', 3)
    plate_number = params.get('plate_number', '220로1284')
    parking_lot = params.get('parking_lot', 'SSAFY 주차장')
    
    # 1. 입차 알림
    entry_data = {
        'plate_number': plate_number,
        'parking_lot': parking_lot,
        'entry_time': timezone.now().isoformat(),
        'test': True,
        'scenario': 'parking_flow'
    }
    
    notification = create_notification(
        user=user,
        title="🚗 차량 입차 감지",
        message=f"{plate_number} 차량이 {parking_lot}에 입차하였습니다. 추천 주차구역을 확인하세요.",
        notification_type='vehicle_entry',
        data=entry_data
    )
    results.append({'step': 'entry', 'status': 'success', 'notification_id': notification.id})
    
    time.sleep(delay)
    
    # 2. 주차 진행 알림
    progress_data = {
        'plate_number': plate_number,
        'recommended_space': 'A5',
        'distance': '20m',
        'test': True,
        'scenario': 'parking_flow'
    }
    
    notification = create_notification(
        user=user,
        title="🅿️ 주차 진행 중",
        message=f"추천 구역 A5로 이동 중입니다. 남은 거리: 20m",
        notification_type='system',
        data=progress_data
    )
    results.append({'step': 'progress', 'status': 'success', 'notification_id': notification.id})
    
    time.sleep(delay)
    
    # 3. 주차 완료 알림
    complete_data = {
        'plate_number': plate_number,
        'parking_space': 'A5',
        'parking_time': timezone.now().isoformat(),
        'score': random.randint(75, 95),
        'duration': '45초',
        'test': True,
        'scenario': 'parking_flow'
    }
    
    notification = create_notification(
        user=user,
        title="✅ 주차 완료",
        message=f"A5 구역에 주차가 완료되었습니다! 점수: {complete_data['score']}점",
        notification_type='parking_complete',
        data=complete_data
    )
    results.append({'step': 'complete', 'status': 'success', 'notification_id': notification.id})
    
    return results


def _simulate_daily_usage(user, params):
    """일일 사용 패턴 시뮬레이션"""
    results = []
    delay = params.get('delay', 2)
    
    daily_notifications = [
        {
            'time': '09:00',
            'title': '🌅 굿모닝!',
            'message': '오늘도 안전한 주차되세요! 현재 주차장 여유 공간: 24개',
            'type': 'system'
        },
        {
            'time': '12:30',
            'title': '🍽️ 점심시간 알림',
            'message': '점심시간입니다. 주차장이 혼잡할 수 있으니 여유시간을 두고 이동하세요.',
            'type': 'system'
        },
        {
            'time': '18:00',
            'title': '🌆 퇴근시간 알림',
            'message': '퇴근 러시아워입니다. 주차 해제 전 주변을 확인하세요.',
            'type': 'system'
        },
        {
            'time': '22:00',
            'title': '🌙 일일 리포트',
            'message': '오늘 총 3회 주차했습니다. 평균 점수: 87점. 수고하셨습니다!',
            'type': 'system'
        }
    ]
    
    for i, notif_data in enumerate(daily_notifications):
        if i > 0:
            time.sleep(delay)
        
        extra_data = {
            'time_slot': notif_data['time'],
            'test': True,
            'scenario': 'daily_usage'
        }
        
        notification = create_notification(
            user=user,
            title=notif_data['title'],
            message=notif_data['message'],
            notification_type=notif_data['type'],
            data=extra_data
        )
        
        results.append({
            'time_slot': notif_data['time'],
            'status': 'success',
            'notification_id': notification.id
        })
    
    return results


def _simulate_emergency_alerts(user, params):
    """긴급 상황 알림 시뮬레이션"""
    results = []
    delay = params.get('delay', 1)
    
    emergency_alerts = [
        {
            'title': '🚨 긴급 알림',
            'message': '주차장 A구역에서 화재 경보가 발생했습니다. 즉시 대피하세요!',
            'type': 'system',
            'priority': 'critical'
        },
        {
            'title': '⚠️ 차량 이동 요청',
            'message': '긴급차량 진입으로 인해 차량 이동이 필요합니다. 협조 부탁드립니다.',
            'type': 'system',
            'priority': 'high'
        },
        {
            'title': '✅ 상황 종료',
            'message': '긴급상황이 해결되었습니다. 정상적인 주차장 이용이 가능합니다.',
            'type': 'system',
            'priority': 'normal'
        }
    ]
    
    for i, alert_data in enumerate(emergency_alerts):
        if i > 0:
            time.sleep(delay)
        
        extra_data = {
            'priority': alert_data['priority'],
            'emergency': True,
            'test': True,
            'scenario': 'emergency_alerts',
            'alert_sequence': i + 1
        }
        
        notification = create_notification(
            user=user,
            title=alert_data['title'],
            message=alert_data['message'],
            notification_type=alert_data['type'],
            data=extra_data
        )
        
        results.append({
            'priority': alert_data['priority'],
            'status': 'success',
            'notification_id': notification.id
        })
    
    return results


def _simulate_grade_progression(user, params):
    """등급 진행 시뮬레이션"""
    results = []
    delay = params.get('delay', 4)
    
    grade_progression = [
        ('초급자', '중급자', 60),
        ('중급자', '고급자', 75),
        ('고급자', '전문가', 85),
        ('전문가', '마스터', 95)
    ]
    
    current_score = user.score
    
    for old_grade, new_grade, required_score in grade_progression:
        if current_score < required_score:
            current_score = required_score + random.randint(1, 10)
        
        grade_data = {
            'old_grade': old_grade,
            'new_grade': new_grade,
            'current_score': current_score,
            'required_score': required_score,
            'upgrade_time': timezone.now().isoformat(),
            'test': True,
            'scenario': 'grade_progression'
        }
        
        notification = create_notification(
            user=user,
            title="🎉 등급 승급!",
            message=f"축하합니다! {old_grade}에서 {new_grade}로 승급했습니다! (점수: {current_score}점)",
            notification_type='grade_upgrade',
            data=grade_data
        )
        
        results.append({
            'upgrade': f"{old_grade} → {new_grade}",
            'score': current_score,
            'status': 'success',
            'notification_id': notification.id
        })
        
        time.sleep(delay)
        current_score += random.randint(5, 15)
    
    return results


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def test_status(request):
    """
    테스트 상태 및 통계 조회
    """
    user = request.user
    
    # 푸시 구독 상태
    subscriptions = PushSubscription.objects.filter(user=user)
    
    # 최근 24시간 테스트 알림 통계
    yesterday = timezone.now() - timedelta(days=1)
    test_notifications = Notification.objects.filter(
        user=user,
        created_at__gte=yesterday,
        data__test=True
    )
    
    # 타입별 통계
    type_stats = {}
    for notification in test_notifications:
        ntype = notification.notification_type
        type_stats[ntype] = type_stats.get(ntype, 0) + 1
    
    return Response({
        'user': {
            'email': user.email,
            'nickname': user.nickname,
            'push_enabled': user.push_enabled,
            'score': user.score
        },
        'push_subscriptions': {
            'count': subscriptions.count(),
            'endpoints': [s.endpoint[:50] + '...' for s in subscriptions[:3]]
        },
        'test_statistics': {
            'last_24h_notifications': test_notifications.count(),
            'by_type': type_stats,
            'latest_test': test_notifications.first().created_at.isoformat() if test_notifications.exists() else None
        },
        'available_scenarios': ['parking_flow', 'daily_usage', 'emergency_alerts', 'grade_progression'],
        'supported_notification_types': ['system', 'vehicle_entry', 'parking_complete', 'grade_upgrade', 'maintenance']
    })


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def clear_test_notifications(request):
    """
    테스트로 생성된 알림들을 모두 삭제
    """
    user = request.user
    
    # 테스트 태그가 있는 알림들 삭제
    deleted_count = Notification.objects.filter(
        user=user,
        data__test=True
    ).delete()[0]
    
    return Response({
        'message': f'{deleted_count}개의 테스트 알림이 삭제되었습니다.',
        'deleted_count': deleted_count
    })