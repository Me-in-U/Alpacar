# accounts/views/push.py
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from djangoApp import settings

from ..models import PushSubscription


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
