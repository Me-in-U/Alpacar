# cd frontend\TEST
# python web.py

import eventlet

eventlet.monkey_patch()

import sys
import threading
import time

import cv2
from flask import Flask, render_template
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app, async_mode="eventlet", cors_allowed_origins="*")

# OCR 서비스에서 뿌리는 어노테이트 MJPEG 스트림
ANN_STREAM = "http://localhost:6000/annot_stream"

# VideoCapture 는 한 번만 열어 둡니다.
cap_ann = cv2.VideoCapture(ANN_STREAM)


def reopen_capture():
    """cap_ann 을 다시 열어줍니다."""
    global cap_ann
    if cap_ann:
        try:
            cap_ann.release()
        except Exception as e:
            print(f"[WARN] cap_ann.release() 중 예외: {e}", file=sys.stderr)
    print(
        f"[INFO] reopen_capture: 2초 대기 후 스트림 재연결 시도 → {ANN_STREAM}",
        file=sys.stderr,
    )
    time.sleep(2)
    cap_ann = cv2.VideoCapture(ANN_STREAM)
    if cap_ann.isOpened():
        print(f"[INFO] reopen_capture: 재연결 성공", file=sys.stderr)
    else:
        print(f"[ERROR] reopen_capture: 재연결 실패", file=sys.stderr)


# 최초 오픈 체크
if cap_ann.isOpened():
    print(f"[INFO] 초기 연결 성공: {ANN_STREAM}", file=sys.stderr)
else:
    print(f"[ERROR] 초기 연결 실패: {ANN_STREAM}", file=sys.stderr)


def capture_loop():
    """어노테이트 스트림을 읽어서 SocketIO로 raw JPEG bytes 전송"""
    global cap_ann

    # 최초 연결 시도
    cap_ann = cv2.VideoCapture(ANN_STREAM)
    cap_ann.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 2000)
    cap_ann.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 2000)
    if cap_ann.isOpened():
        print(f"[INFO] 초기 연결 성공: {ANN_STREAM}", file=sys.stderr)
    else:
        print(f"[ERROR] 초기 연결 실패: {ANN_STREAM}", file=sys.stderr)

    while True:
        if cap_ann is None or not cap_ann.isOpened():
            reopen_capture()
            continue

        ret_a, frame_a = cap_ann.read()
        if not ret_a or frame_a is None:
            print(
                "[WARN] capture_loop: 프레임 읽기 실패, 2초 대기 후 재연결",
                file=sys.stderr,
            )
            reopen_capture()
            continue

        # JPEG 인코딩
        ok, buf_a = cv2.imencode(".jpg", frame_a)
        if not ok:
            print("[WARN] capture_loop: imencode 실패", file=sys.stderr)
            socketio.sleep(0.033)
            continue

        # 각각 별도 이벤트로 전송
        socketio.emit("annot_frame", buf_a.tobytes())

        socketio.sleep(0.033)  # 약 30fps


@app.route("/")
def index():
    return render_template("index.html")


@socketio.on("connect")
def handle_connect():
    print("[INFO] WebSocket 클라이언트 연결됨")


@socketio.on("disconnect")
def handle_disconnect():
    print("[INFO] WebSocket 클라이언트 연결 끊김")


if __name__ == "__main__":
    # 백그라운드 스레드 시작
    threading.Thread(target=capture_loop, daemon=True).start()
    socketio.run(app, host="0.0.0.0", port=5000, debug=True, use_reloader=False)
