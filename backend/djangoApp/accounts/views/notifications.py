# accounts/views/notifications.py

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import Notification
from ..serializers.notifications import (
    NotificationSerializer,
    NotificationUpdateSerializer,
)


class NotificationPagination(PageNumberPagination):
    """
    알림 목록 페이지네이션
    """

    page_size = 20
    page_size_query_param = "page_size"
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
    notifications = Notification.objects.filter(user=user).order_by("-created_at")

    # 페이지네이션 적용
    paginator = NotificationPagination()
    page = paginator.paginate_queryset(notifications, request)

    if page is not None:
        serializer = NotificationSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    # 페이지네이션 없이 전체 조회
    serializer = NotificationSerializer(notifications, many=True)
    return Response({"count": len(notifications), "results": serializer.data})


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
        serializer = NotificationUpdateSerializer(
            notification, data=request.data, partial=True
        )
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
    return Response(
        {
            "message": f"{deleted_count}개의 알림이 삭제되었습니다.",
            "deleted_count": deleted_count,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def notification_mark_all_read(request):
    """
    사용자의 모든 알림을 읽음 상태로 변경
    """
    user = request.user
    updated_count = Notification.objects.filter(user=user, is_read=False).update(
        is_read=True
    )
    return Response(
        {
            "message": f"{updated_count}개의 알림이 읽음 처리되었습니다.",
            "updated_count": updated_count,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def notification_unread_count(request):
    """
    읽지 않은 알림 개수 조회
    """
    user = request.user
    unread_count = Notification.objects.filter(user=user, is_read=False).count()
    return Response({"unread_count": unread_count})
