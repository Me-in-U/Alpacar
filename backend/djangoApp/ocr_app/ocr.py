# C:\Users\SSAFY\Documents\GitHub\S13P11E102\backend\djangoApp\ocr_app\ocr.py

import json
import os
import re
import sys
import threading
import time

import cv2

# Django 셋업 & 모델 임포트
import django
import easyocr
import numpy as np
from django.conf import settings
from PIL import Image, ImageDraw, ImageFont
from ultralytics import YOLO

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djangoApp.settings")
django.setup()
# 웹푸시용
from pywebpush import WebPushException, webpush

from accounts.models import Member, PushSubscription


def send_push(subscription, title, body):
    payload = json.dumps({"title": title, "body": body})
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
    except WebPushException as ex:
        print(f"[PUSH ERROR] {ex}", file=sys.stderr)


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

KOREAN = (
    "가나다라마거너더러머버서어저"
    "고노도로모보소오조구누두루"
    "무부수우주아바사자허하호배"
)

# 번호판 패턴
plate_pattern = re.compile(
    rf"^(?:0[1-9]|[1-9]\d|[1-9]\d{{2}})"  # 01-99 또는 100-999
    rf"[{KOREAN}]"  # 한글 1자
    rf"[1-9]\d{{3}}$"  # 1000-9999
)


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
    last_entered = None
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
            pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            draw = ImageDraw.Draw(pil)

            # 초기화
            text = "인식대기중"
            cleaned = ""
            is_valid_plate = False

            # 번호판 후보가 있을 때만 OCR 실행
            res = model.predict(frame, conf=0.4, device="cuda:0", verbose=False)[
                0
            ].boxes
            boxes = res.xyxy.cpu().numpy()
            scores = res.conf.cpu().numpy()
            if scores.size and scores.max() > 0.4:
                # OCR 수행
                i = np.argmax(scores)
                x1, y1, x2, y2 = boxes[i].astype(int)
                roi = frame[y1:y2, x1:x2]
                gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                blur = cv2.medianBlur(gray, 3)
                result = reader.readtext(blur, detail=1, paragraph=False)
                text = " ".join([t for _, t, p in result if p > 0.5])
                cleaned = text.replace(" ", "")
                # 매치 검사
                is_valid_plate = bool(plate_pattern.match(cleaned))
                # 박스/텍스트 색 결정
                color = "lime" if is_valid_plate else "red"
                draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
                draw.text((x1, y1 - 30), text, font=font, fill=color)

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

            # 3) 텍스트 갱신 & 푸시 발송
            with text_lock:
                # 번호판 포맷이 아니면 무시
                if not is_valid_plate:
                    continue

                # 이미 처리된 번호판이면 무시
                if cleaned == last_entered:
                    last_text = f"{cleaned} 입차된 차량"
                    continue

                # 한 번만 DB를 조회
                try:
                    user_qs = Member.objects.filter(plate_number=cleaned)
                    exists = user_qs.exists()
                except Exception:
                    exists = False

                # ─────────── 화면용 last_text 갱신 ───────────
                if exists:
                    last_text = f"입차:{cleaned}"
                    # ─────────── 푸시 발송 ───────────
                    # 등록된 차량이면서 사용자가 푸시 수신을 켜놨다면
                    if exists and cleaned != last_entered:
                        # 푸시 수신 ON 유저만 필터
                        push_users = user_qs.filter(push_enabled=True)
                        if push_users.exists():
                            print(
                                f"[OCR] 번호판 인식 및 푸시: {cleaned}", file=sys.stderr
                            )

                            # 구독 정보 한 번에 꺼내서
                            subs = PushSubscription.objects.filter(user__in=push_users)
                            for sub in subs:
                                send_push(
                                    sub,
                                    title="차량 번호판 감지",
                                    body=f"`{cleaned}` 차량이 감지되었습니다.",
                                )
                    last_entered = cleaned  # 등록차량 입차 처리
                else:
                    last_text = "등록되지 않은 차량입니다"

            # 계속 다음 프레임 처리…

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
