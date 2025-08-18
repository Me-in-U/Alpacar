# cd backend\ocr
# python ocr.py

import eventlet

eventlet.monkey_patch()

import sys
import threading
import time

import cv2
import easyocr
import numpy as np
from flask import Flask, Response, stream_with_context
from flask_sock import Sock
from PIL import Image, ImageDraw, ImageFont
from ultralytics import YOLO

app = Flask(__name__)
sock = Sock(app)

# === 모델 및 OCR 초기화 ===
model = YOLO("weights/best.pt").to("cuda:0")
reader = easyocr.Reader(["ko"], gpu=True)
font = ImageFont.truetype("NanumGothic-Regular.ttf", size=70)

# === 전역 상태 ===
CAM_STREAM_URL = "http://192.168.8.253:5000/stream"
latest_frame = None
frame_lock = threading.Lock()
last_text = ""
text_lock = threading.Lock()


def capture_loop():
    """
    1) MJPEG 스트림에서 프레임 읽기
    2) 박스+텍스트 어노테이트 & OCR
    3) JPEG으로 인코딩 → latest_frame에 캐시
    4) 텍스트가 변경되면 last_text 갱신
    """
    global latest_frame, last_text

    while True:
        cap = cv2.VideoCapture(CAM_STREAM_URL)
        cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 2000)
        cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 2000)
        if not cap.isOpened():
            print(f"[ERROR] CAM_STREAM 연결 실패 → {CAM_STREAM_URL}", file=sys.stderr)
            time.sleep(2)
            print("[INFO] 2초 후 재연결 시도합니다...", file=sys.stderr)
            continue

        boundary = b"--frame\r\n"
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[WARN] 프레임 읽기 실패, 캡처 재시작", file=sys.stderr)
                cap.release()
                break  # 내부 루프 탈출해서 바깥에서 재연결 시도

            # --- OCR & 어노테이트 ---
            res = model.predict(frame, conf=0.4, device="cuda:0", verbose=False)[
                0
            ].boxes
            boxes = res.xyxy.cpu().numpy()
            scores = res.conf.cpu().numpy()

            pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            draw = ImageDraw.Draw(pil)
            text = "인식대기중"

            if scores.size and scores.max() > 0.4:
                i = np.argmax(scores)
                x1, y1, x2, y2 = boxes[i].astype(int)
                roi = frame[y1:y2, x1:x2]
                gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                blur = cv2.medianBlur(gray, 3)
                result = reader.readtext(blur, detail=1, paragraph=False)
                text = " ".join([t for _, t, p in result if p > 0.5])
                draw.rectangle([x1, y1, x2, y2], outline="lime", width=3)
                draw.text((x1, y1 - 30), text, font=font, fill="lime")

            # --- JPEG 인코딩 & 캐시 ---
            annotated = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
            ok, buf = cv2.imencode(".jpg", annotated)
            if ok:
                jpg = (
                    boundary
                    + b"Content-Type: image/jpeg\r\n\r\n"
                    + buf.tobytes()
                    + b"\r\n"
                )
                with frame_lock:
                    latest_frame = jpg

            # --- 텍스트 변경 시 갱신 ---
            with text_lock:
                if text != last_text:
                    last_text = text
                    print(f"[OCR] 업데이트: {text}")

            # 부하 방지
            # time.sleep(0.05)

        # 내부 루프를 빠져나오면 2초 대기 후 재연결
        time.sleep(2)
        print("[INFO] 2초 후 다시 카메라 스트림을 열어봅니다...", file=sys.stderr)


@app.route("/annot_stream")
def annot_stream():
    """
    캐시된 latest_frame 을 MJPEG 스트림으로 제공.
    브라우저에서 <img src="/annot_stream"> 로 바로 재생 가능.
    """

    def generator():
        while True:
            with frame_lock:
                chunk = latest_frame
            if chunk:
                yield chunk
            else:
                time.sleep(0.1)

    return Response(
        stream_with_context(generator()),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


@sock.route("/ws_plain")
def ws_plain(ws):
    """
    순수 WebSocket 엔드포인트.
    last_text 가 변경될 때마다 연결된 클라이언트에 푸시.
    """
    prev = ""
    while True:
        with text_lock:
            curr = last_text
        if curr != prev:
            ws.send(curr)
            prev = curr
        eventlet.sleep(0.05)


if __name__ == "__main__":
    # 백그라운드 스레드 시작
    threading.Thread(target=capture_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=6000, threaded=True)
