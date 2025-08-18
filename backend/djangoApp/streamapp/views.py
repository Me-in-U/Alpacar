# streamapp\views.py
import base64
import time
from threading import Lock

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response

# ─── 전역 캐시 & 동기화 ───────────────────────────────────────────────
latest_frame = None  # JPEG 바이너리
latest_text = ""  # 번호판 텍스트
cache_lock = Lock()  # 쓰레드 안전을 위한 Lock


# ─── Raspberry Pi → POST 수신 핸들러 ───────────────────────────────────
@api_view(["POST"])
def upload_frame(request):
    """
    Raspberry Pi에서 POST된 이미지와 텍스트 수신
    - 최신 프레임/텍스트 전역 변수에 저장
    - Channels 'stream' 그룹에 WebSocket 메시지 전송
    """
    global latest_frame, latest_text

    img_file = request.FILES.get("image")  # 업로드된 이미지 파일
    plate_text = request.POST.get("plate_text", "")  # 전송된 번호판 텍스트

    if img_file:
        data = img_file.read()

        # 최신 프레임/텍스트 캐시에 저장 (스레드 안전)
        with cache_lock:
            latest_frame = data
            latest_text = plate_text
            print(f"[INFO] 수신된 텍스트: {latest_text}")

        # base64 인코딩 후 WebSocket 그룹에 전송
        b64_frame = base64.b64encode(data).decode()
        channel_layer = get_channel_layer()  # 채널 레이어 인스턴스
        async_to_sync(channel_layer.group_send)(
            "stream",
            {
                "type": "new_frame",  # 메시지 핸들러 메서드
                "frame": b64_frame,  # base64 이미지
                "text": latest_text,  # 텍스트
            },
        )  # 비동기 호출을 동기화하여 실행

    return Response({"status": "ok"})
