import base64
import json
import time, requests, cv2, numpy as np
import easyocr
from ultralytics import YOLO
from picamera2 import Picamera2
from libcamera import controls
from PIL import Image, ImageDraw, ImageFont
from requests import RequestException
import re
import time
from websocket import create_connection, WebSocketException

# ─── 백엔드 서버 주소 설정 ─────────────────────────────────────────────────────────
WS_URL = 'ws://192.168.45.183:8000/ws/upload/'

# ─── HTTP 세션 재사용 ────────────────────────────────────────────────────────
sess = requests.Session() # 세션 재사용

# ─── 모델 · OCR 설정 ───────────────────────────────────────────────────
model  = YOLO("weights/best.pt") # 번호판 탐지용 YOLO 모델 로드
reader = easyocr.Reader(['ko'], gpu=False) # OCR 엔진 (한글만) 비GPU 모드
FONT_PATH = "NanumGothic-Regular.ttf" # PIL 한글 폰트 파일 경로
font      = ImageFont.truetype(FONT_PATH, size=48) # PIL 텍스트용 폰트

# ─── Picamera2 설정 ────────────────────────────────────────────────────
picam2 = Picamera2()
config = picam2.create_preview_configuration(
    main = {"size": (4608,2592), "format": "RGB888"}, # 원본 해상도 캡처
    lores= {"size": (2304,1296), "format": "RGB888"},# OCR용 저해상도
)
picam2.configure(config)
picam2.start()
picam2.set_controls({
    "AfMode":       controls.AfModeEnum.Manual, # 수동 초점
    "LensPosition": 20.0,
    "FrameRate":    10.0 # 초당 10프레임
})

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

# ─── WebSocket 연결 ──────────────────────────────────────────────────────
try:
    ws = create_connection(WS_URL)
    print("WebSocket 연결 성공")
except WebSocketException as e:
    print("WebSocket 연결 실패:", e)
    exit(1)

# ─── 유틸 함수 ────────────────────────────────────────────────────────────
def zoom_flip(frame, zoom=2.0):
    h, w = frame.shape[:2]
    cw, ch = int(w/zoom), int(h/zoom)
    x1, y1 = (w-cw)//2, (h-ch)//2
    crop = frame[y1:y1+ch, x1:x1+cw]
    return cv2.flip(crop, -1)

# ─── YOLO로 번호판 위치 검출 ───────────────────────────────────────────────
def detect_plate_pos(frame, conf_threshold=0.5) -> None | tuple[int, int, int, int]:
    results = model.predict(frame, conf=conf_threshold, verbose=False)[0].boxes
    boxes   = results.xyxy.cpu().numpy()  # shape (N,4)
    scores  = results.conf.cpu().numpy()  # shape (N,)

    # 검출 결과가 없으면 None 리턴
    if scores.size == 0:
        return None

    # 가장 높은 confidence 인덱스 찾기
    best_i = np.argmax(scores)
    if scores[best_i] < conf_threshold:
        return None

    x1, y1, x2, y2 = boxes[best_i]
    return int(x1), int(y1), int(x2), int(y2)

# ─── OCR 및 어노테이트 함수 ────────────────────────────────────────────────
def ocr_and_annotate():
    global text
    original_frame = picam2.capture_array("lores") # 저해상도 캡처
    zoomed_frame = zoom_flip(original_frame) # 중앙 크롭 & 뒤집기
    text = "번호판 인식 대기중"
    
    # 번호판 영역 탐지
    start = time.perf_counter()
    plate_coords = detect_plate_pos(zoomed_frame)
    elapsed = time.perf_counter() - start
    print(f"[Detect] {elapsed*1000:.1f} ms", end=", ")
    
    # PIL 이미지로 변환 및 어노테이션 준비
    pillow = Image.fromarray(cv2.cvtColor(zoomed_frame, cv2.COLOR_BGR2RGB))

    if plate_coords:
        x1, y1, x2, y2 = plate_coords
        plate_image = zoomed_frame[y1:y2, x1:x2] # ROI 추출
        h, w = plate_image.shape[:2]
        print(f"[PLATE] {w}x{h}", end=", ")

        # 너비 333px로 리사이즈 (비율 유지)
        target_w = 333
        target_h = int(h * (target_w / w))
        small = cv2.resize(
            plate_image,
            (target_w, target_h),       # (width, height)
            interpolation=cv2.INTER_LINEAR
        )
        
        # 전처리
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        blur = cv2.medianBlur(gray, 3)
        
        # OCR 수행
        start = time.perf_counter()
        ocr_result = reader.readtext(blur, detail=1, paragraph=False)
        elapsed = time.perf_counter() - start
        print(f"[OCR] {elapsed*1000:.1f} ms", end=", ")  # 예: 100 ms 이내 목표

        # 유효성 검사
        start = time.perf_counter()
        text = "".join([t for (_b, t, p) in ocr_result if p > 0.5]).replace(" ", "")
        is_valid_plate = bool(plate_pattern.match(text))
        text = text if is_valid_plate else "유효하지 않은 번호판"
        
        # 박스/텍스트 색 결정
        color = "lime" if is_valid_plate else "red"
        draw = ImageDraw.Draw(pillow)
        draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
        draw.text((x1, y1 - 30), text, font=font, fill=color)
        elapsed = time.perf_counter() - start
        print(f"[DRAW] {elapsed*1000:.1f} ms", end=", ")  # 예: 100 ms 이내 목표

    # PIL → NumPy(BGR) 변환 후 반환
    annotated_np = cv2.cvtColor(np.array(pillow), cv2.COLOR_RGB2BGR)
    return annotated_np, text

# ─── WebSocket 전송 함수 ────────────────────────────────────────────────
def send_with_retry(ws, msg, url, max_retries=3, backoff=2):
    payload = json.dumps(msg)
    for attempt in range(1, max_retries+1):
        try:
            ws.send(payload)
            return ws
        except Exception as e:
            print(f"[WS send 실패] 시도 {attempt}/{max_retries}: {e}")
            try:
                ws.close()
            except:
                pass
            time.sleep(backoff)
            try:
                ws = create_connection(url)
                print("[WS] 재연결 성공")
            except Exception as e2:
                print(f"[WS] 재연결 실패: {e2}")
    raise ConnectionError("WebSocket 전송/재연결 모두 실패")

# ─── 메인 루프: 캡처 → OCR → WebSocket 전송 ─────────────────────────────────
try:
    while True:
        # 타이머 시작
        start = time.perf_counter()
        
        # 캡처 & 어노테이트
        out, text = ocr_and_annotate()

        # JPEG → base64
        ok, buf = cv2.imencode('.jpg', out, [cv2.IMWRITE_JPEG_QUALITY,30])
        if not ok:
            continue
        b64 = base64.b64encode(buf.tobytes()).decode()
        msg = {"image": b64, "text": text}

        # WebSocket 전송 및 예외 처리
        try:
            ws = send_with_retry(ws, msg, WS_URL)
        except ConnectionError as err:
            print(err)
            continue  # 다음 루프에서 다시 시도
        
        # 타이머 종료
        elapsed = time.perf_counter() - start
        print(f"\n[LOOP] {elapsed*1000:.1f} ms\n")

except KeyboardInterrupt:
    # Ctrl+C 입력 시 자원 정리
    print("종료 중: 세션과 카메라 정리합니다.")
    sess.close()
    picam2.stop()
    print("종료 완료.")