# stream_camera.py
# Flask 기반의 MJPEG 스트리밍 서버
# Picamera2를 사용하여 카메라 스트림을 처리합니다.

from flask import Flask, Response
import cv2
from picamera2 import Picamera2
from libcamera import controls

app = Flask(__name__)

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


@app.route("/stream")
def stream():
    """
    브라우저 <img src="/stream"> 으로 접속하면
    메인 해상도로 MJPEG 스트리밍이 시작됩니다.
    """
    return Response(
        mjpeg_generator(), mimetype="multipart/x-mixed-replace; boundary=frame"
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, threaded=True)
