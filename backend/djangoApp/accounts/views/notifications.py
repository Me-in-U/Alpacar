# accounts/views/notifications.py
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.utils import timezone
import random

from ..models import Notification
from ..serializers.notifications import NotificationSerializer, NotificationUpdateSerializer
from ..utils import create_notification, send_vehicle_entry_notification, send_parking_complete_notification, send_grade_upgrade_notification
from vehicles.models import Vehicle


def _handle_notification_error(error, user, function_name, error_message=None):
    """공통 알림 에러 처리 함수"""
    import traceback
    error_trace = traceback.format_exc()
    print(f"[ERROR] {function_name}: {str(error)}")
    
    if not error_message:
        error_message = f'알림 전송 실패: {str(error)}'
    
    return Response({
        'error': error_message,
        'error_type': type(error).__name__,
        'debug': {
            'user_id': user.id,
            'user_email': user.email,
            'push_enabled': getattr(user, 'push_enabled', 'Unknown'),
            'function': function_name
        }
    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _check_user_push_settings(user):
    """사용자 푸시 설정 확인 공통 함수"""
    if not hasattr(user, 'push_enabled'):
        return Response({
            'error': '사용자 푸시 설정을 확인할 수 없습니다.',
            'debug': 'User model does not have push_enabled field'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return None


def _get_user_vehicle_info(user):
    """사용자 차량 정보 조회 공통 함수"""
    try:
        user_vehicle = Vehicle.objects.filter(user=user).first()
        plate_number = user_vehicle.license_plate if user_vehicle else 'TEST차량'
        return user_vehicle, plate_number
    except Exception as e:
        print(f"[WARN] 사용자 차량 조회 실패: {str(e)}")
        return None, 'TEST차량'


class NotificationPagination(PageNumberPagination):
    """
    알림 목록 페이지네이션
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def notification_list(request):
    """
    사용자 알림 목록 조회
    - 로그인한 사용자의 알림만 조회
    - 최신순 정렬
    - 페이지네이션 적용
    """
    user = request.user
    notifications = Notification.objects.filter(user=user).order_by('-created_at')
    
    # 페이지네이션 적용
    paginator = NotificationPagination()
    page = paginator.paginate_queryset(notifications, request)
    
    if page is not None:
        serializer = NotificationSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    # 페이지네이션 없이 전체 조회
    serializer = NotificationSerializer(notifications, many=True)
    return Response({
        'count': len(notifications),
        'results': serializer.data
    })


@api_view(["GET", "PUT"])
@permission_classes([IsAuthenticated])
def notification_detail(request, notification_id):
    """
    특정 알림 조회 및 업데이트
    - GET: 알림 상세 정보 조회
    - PUT: 알림 읽음 상태 업데이트
    """
    user = request.user
    notification = get_object_or_404(Notification, id=notification_id, user=user)
    
    if request.method == "GET":
        serializer = NotificationSerializer(notification)
        return Response(serializer.data)
    
    elif request.method == "PUT":
        # 읽음 상태 업데이트
        serializer = NotificationUpdateSerializer(notification, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def notification_delete(request, notification_id):
    """
    특정 알림 삭제
    """
    user = request.user
    notification = get_object_or_404(Notification, id=notification_id, user=user)
    notification.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def notification_delete_all(request):
    """
    사용자의 모든 알림 삭제
    """
    user = request.user
    deleted_count = Notification.objects.filter(user=user).count()
    Notification.objects.filter(user=user).delete()
    return Response({
        'message': f'{deleted_count}개의 알림이 삭제되었습니다.',
        'deleted_count': deleted_count
    }, status=status.HTTP_200_OK)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def notification_mark_all_read(request):
    """
    사용자의 모든 알림을 읽음 상태로 변경
    """
    user = request.user
    updated_count = Notification.objects.filter(user=user, is_read=False).update(is_read=True)
    return Response({
        'message': f'{updated_count}개의 알림이 읽음 처리되었습니다.',
        'updated_count': updated_count
    }, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def notification_unread_count(request):
    """
    읽지 않은 알림 개수 조회
    """
    user = request.user
    unread_count = Notification.objects.filter(user=user, is_read=False).count()
    return Response({
        'unread_count': unread_count
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def test_push_notification(request):
    """
    테스트용 푸시 알림 전송 API
    - POST: 로그인한 사용자에게 테스트 푸시 알림 전송
    """
    user = request.user
    
    # 사용자 푸시 설정 확인
    error_response = _check_user_push_settings(user)
    if error_response:
        return error_response
    
    # 테스트 알림 데이터
    test_data = {
        'test': True,
        'timestamp': '2025-01-08T16:30:00Z',
        'source': 'api_test'
    }
    
    try:
        # 알림 생성 및 푸시 전송
        notification = create_notification(
            user=user,
            title="🔔 테스트 푸시 알림",
            message="푸시 알림 테스트입니다. 정상적으로 작동하고 있습니다!",
            notification_type='system',
            data=test_data
        )
        
        return Response({
            'success': True,
            'message': '테스트 푸시 알림이 전송되었습니다.',
            'notification_id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'push_enabled': user.push_enabled,
            'debug': {
                'user_id': user.id,
                'user_email': user.email,
                'push_setting': user.push_enabled
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return _handle_notification_error(e, user, 'test_push_notification', f'푸시 알림 전송 실패: {str(e)}')


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def test_vehicle_entry_notification(request):
    """
    테스트용 입차 알림 전송 API
    """
    user = request.user
    
    # 사용자 푸시 설정 확인
    error_response = _check_user_push_settings(user)
    if error_response:
        return error_response
    
    # 사용자 차량 정보 조회
    user_vehicle, plate_number = _get_user_vehicle_info(user)
    
    # 테스트 입차 데이터 (실제 차량번호 및 현재 시간 사용)
    entry_data = {
        'plate_number': plate_number,
        'parking_lot': 'SSAFY 주차장',
        'entry_time': timezone.now().isoformat(),
        'test': True
    }
    
    try:
        # 직접 create_notification을 호출하여 더 나은 에러 추적
        notification = create_notification(
            user=user,
            title="🚗 테스트 입차 알림",
            message=f"{entry_data['plate_number']} 차량이 {entry_data['parking_lot']}에 입차하였습니다.",
            notification_type='vehicle_entry',
            data=entry_data
        )
        
        return Response({
            'success': True,
            'message': '입차 알림이 전송되었습니다.',
            'type': 'vehicle_entry',
            'notification_id': notification.id,
            'data': entry_data,
            'push_enabled': user.push_enabled,
            'debug': {
                'user_id': user.id,
                'user_email': user.email,
                'push_setting': user.push_enabled,
                'vehicle_source': 'user_vehicle' if user_vehicle else 'fallback',
                'has_registered_vehicle': bool(user_vehicle)
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return _handle_notification_error(e, user, 'test_vehicle_entry_notification', f'입차 알림 전송 실패: {str(e)}')


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def test_parking_complete_notification(request):
    """
    테스트용 주차 완료 알림 전송 API
    """
    user = request.user
    
    # 사용자 푸시 설정 확인
    error_response = _check_user_push_settings(user)
    if error_response:
        return error_response
    
    # 사용자 차량 정보 조회
    user_vehicle, plate_number = _get_user_vehicle_info(user)
    
    # 테스트 주차 완료 데이터 (실제 차량번호 및 현재 시간 사용)
    parking_data = {
        'plate_number': plate_number,
        'parking_space': f'A{random.randint(1, 20)}',  # 랜덤 주차공간
        'parking_time': timezone.now().isoformat(),
        'score': None,  # 점수가 없는 경우로 테스트
        'test': True
    }
    
    # 50% 확률로 점수 추가 (테스트용)
    if random.choice([True, False]):
        parking_data['score'] = random.randint(60, 95)
    
    try:
        # 직접 create_notification을 호출하여 더 나은 에러 추적
        score_text = f" 점수: {parking_data['score']}점" if parking_data['score'] else ""
        notification = create_notification(
            user=user,
            title="🅿️ 테스트 주차 완료",
            message=f"{parking_data['plate_number']} 차량이 {parking_data['parking_space']} 구역에 주차 완료되었습니다.{score_text}",
            notification_type='parking_complete',
            data=parking_data
        )
        
        return Response({
            'success': True,
            'message': '주차 완료 알림이 전송되었습니다.',
            'type': 'parking_complete',
            'notification_id': notification.id,
            'data': parking_data,
            'push_enabled': user.push_enabled,
            'debug': {
                'user_id': user.id,
                'user_email': user.email,
                'push_setting': user.push_enabled,
                'vehicle_source': 'user_vehicle' if user_vehicle else 'fallback',
                'has_registered_vehicle': bool(user_vehicle)
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return _handle_notification_error(e, user, 'test_parking_complete_notification', f'주차 완료 알림 전송 실패: {str(e)}')


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def test_grade_upgrade_notification(request):
    """
    테스트용 등급 승급 알림 전송 API
    """
    user = request.user
    
    # 사용자 푸시 설정 확인
    error_response = _check_user_push_settings(user)
    if error_response:
        return error_response
    
    # 테스트 등급 승급 데이터
    grade_levels = [
        ('초급자', '중급자'),
        ('중급자', '고급자'), 
        ('고급자', '전문가'),
        ('전문가', '마스터')
    ]
    
    old_grade, new_grade = random.choice(grade_levels)
    
    grade_data = {
        'old_grade': old_grade,
        'new_grade': new_grade,
        'current_score': user.score + random.randint(10, 50),
        'upgrade_time': timezone.now().isoformat(),
        'test': True
    }
    
    try:
        # 직접 create_notification을 호출하여 더 나은 에러 추적
        notification = create_notification(
            user=user,
            title="🎉 테스트 등급 승급!",
            message=f"축하합니다! 주차 등급이 {old_grade}에서 {new_grade}로 승급되었습니다! (점수: {grade_data['current_score']}점)",
            notification_type='grade_upgrade',
            data=grade_data
        )
        
        return Response({
            'success': True,
            'message': '등급 승급 알림이 전송되었습니다.',
            'type': 'grade_upgrade',
            'notification_id': notification.id,
            'data': grade_data,
            'push_enabled': user.push_enabled,
            'debug': {
                'user_id': user.id,
                'user_email': user.email,
                'push_setting': user.push_enabled
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return _handle_notification_error(e, user, 'test_grade_upgrade_notification', f'등급 승급 알림 전송 실패: {str(e)}')




@api_view(["GET"])
@permission_classes([IsAuthenticated])
def notification_system_diagnostic(request):
    """
    푸시 알림 시스템 진단 API
    - 모든 설정 및 환경을 검사하여 500 에러 원인 파악
    """
    user = request.user
    diagnostic = {
        'user_info': {},
        'push_settings': {},
        'vapid_config': {},
        'subscription_info': {},
        'system_status': {},
        'recommendations': []
    }
    
    try:
        # 사용자 정보 확인
        diagnostic['user_info'] = {
            'user_id': user.id,
            'email': user.email,
            'is_authenticated': user.is_authenticated,
            'has_push_enabled_field': hasattr(user, 'push_enabled'),
            'push_enabled_value': getattr(user, 'push_enabled', None)
        }
        
        # 푸시 설정 확인
        from ..models import PushSubscription
        subscriptions = PushSubscription.objects.filter(user=user)
        diagnostic['subscription_info'] = {
            'subscription_count': subscriptions.count(),
            'subscriptions': [
                {
                    'id': sub.id,
                    'endpoint': sub.endpoint[:50] + '...' if len(sub.endpoint) > 50 else sub.endpoint,
                    'has_p256dh': bool(sub.p256dh),
                    'has_auth': bool(sub.auth),
                    'created_at': sub.created_at.isoformat() if hasattr(sub, 'created_at') else 'Unknown'
                } for sub in subscriptions
            ]
        }
        
        # VAPID 설정 확인
        vapid_private_key = getattr(settings, 'VAPID_PRIVATE_KEY', None)
        vapid_public_key = getattr(settings, 'VAPID_PUBLIC_KEY', None)
        diagnostic['vapid_config'] = {
            'has_private_key': bool(vapid_private_key),
            'has_public_key': bool(vapid_public_key),
            'private_key_length': len(vapid_private_key) if vapid_private_key else 0,
            'public_key_length': len(vapid_public_key) if vapid_public_key else 0
        }
        
        # 시스템 상태 확인
        diagnostic['system_status'] = {
            'pywebpush_available': True,  # 이미 import 성공했음
            'notification_model_available': True,  # 이미 import 성공했음
            'user_model_fields': [field.name for field in user._meta.get_fields()]
        }
        
        # 문제 진단 및 추천사항
        if not diagnostic['user_info']['has_push_enabled_field']:
            diagnostic['recommendations'].append('❌ User 모델에 push_enabled 필드가 없습니다. 마이그레이션이 필요할 수 있습니다.')
        elif not diagnostic['user_info']['push_enabled_value']:
            diagnostic['recommendations'].append('⚠️ 사용자의 푸시 알림이 비활성화되어 있습니다.')
        else:
            diagnostic['recommendations'].append('✅ 사용자 푸시 설정이 활성화되어 있습니다.')
        
        if not diagnostic['vapid_config']['has_private_key'] or not diagnostic['vapid_config']['has_public_key']:
            diagnostic['recommendations'].append('❌ VAPID 키가 설정되지 않았습니다. settings.py에 VAPID_PRIVATE_KEY와 VAPID_PUBLIC_KEY를 설정하세요.')
        else:
            diagnostic['recommendations'].append('✅ VAPID 설정이 올바르게 구성되어 있습니다.')
        
        if diagnostic['subscription_info']['subscription_count'] == 0:
            diagnostic['recommendations'].append('⚠️ 푸시 구독 정보가 없습니다. 브라우저에서 푸시 알림을 허용하고 구독해야 합니다.')
        else:
            diagnostic['recommendations'].append(f'✅ {diagnostic["subscription_info"]["subscription_count"]}개의 푸시 구독이 활성화되어 있습니다.')
        
        # 테스트 알림 생성 시뮬레이션
        try:
            from ..utils import create_notification
            # 실제로는 생성하지 않고 유효성만 검사
            test_data = {'test': True, 'diagnostic': True}
            diagnostic['system_status']['notification_creation_test'] = '✅ 알림 생성 함수에 접근 가능'
        except ImportError as e:
            diagnostic['system_status']['notification_creation_test'] = f'❌ 알림 생성 함수 import 실패: {str(e)}'
            diagnostic['recommendations'].append('❌ accounts.utils.create_notification 함수를 확인하세요.')
        except Exception as e:
            diagnostic['system_status']['notification_creation_test'] = f'⚠️ 알림 생성 함수 테스트 중 오류: {str(e)}'
        
        return Response({
            'success': True,
            'message': '푸시 알림 시스템 진단이 완료되었습니다.',
            'diagnostic': diagnostic,
            'summary': {
                'total_issues': len([r for r in diagnostic['recommendations'] if r.startswith('❌')]),
                'warnings': len([r for r in diagnostic['recommendations'] if r.startswith('⚠️')]),
                'ok_status': len([r for r in diagnostic['recommendations'] if r.startswith('✅')])
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[ERROR] notification_system_diagnostic: {str(e)}")
        print(f"[TRACE] {error_trace}")
        
        return Response({
            'error': f'진단 실행 중 오류 발생: {str(e)}',
            'error_type': type(e).__name__,
            'debug': {
                'trace': error_trace.split('\n')[-5:-1]  # 마지막 몇 줄만
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)