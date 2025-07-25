# ocr_app/views.py
import asyncio  # noqa: F401

from django.http import StreamingHttpResponse  # type: ignore
from django.shortcuts import render  # type: ignore

from . import ocr  # 방금 만든 모듈


def index(request):
    return render(request, "index.html")


# async def annot_stream(request):
#     # 시작되지 않았으면 OCR 캡처 스레드 시작
#     ocr.start_capture()
#     boundary = b"--frame\r\n"

#     async def gen():
#         while True:
#             with ocr.frame_lock:
#                 chunk = ocr.latest_frame
#             if chunk:
#                 yield chunk
#             else:
#                 await asyncio.sleep(0.1)

#     return StreamingHttpResponse(
#         gen(), content_type="multipart/x-mixed-replace;boundary=frame"
#     )
