# streamapp\consumers.py
import asyncio
import json
import re
import sys

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from pywebpush import WebPushException, webpush

# ─── 전역 상태 ───────────────────────────────────────────────────────────
LATEST_TEXT = "번호판 인식 대기중"

# ─── 번호판 정규식 패턴 정의 ────────────────────────────────────────────────
KOREAN = (
    "가나다라마거너더러머버서어저"
    "고노도로모보소오조구누두루"
    "무부수우주아바사자허하호배"
)

plate_pattern = re.compile(
    rf"^(?:0[1-9]|[1-9]\d|[1-9]\d{{2}})"  # 01-99 또는 100-999
    rf"[{KOREAN}]"  # 한글 1자
    rf"[1-9]\d{{3}}$"  # 1000-9999
)


# ─── DB 접근 비동기 래퍼 ─────────────────────────────────────────────────
@database_sync_to_async
def lookup_vehicle_owner(plate):
    """
    차량 번호판으로 소유자 조회
    """
    from vehicles.models import Vehicle

    try:
        # User와 JOIN하여 한 번에 조회
        vehicle = Vehicle.objects.select_related("user").get(license_plate=plate)
        return vehicle.user, True
    except Vehicle.DoesNotExist:
        return None, False


@database_sync_to_async
def get_push_subscriptions(user):
    """
    사용자 푸시 구독 목록 조회
    """
    from accounts.models import PushSubscription

    if not user.push_enabled:
        return []  # 푸시 비활성 시 빈 목록 반환
    return list(PushSubscription.objects.filter(user=user))  # 구독 리스트


# ─── 푸시 발송 함수 ─────────────────────────────────────────────────────
def send_push(subscription, title, body):
    """
    웹푸시 전송
    """
    payload = json.dumps({"title": title, "body": body})  # 페이로드 생성
    try:
        webpush(
            subscription_info={
                "endpoint": subscription.endpoint,
                "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth},
            },
            data=payload,
            vapid_private_key=settings.VAPID_PRIVATE_KEY,  # VAPID 키
            vapid_claims=settings.VAPID_CLAIMS,
        )
    except WebPushException as ex:
        print(f"[PUSH ERROR] {ex}", file=sys.stderr)  # 오류 로깅


# ─── PiUploadConsumer: 라즈베리파이 → Django WebSocket ────────────────────
class PiUploadConsumer(AsyncWebsocketConsumer):
    """
    RPi에서 전송된 이미지/텍스트 수신 및 처리
    """

    last_entered = None  # 마지막 입차된 번호판 기록

    async def connect(self):
        print(f"[SERVER][PiUploadConsumer] connect: {self.channel_name}")
        await self.accept()  # WebSocket 연결 허용

    async def disconnect(self, code):
        print(f"[SERVER][PiUploadConsumer] disconnect code={code}")

    async def receive(self, text_data=None, bytes_data=None):
        global LATEST_TEXT
        payload = json.loads(text_data)  # JSON 파싱
        b64_img = payload.get("image")
        LATEST_TEXT = payload.get("text", "").strip()  # 텍스트 추출
        print(f"[SERVER][PiUploadConsumer] received text='{LATEST_TEXT}'")

        # 중복된 번호판: 입차된 차량 메시지 전송 후 종료
        if LATEST_TEXT == PiUploadConsumer.last_entered:
            # 화면에만 상태 메시지 갱신(브로드캐스트 그룹으로 전송)
            await self.channel_layer.group_send(
                "stream",
                {
                    "type": "new_frame",
                    "frame": b64_img,
                    "text": f"{LATEST_TEXT} 입차된 차량입니다.",
                },
            )
            return

        # 대기중/유효하지 않은 번호판: 그대로 전송 후 종료
        if LATEST_TEXT in ("번호판 인식 대기중", "유효하지 않은 번호판"):
            await self.channel_layer.group_send(
                "stream",
                {
                    "type": "new_frame",
                    "frame": b64_img,
                    "text": LATEST_TEXT,
                },
            )
            return

        # DB 조회: 차량→소유자
        user, exists = await lookup_vehicle_owner(LATEST_TEXT)
        # 화면 갱신 및 푸시 발송
        if exists:
            # 화면에 '입차:번호판' 전송
            await self.channel_layer.group_send(
                "stream",
                {"type": "new_frame", "frame": b64_img, "text": f"입차:{LATEST_TEXT}"},
            )
            # 사용자 푸시 구독 가져와 푸시 발송
            subs = await get_push_subscriptions(user)
            if subs:
                send_push(
                    subs[0],
                    title="차량 번호판 감지",
                    body=f"`{LATEST_TEXT}` 차량이 입차되었습니다.",
                )
        else:
            # 등록되지 않은 차량 알림
            print(f"[DEBUG][receive] 미등록 차량: {LATEST_TEXT}")
            await self.channel_layer.group_send(
                "stream",
                {
                    "type": "new_frame",
                    "frame": b64_img,
                    "text": "등록되지 않은 차량입니다",
                },
            )

        # 처리된 번호판 기록
        PiUploadConsumer.last_entered = LATEST_TEXT


# ─── StreamConsumer: 관리 화면용 WebSocket ─────────────────────────────────
class StreamConsumer(AsyncWebsocketConsumer):
    """
    관리자용 실시간 스트림 Consumer
    """

    async def connect(self):
        # 'stream' 그룹에 가입
        print(f"[SERVER][StreamConsumer] connect: {self.channel_name}")
        await self.channel_layer.group_add("stream", self.channel_name)  # 그룹 가입
        await self.accept()  # 연결 허용
        print("[SERVER][StreamConsumer] accepted")

    async def disconnect(self, code):
        print(f"[SERVER][StreamConsumer] disconnect code={code}")
        await self.channel_layer.group_discard("stream", self.channel_name)  # 그룹 탈퇴

    async def new_frame(self, event):
        # broadcast 받은 frame/text를 그대로 클라이언트로 전송
        print(f"[SERVER][StreamConsumer] new_frame event: {event['text'][:20]}…")
        await self.send(
            text_data=json.dumps(
                {
                    "image": event["frame"],
                    "text": event["text"],
                }
            )
        )  # 이벤트 전송


# ─── OCRTextConsumer: 텍스트 전용 푸시용 WebSocket ─────────────────────────
class OCRTextConsumer(AsyncWebsocketConsumer):
    """
    텍스트 전용 푸시용 Consumer
    """

    async def connect(self):
        await self.accept()  # 연결 허용
        self.task = asyncio.create_task(
            self.push_loop()
        )  # 주기적 텍스트 전송 태스크 시작

    async def disconnect(self, code):
        self.task.cancel()  # 태스크 취소

    async def push_loop(self):
        while True:
            await asyncio.sleep(0.5)  # 0.5초 대기
            is_valid_plate = bool(
                plate_pattern.match(LATEST_TEXT)
            )  # 번호판 유효성 검사
            returned_text = (
                f"입차: {LATEST_TEXT}" if is_valid_plate else "번호판 인식 대기중"
            )
            payload = json.dumps(
                {"text": returned_text}, ensure_ascii=False
            )  # JSON 페이로드 생성
            await self.send(text_data=payload)  # 클라이언트 전송
