# test_jetson_ws.py
import json

import websocket

WS_URL = "wss://i13e102.p.ssafy.io/ws/jetson/"  # 장고 라우팅에 맞춰 수정


def on_message(ws, message):
    print("[받음]", message)
    try:
        data = json.loads(message)
        print("[파싱]", json.dumps(data, indent=2, ensure_ascii=False))
    except Exception:
        pass


def on_error(ws, error):
    print("[에러]", error)


def on_close(ws, close_status_code, close_msg):
    print("[닫힘]", close_status_code, close_msg)


def on_open(ws):
    print("[연결 성공] 장고가 보내는 메시지를 기다립니다.")


if __name__ == "__main__":
    ws = websocket.WebSocketApp(
        WS_URL,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )
    ws.run_forever()
