# jetson/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from parking.services import handle_assignment_from_jetson, add_score_from_jetson

JETSON_GROUP = "jetson"  # 장고→젯슨 요청 broadcast 그룹


class JetsonAssignConsumer(AsyncWebsocketConsumer):
    """
    Jetson이 이 WS에 붙는다.
    - 장고가 group_send("jetson", {"type":"jetson.request", payload})로 요청을 내리면 → 그대로 send
    - Jetson이 {"message_type":"assignment", "license_plate", "assignment":"B3"}를 보내면 → DB 반영
    """

    async def connect(self):
        await self.accept()
        await self.channel_layer.group_add(JETSON_GROUP, self.channel_name)
        # 필요시 인증/토큰 검증 로직 추가 가능

    async def disconnect(self, code):
        await self.channel_layer.group_discard(JETSON_GROUP, self.channel_name)

    # 장고→젯슨 브로드캐스트 훅
    async def jetson_request(self, event):
        # event = {"type":"jetson_request", "payload": {...}}
        await self.send(text_data=json.dumps(event["payload"], ensure_ascii=False))

    # 젯슨→장고 결과 수신
    async def receive(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data or "{}")
        except Exception:
            return

        message_type = data.get("message_type")

        if message_type == "assignment":
            plate = data.get("license_plate")
            slot_label = data.get("assignment")
            if plate and slot_label:
                ok, msg = await database_sync_to_async(handle_assignment_from_jetson)(
                    plate, slot_label
                )
                await self.send(
                    text_data=json.dumps(
                        {
                            "message_type": "assignment_ack",
                            "license_plate": plate,
                            "assignment": slot_label,
                            "status": "success" if ok else "error",
                            "detail": msg,
                        },
                        ensure_ascii=False,
                    )
                )

        elif message_type == "score":
            plate = data.get("license_plate")
            score = data.get("score")
            if plate is None or score is None:
                await self.send(
                    text_data=json.dumps(
                        {
                            "message_type": "score_ack",
                            "status": "error",
                            "detail": "license_plate and score required",
                        },
                        ensure_ascii=False,
                    )
                )
                return
            try:
                score = int(score)
            except Exception:
                await self.send(
                    text_data=json.dumps(
                        {
                            "message_type": "score_ack",
                            "status": "error",
                            "detail": "score must be integer",
                        },
                        ensure_ascii=False,
                    )
                )
                return

            ok, msg = await database_sync_to_async(add_score_from_jetson)(plate, score)
            await self.send(
                text_data=json.dumps(
                    {
                        "message_type": "score_ack",
                        "license_plate": plate,
                        "score": score,
                        "status": "success" if ok else "error",
                        "detail": msg,
                    },
                    ensure_ascii=False,
                )
            )
