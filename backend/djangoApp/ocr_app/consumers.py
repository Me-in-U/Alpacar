# ocr_app/consumers.py
import asyncio
import json

from channels.generic.websocket import AsyncWebsocketConsumer

from . import ocr


class OCRTextConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self._send_text(ocr.last_text)
        self.task = asyncio.create_task(self.push_loop())

    async def push_loop(self):
        prev = ocr.last_text
        while True:
            await asyncio.sleep(0.05)
            with ocr.text_lock:
                curr = ocr.last_text
            if curr != prev:
                await self._send_text(curr)
                prev = curr

    # 한글 그대로 보내는 헬퍼
    async def _send_text(self, text: str):
        payload = json.dumps({"text": text}, ensure_ascii=False)
        await self.send(text_data=payload)


# 새로 추가: binary frame 전송용 소비자
class OcrImageConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # WebSocket 열리면 OCR 캡처도 시작
        ocr.start_capture()
        await self.accept()
        self.task = asyncio.create_task(self.send_loop())

    async def disconnect(self, code):
        if hasattr(self, "task"):
            self.task.cancel()

    async def send_loop(self):
        prev = None
        while True:
            await asyncio.sleep(0.05)
            with ocr.frame_lock:
                frame = ocr.latest_frame
            if frame and frame != prev:
                # boundary, headers 분리 → 순수 JPEG 바이트만 전송
                raw = frame.split(b"\r\n\r\n", 1)[1]
                jpg = raw[:-2]
                # Channels 4.x: send(bytes_data=…) 로 맞춰야 바이너리 전송
                await self.send(bytes_data=jpg)
                prev = frame
