# accounts/views/notifications.py
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404

from ..models import Notification
from ..serializers.notifications import NotificationSerializer, NotificationUpdateSerializer
from ..utils import create_notification, send_vehicle_entry_notification, send_parking_complete_notification, send_grade_upgrade_notification


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
            'message': '테스트 푸시 알림이 전송되었습니다.',
            'notification_id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'push_enabled': user.push_enabled
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': f'푸시 알림 전송 실패: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def test_vehicle_entry_notification(request):
    """
    테스트용 입차 알림 전송 API
    """
    user = request.user
    
    # 테스트 입차 데이터
    entry_data = {
        'plate_number': '220로1284',
        'parking_lot': 'SSAFY 주차장',
        'entry_time': '2025-01-08T10:30:00Z',
        'test': True
    }
    
    try:
        send_vehicle_entry_notification(user, entry_data)
        
        return Response({
            'message': '입차 알림이 전송되었습니다.',
            'type': 'vehicle_entry',
            'data': entry_data
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': f'입차 알림 전송 실패: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def test_parking_complete_notification(request):
    """
    테스트용 주차 완료 알림 전송 API
    """
    user = request.user
    
    # 테스트 주차 완료 데이터
    parking_data = {
        'plate_number': '220로1284',
        'parking_space': 'A5',
        'parking_time': '2025-01-08T10:45:00Z',
        'score': None,  # 점수가 없는 경우로 테스트
        'test': True
    }
    
    # 50% 확률로 점수 추가 (테스트용)
    import random
    if random.choice([True, False]):
        parking_data['score'] = random.randint(60, 95)
    
    try:
        send_parking_complete_notification(user, parking_data)
        
        return Response({
            'message': '주차 완료 알림이 전송되었습니다.',
            'type': 'parking_complete',
            'data': parking_data
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': f'주차 완료 알림 전송 실패: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def test_grade_upgrade_notification(request):
    """
    테스트용 등급 승급 알림 전송 API
    """
    user = request.user
    
    # 테스트 등급 승급 데이터
    grade_levels = [
        ('초급자', '중급자'),
        ('중급자', '고급자'), 
        ('고급자', '전문가'),
        ('전문가', '마스터')
    ]
    
    import random
    old_grade, new_grade = random.choice(grade_levels)
    
    grade_data = {
        'old_grade': old_grade,
        'new_grade': new_grade,
        'current_score': user.score + random.randint(10, 50),
        'upgrade_time': '2025-01-08T11:00:00Z',
        'test': True
    }
    
    try:
        send_grade_upgrade_notification(user, grade_data)
        
        return Response({
            'message': '등급 승급 알림이 전송되었습니다.',
            'type': 'grade_upgrade',
            'data': grade_data
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': f'등급 승급 알림 전송 실패: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def test_all_notifications(request):
    """
    모든 알림 타입을 순차적으로 테스트하는 API
    """
    user = request.user
    results = []
    
    try:
        # 1. 입차 알림
        entry_data = {
            'plate_number': '220로1284',
            'parking_lot': 'SSAFY 주차장',
            'entry_time': '2025-01-08T10:30:00Z',
            'test': True
        }
        send_vehicle_entry_notification(user, entry_data)
        results.append({'type': 'vehicle_entry', 'status': 'success'})
        
        # 2. 주차 완료 알림 (3초 후)
        import time
        time.sleep(3)
        
        parking_data = {
            'plate_number': '220로1284',
            'parking_space': 'A5',
            'parking_time': '2025-01-08T10:45:00Z',
            'score': 85,
            'test': True
        }
        send_parking_complete_notification(user, parking_data)
        results.append({'type': 'parking_complete', 'status': 'success'})
        
        # 3. 등급 승급 알림 (3초 후)
        time.sleep(3)
        
        grade_data = {
            'old_grade': '중급자',
            'new_grade': '고급자',
            'current_score': user.score + 25,
            'upgrade_time': '2025-01-08T11:00:00Z',
            'test': True
        }
        send_grade_upgrade_notification(user, grade_data)
        results.append({'type': 'grade_upgrade', 'status': 'success'})
        
        return Response({
            'message': '모든 알림이 순차적으로 전송되었습니다.',
            'results': results,
            'total_sent': len(results)
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': f'알림 전송 실패: {str(e)}',
            'results': results
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)