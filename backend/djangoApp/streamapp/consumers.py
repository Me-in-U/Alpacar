import asyncio
import json
import os
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
def get_member_qs(plate):
    # plate_number 기준으로 Member queryset 조회
    from accounts.models import Member

    qs = Member.objects.filter(plate_number=plate)
    return list(qs), qs.exists()


@database_sync_to_async
def get_push_subs(qs):
    # members 리스트 중 push_enabled=True인 사용자만 필터
    from accounts.models import PushSubscription

    users = [m for m in qs if m.push_enabled]
    return list(PushSubscription.objects.filter(user__in=users))


# ─── 푸시 발송 함수 ─────────────────────────────────────────────────────
def send_push(subscription, title, body):
    payload = json.dumps({"title": title, "body": body})
    print(
        f"[DEBUG][send_push] to={subscription.user_id} endpoint={subscription.endpoint}"
    )
    try:
        webpush(
            subscription_info={
                "endpoint": subscription.endpoint,
                "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth},
            },
            data=payload,
            vapid_private_key=settings.VAPID_PRIVATE_KEY,
            vapid_claims=settings.VAPID_CLAIMS,
        )
        print(f"[DEBUG][send_push] SUCCESS for {subscription.user_id}")
    except WebPushException as ex:
        print(f"[PUSH ERROR] {ex}", file=sys.stderr)


# ─── PiUploadConsumer: 라즈베리파이 → Django WebSocket ────────────────────
class PiUploadConsumer(AsyncWebsocketConsumer):
    """
    라즈베리파이 → Django WebSocket (ws://…/ws/upload/)
    에 연결해서 JSON {image: base64, text: ...} 을 받습니다.
    """

    last_entered = None

    async def connect(self):
        await self.accept()  # 연결 허용

    async def disconnect(self, code):
        pass  # 특별한 처리 없음

    async def receive(self, text_data=None, bytes_data=None):
        global LATEST_TEXT

        # JSON 파싱 & 텍스트 strip
        payload = json.loads(text_data)
        b64_img = payload.get("image")
        LATEST_TEXT = payload.get("text", "").strip()

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

        # DB 조회: 멤버 리스트 & 존재 여부
        member_list, exists = await get_member_qs(LATEST_TEXT)
        print(f"[DEBUG][receive] exists={exists}, member_count={len(member_list)}")

        # 화면 갱신 및 푸시 발송
        if exists:
            # 화면에 '입차:번호판' 전송
            await self.channel_layer.group_send(
                "stream",
                {"type": "new_frame", "frame": b64_img, "text": f"입차:{LATEST_TEXT}"},
            )
            # 구독자 조회
            subs = await get_push_subs(
                member_list
            )  # 이제 subs는 list[PushSubscription]
            print(f"[DEBUG][receive] subs_count={len(subs)}")
            # 첫 구독자에게만 푸시 발송
            if subs:
                print(f"[DEBUG][receive] send_push 호출 -> user_id={subs[0].user_id}")
                send_push(
                    subs[0],
                    title="차량 번호판 감지",
                    body=f"`{LATEST_TEXT}` 차량이 감지되었습니다.",
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
    관리자용 Consumer (ws://…/ws/stream/)
    group 'stream' 가입 → new_frame 이벤트 받으면 클라이언트로 전송
    """

    async def connect(self):
        # 'stream' 그룹에 가입
        await self.channel_layer.group_add("stream", self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard("stream", self.channel_name)

    async def new_frame(self, event):
        # broadcast 받은 frame/text를 그대로 클라이언트로 전송
        await self.send(
            text_data=json.dumps(
                {
                    "image": event["frame"],
                    "text": event["text"],
                }
            )
        )


# ─── OCRTextConsumer: 텍스트 전용 푸시용 WebSocket ─────────────────────────
class OCRTextConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        # 0.5초마다 LATEST_TEXT 전송하는 백그라운드 태스크 시작
        self.task = asyncio.create_task(self.push_loop())

    async def disconnect(self, code):
        # 태스크 취소
        self.task.cancel()

    async def push_loop(self):
        while True:
            await asyncio.sleep(0.5)
            # 입차 상태인지 검사
            is_valid_plate = bool(plate_pattern.match(LATEST_TEXT))
            returned_text = (
                f"입차: {LATEST_TEXT}" if is_valid_plate else "번호판 인식 대기중"
            )
            payload = json.dumps({"text": returned_text}, ensure_ascii=False)
            await self.send(text_data=payload)
