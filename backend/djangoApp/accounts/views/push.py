# accounts/views/push.py
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import JsonResponse
import json
import logging

from djangoApp import settings

from ..models import PushSubscription

logger = logging.getLogger(__name__)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def push_setting(request):
    """
    푸시 설정 조회 및 저장 엔드포인트
    - GET: 현재 사용자 푸시 수신 설정(push_on)과 VAPID 공개키 반환
    - POST: 요청의 push_on 값으로 사용자 설정 저장 후 상태 반환
    """
    print(
        "[DEBUG] push_setting called with body:", request.data
    )  # DEBUG: 요청 본문 로깅
    user = request.user  # 인증된 사용자 객체
    if request.method == "GET":
        # GET 요청: 설정 정보 반환
        return Response(
            {
                "push_on": request.user.push_enabled,  # DB에 저장된 푸시 수신 설정 읽기
                "vapid_public_key": settings.VAPID_PUBLIC_KEY,  # VAPID 공개키 반환
            }
        )
    # POST 요청: 클라이언트에서 전달한 push_on 값으로 설정 업데이트
    on = request.data.get("push_on", False)
    user.push_enabled = bool(on)  # Boolean 형 변환 후 저장
    user.save()  # 변경된 설정 DB에 반영
    return Response({"push_on": user.push_enabled})  # 업데이트된 상태 반환


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def subscribe_push(request):
    """
    푸시 구독 정보 등록/업데이트 엔드포인트
    - request.data: { endpoint, keys: { p256dh, auth } }
    """
    print(
        "[DEBUG] subscribe_push called with body:", request.data
    )  # DEBUG: 요청 내용 로깅
    data = request.data  # 요청 데이터 추출
    # update_or_create: 기존 레코드 있으면 업데이트, 없으면 생성
    PushSubscription.objects.update_or_create(
        user=request.user,  # 현재 사용자와 매핑
        endpoint=data["endpoint"],  # 구독 endpoint
        defaults={
            "p256dh": data["keys"]["p256dh"],  # 공개 키
            "auth": data["keys"]["auth"],  # 인증 토큰
        },
    )
    return Response(status=status.HTTP_201_CREATED)  # 생성/업데이트 성공 응답


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def unsubscribe_push(request):
    """
    푸시 구독 해제 엔드포인트
    - request.data: { endpoint }
    """
    print(
        "[DEBUG] unsubscribe_push called with body:", request.data
    )  # DEBUG: 요청 본문 로깅
    endpoint = request.data.get("endpoint")  # 해제할 endpoint 추출
    # 해당 사용자와 endpoint를 가진 구독 레코드 삭제
    PushSubscription.objects.filter(user=request.user, endpoint=endpoint).delete()
    return Response(status=status.HTTP_204_NO_CONTENT)  # 삭제 성공 응답


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def test_push_notification(request):
    """
    테스트 푸시 알림 전송 엔드포인트
    - request.data: { title, body }
    """
    try:
        print(f"[DEBUG] test_push_notification called by user: {request.user.email}")
        
        # 사용자가 푸시 알림을 활성화했는지 확인
        if not request.user.push_enabled:
            print("[DEBUG] User has push notifications disabled")
            return Response(
                {"detail": "푸시 알림이 비활성화되어 있습니다."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 사용자의 구독 정보 확인
        subscriptions = PushSubscription.objects.filter(user=request.user)
        if not subscriptions.exists():
            print("[DEBUG] No push subscriptions found for user")
            return Response(
                {"detail": "푸시 구독 정보를 찾을 수 없습니다."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 요청 데이터 추출
        data = request.data
        title = data.get("title", "테스트 알림")
        body = data.get("body", "이것은 테스트 푸시 알림입니다.")
        
        print(f"[DEBUG] Sending test notification: {title} - {body}")
        
        # 실제 푸시 알림 전송 로직은 여기에 구현
        # pywebpush 라이브러리를 사용하여 실제 푸시 알림을 전송할 수 있습니다.
        
        # 현재는 로그만 출력하고 성공 응답 반환
        success_count = subscriptions.count()
        
        logger.info(f"Test push notification sent to user {request.user.email}: {title}")
        
        return Response({
            "message": "테스트 푸시 알림이 전송되었습니다.",
            "title": title,
            "body": body,
            "subscriptions_count": success_count
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"[DEBUG] Error in test_push_notification: {str(e)}")
        logger.error(f"Test push notification error for user {request.user.email}: {str(e)}")
        return Response(
            {"detail": "푸시 알림 전송 중 오류가 발생했습니다."}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
