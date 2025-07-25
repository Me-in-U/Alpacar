# C:\Users\SSAFY\Documents\GitHub\S13P11E102\backend\djangoApp\ocr_app\ocr.py

import os
import sys
import threading
import time
import re
import cv2
import easyocr
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from ultralytics import YOLO

# --- 전역 상태 변수 선언 ---
CAM_STREAM_URL = "http://192.168.8.253:5000/stream"
latest_frame = None
frame_lock = threading.Lock()
last_text = ""
text_lock = threading.Lock()

started = False  # 추가: 스레드 기동 플래그
MULTI_PLATE_MODE = False  # True로 설정하면 다중 번호판 인식

# 모델, OCR Reader, font 객체는 실제 시작 시 초기화
model = None
reader = None
font = None

# 번호판 패턴
plate_pattern = re.compile(r"^\d{2,3}[가-힣]\d{4}$")


def _init_ocr():
    """
    서버(runserver) 시작 시 한 번만 호출되어 모델, OCR Reader, font를 초기화합니다.
    """
    global model, reader, font
    # 프로젝트 루트 기준으로 경로 설정
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    weights_path = os.path.join(base_dir, "ocr_app", "weights", "best.pt")
    font_path = os.path.join(base_dir, "ocr_app", "NanumGothic-Regular.ttf")

    model = YOLO(weights_path).to("cuda:0")
    reader = easyocr.Reader(["ko"], gpu=True)
    font = ImageFont.truetype(font_path, size=70)


def capture_loop():
    """
    1) MJPEG 스트림에서 프레임 읽기
    2) 번호판 박스 탐지 + OCR
    3) 어노테이트한 프레임 JPEG 인코딩 → latest_frame에 캐시
    4) OCR 텍스트 변경 시 last_text 갱신
    """
    global latest_frame, last_text
    _init_ocr()

    boundary = b"--frame\r\n"
    while True:
        cap = cv2.VideoCapture(CAM_STREAM_URL)
        cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 2000)
        cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 2000)
        if not cap.isOpened():
            print(f"[ERROR] CAM_STREAM 연결 실패 → {CAM_STREAM_URL}", file=sys.stderr)
            print("[INFO] 5초 후 재연결 시도...", file=sys.stderr)
            time.sleep(5)
            continue

        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                print("[WARN] 프레임 읽기 실패, 재연결", file=sys.stderr)
                cap.release()
                break

            # OCR & 어노테이트
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

            # JPEG 인코딩 & 캐시
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 30]
            annotated = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
            ok, buf = cv2.imencode(".jpg", annotated, encode_param)
            if ok:
                chunk = (
                    boundary
                    + b"Content-Type: image/jpeg\r\n\r\n"
                    + buf.tobytes()
                    + b"\r\n"
                )
                with frame_lock:
                    latest_frame = chunk

            # OCR 텍스트 변경 시 갱신
            with text_lock:
                # 공백 제거
                cleaned = text.replace(" ", "")
                # “인식대기중”이거나, 번호판 패턴에 맞을 때만 갱신
                if (text == "인식대기중" and last_text != text) or (
                    plate_pattern.match(cleaned) and last_text != cleaned
                ):
                    # default ↔ plate
                    last_text = text if text == "인식대기중" else cleaned
                    print(f"[OCR] 업데이트: {last_text}")

        time.sleep(2)
        print("[INFO] 2초 후 캡처 루프 재시작...", file=sys.stderr)


def start_capture():
    """
    서버 시작 시 한 번만 호출: 백그라운드 OCR 루프 실행
    """
    global started
    if started:
        return
    started = True
    thread = threading.Thread(target=capture_loop, daemon=True)
    thread.start()
