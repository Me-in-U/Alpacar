import time

import eventlet

eventlet.monkey_patch()

# Component
import ocr

# Flask
from flask import Flask, Response, render_template, stream_with_context
from flask_sock import Sock
from flask_socketio import SocketIO

app = Flask(__name__)
sock = Sock(app)
socketio = SocketIO(app, async_mode="eventlet", cors_allowed_origins="*")

# OCR 백그라운드 시작
ocr.start_capture()


@app.route("/")
def index():
    return render_template("index.html")  # 여기에 적절히


@app.route("/annot_stream")
def annot_stream():
    """MJPEG 스트림 제공"""

    def gen():
        while True:
            chunk = None
            with ocr.frame_lock:
                chunk = ocr.latest_frame
            if chunk:
                yield chunk
            else:
                time.sleep(0.1)

    return Response(
        stream_with_context(gen()), mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@sock.route("/ws_plain")
def ws_plain(ws):
    """순수 WebSocket: 텍스트 업데이트 푸시"""
    prev = ""
    while True:
        with ocr.text_lock:
            curr = ocr.last_text
        if curr != prev:
            ws.send(curr)
            prev = curr
        eventlet.sleep(0.05)


@socketio.on("connect")
def on_connect():
    print("[SocketIO] Client connected")


@socketio.on("disconnect")
def on_disconnect():
    print("[SocketIO] Client disconnected")


if __name__ == "__main__":
    # Flask‑Sock 순수 WS + SocketIO 동시 실행
    # socketio.run(app, host="0.0.0.0", port=5000, debug=True, use_reloader=False)
    # gunicorn -w 2 -k eventlet -b 0.0.0.0:5000 app:app
    pass
