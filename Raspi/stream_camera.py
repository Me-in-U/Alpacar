# stream_camera.py
# Flask 기반의 MJPEG 스트리밍 서버
# Picamera2를 사용하여 카메라 스트림을 처리합니다.

from flask import Flask, Response
from flask_wtf import CSRFProtect  # CSRFProtect 사용을 위한 import
import cv2
from picamera2 import Picamera2
from libcamera import controls


app = Flask(__name__)
csrf = CSRFProtect()
csrf.init_app(app)  # GET/HEAD/OPTIONS는 기본적으로 CSRF 검사 대상 아님
# CSRF 안내(S4502):
# - 이 서비스는 스트리밍(읽기 전용)만 제공하며 서버 상태를 변경하지 않습니다.
# - 세션/쿠키/인증 정보를 사용하지 않습니다.
# - 따라서 본 엔드포인트는 CSRF 보호 미적용이 안전합니다. (python:S4502)

# --- Picamera2 초기 설정 (기존 설정 그대로) ---
picam2 = Picamera2()
config = picam2.create_preview_configuration(
    main={"size": (4608, 2592), "format": "RGB888"},
    lores={"size": (2304, 1296), "format": "RGB888"},
)
picam2.configure(config)
picam2.start()
picam2.set_controls(
    {"AfMode": controls.AfModeEnum.Manual, "LensPosition": 20.0, "FrameRate": 30.0}
)


def zoom_flip(frame, zoom=2.0):
    h, w = frame.shape[:2]
    cw, ch = int(w / zoom), int(h / zoom)
    x1, y1 = (w - cw) // 2, (h - ch) // 2
    crop = frame[y1 : y1 + ch, x1 : x1 + cw]
    return cv2.flip(crop, -1)


def mjpeg_generator():
    boundary = b"--frame\r\n"
    while True:
        # Picamera2에서 한 프레임 캡처
        frame = picam2.capture_array("lores")

        # 2배 확대 & 뒤집기
        frame = zoom_flip(frame, zoom=2.0)

        # NumPy array → JPEG bytes
        success, jpg = cv2.imencode(".jpg", frame)
        if not success:
            continue

        yield (boundary + b"Content-Type: image/jpeg\r\n\r\n" + jpg.tobytes() + b"\r\n")


@app.route("/stream", methods=["GET"])  # CSRF-safe: read-only GET endpoint (S4502)
def stream():
    """
    브라우저 <img src="/stream"> 으로 접속하면
    메인 해상도로 MJPEG 스트리밍이 시작됩니다.

    보안 참고:
    - GET 전용, 서버 상태 변경 없음, 세션/쿠키 미사용 → CSRF 토큰 불필요 (S4502)
    """
    return Response(
        mjpeg_generator(), mimetype="multipart/x-mixed-replace; boundary=frame"
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, threaded=True)
