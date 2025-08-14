# events/consumers.py (개선본 A)
from __future__ import annotations

import logging
from typing import Any, Dict

from channels.generic.websocket import AsyncJsonWebsocketConsumer

logger = logging.getLogger(__name__)

PARKING_LOG_GROUP = "parking_logs"


class ParkingLogConsumer(AsyncJsonWebsocketConsumer):
    """
    실시간 주차 로그를 구독하는 WebSocket Consumer.
    - 연결 시 공용 그룹에 조인
    - 서버 측 브로드캐스트(vehicle_event)를 JSON으로 그대로 전달
    - 클라이언트 → 서버 입력은 차단(옵션)
    """

    group_name: str = PARKING_LOG_GROUP

    async def connect(self) -> None:
        # 인증이 필요한 경우(선택): 미인증이면 거절
        user = self.scope.get("user")
        if user is not None and hasattr(user, "is_authenticated"):
            if not user.is_authenticated:
                logger.warning(
                    "Unauthenticated WS connection blocked: %s", self.channel_name
                )
                await self.close(code=4401)  # 4401: custom unauthorized
                return

        logger.debug(
            "WS connect: channel=%s, group=%s", self.channel_name, self.group_name
        )
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code: int) -> None:
        logger.debug(
            "WS disconnect: channel=%s, code=%s", self.channel_name, close_code
        )
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # 그룹으로부터 이벤트 수신 (Channels 이벤트 타입: "vehicle.event" → 메서드명 vehicle_event)
    async def vehicle_event(self, event: Dict[str, Any]) -> None:
        """
        기대 이벤트 포맷:
        {
            "type": "vehicle.event",
            "payload": {...}  # dict(JSON 직렬화 가능)
        }
        """
        payload = event.get("payload", {})
        logger.debug(
            "WS vehicle_event: channel=%s, keys=%s",
            self.channel_name,
            list(payload.keys()),
        )
        await self.send_json(payload)

    # 클라이언트 → 서버 입력 차단(원치 않으면 제거)
    async def receive_json(self, content: Any, **kwargs: Any) -> None:
        logger.warning("Client message rejected (read-only channel): %s", content)
        # 필요 시 에러 응답 전송
        await self.send_json({"error": "read-only channel"})
