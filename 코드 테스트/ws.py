# test_jetson_sender.py
import json
import math
import random
import threading
import time
from typing import Dict, List

import websocket

WS_URL = "wss://i13e102.p.ssafy.io/ws/jetson/"
# WS_URL = "ws://localhost:8000/ws/jetson/"

# ==== 환경/레이아웃 (프론트 오버레이 좌표와 맞춤) ====
CANVAS_W, CANVAS_H = 900, 550

MY_PLATE = "157고4895"
OTHER_PLATES = ["12가3456", "11가1111"]

ALL_SLOTS = ["B1", "B2", "B3", "C1", "C2", "C3", "A1", "A2", "A3", "A4", "A5"]

# 초기 슬롯 상태(원하는 대로 바꾸세요)
BASE_SLOT_MAP: Dict[str, str] = {
    "B1": "free",
    "B2": "free",
    "B3": "free",
    "C1": "occupied",
    "C2": "reserved",
    "C3": "free",
    "A1": "free",
    "A2": "occupied",
    "A3": "free",
    "A4": "free",
    "A5": "reserved",
}

# 주기적으로 토글할 후보 슬롯들(occupied <-> free)
TOGGLE_CANDIDATES = ["B2", "B3", "C3", "A3", "A4"]


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def rect_corners(
    cx: float, cy: float, w: float, h: float, angle_deg: float
) -> List[List[float]]:
    """중심(cx,cy), 가로w, 세로h, 각도(deg)로 4개 모서리 좌표 생성 (좌상→우상→우하→좌하)."""
    ang = math.radians(angle_deg)
    ca, sa = math.cos(ang), math.sin(ang)
    # 중심 기준 직사각형 코너(시계방향)
    local = [
        (-w / 2, -h / 2),
        (w / 2, -h / 2),
        (w / 2, h / 2),
        (-w / 2, h / 2),
    ]
    world = []
    for x, y in local:
        rx = x * ca - y * sa
        ry = x * sa + y * ca
        world.append([clamp(cx + rx, 0, CANVAS_W - 1), clamp(cy + ry, 0, CANVAS_H - 1)])
    return world


def suggested_slot_for_my_car(slot_map: Dict[str, str]) -> str:
    """가장 먼저 보이는 free 슬롯을 추천값으로 사용(간단)."""
    for s in ["B1", "B2", "B3", "C1", "C2", "C3", "A1", "A2", "A3", "A4", "A5"]:
        if slot_map.get(s) == "free":
            return s
    return ""


def build_frame(t: float, slot_map: Dict[str, str]) -> Dict:
    """t(초)에 따른 차량 위치/각도 애니메이션 + 슬롯 상태를 포함한 프레임 생성."""
    # 내 차(부드러운 원운동)
    cx = 450 + 160 * math.cos(t * 0.5)
    cy = 275 + 90 * math.sin(t * 0.5)
    angle = 15.0 * math.sin(t * 0.7)  # -15~+15도
    my_car = {
        "plate": MY_PLATE,
        "center": {
            "x": round(clamp(cx, 0, CANVAS_W - 1), 1),
            "y": round(clamp(cy, 0, CANVAS_H - 1), 1),
        },
        "corners": rect_corners(cx, cy, 90, 40, angle),
        "state": "moving",
        "suggested": suggested_slot_for_my_car(slot_map),
    }

    # 임의 차량 1: 좌→우 직선 주행
    cx2 = (100 + (t * 60)) % (CANVAS_W + 120) - 60
    cy2 = 140
    angle2 = 0
    car2 = {
        "plate": OTHER_PLATES[0],
        "center": {"x": round(cx2, 1), "y": round(cy2, 1)},
        "corners": rect_corners(cx2, cy2, 100, 44, angle2),
        "state": "moving",
        "suggested": "",
    }

    # 임의 차량 2: 우→좌 직선 주행
    cx3 = (CANVAS_W - 100 - (t * 80)) % (CANVAS_W + 200) - 100
    cy3 = 420
    angle3 = 180
    car3 = {
        "plate": OTHER_PLATES[1],
        "center": {"x": round(cx3, 1), "y": round(cy3, 1)},
        "corners": rect_corners(cx3, cy3, 110, 48, angle3),
        "state": "moving",
        "suggested": "",
    }

    payload = {
        "message_type": "car_position",
        "slot": slot_map,  # {"B1": "free", ...}
        "vehicles": [my_car, car2, car3],  # 0대 이상 가능
    }
    return payload


def slot_map_with_toggles(base: Dict[str, str], t: float) -> Dict[str, str]:
    """일정 주기로 일부 슬롯 상태를 토글하여 DB/프론트 반응 테스트."""
    m = base.copy()
    # 6초마다 하나 토글
    if int(t) % 6 == 0:
        target = random.choice(TOGGLE_CANDIDATES)
        cur = m.get(target, "free")
        if cur == "free":
            m[target] = random.choice(["occupied", "reserved"])
        else:
            m[target] = "free"
    return m


def sender_loop(ws, fps: float = 2.0):
    print("[송신 시작] car_position 프레임을 주기적으로 전송합니다.")
    t = 0.0
    dt = 1.0 / fps
    slot_map = BASE_SLOT_MAP.copy()

    try:
        while True:
            # 슬롯 토글 반영
            slot_map = slot_map_with_toggles(slot_map, t)
            frame = build_frame(t, slot_map)
            ws.send(json.dumps(frame, ensure_ascii=False))
            # 콘솔 확인용
            print(
                f"[보냄] t={t:.1f}s vehicles={len(frame['vehicles'])} suggested={frame['vehicles'][0]['suggested']} slots.changed=maybe"
            )
            time.sleep(dt)
            t += dt
    except KeyboardInterrupt:
        print("\n[중단] 사용자 종료")
    except Exception as e:
        print("[송신 오류]", e)


# ===== websocket 콜백 =====
def on_open(ws):
    print("[연결 성공] /ws/jetson/ 로 송신을 시작합니다.")
    threading.Thread(target=sender_loop, args=(ws,), daemon=True).start()


def on_message(ws, message):
    # 장고가 젯슨으로 보내는 제어 메시지(예: request_assignment)를 여기서 확인 가능
    print("[장고→젯슨 수신]", message)


def on_error(ws, error):
    print("[에러]", error)


def on_close(ws, close_status_code, close_msg):
    print("[닫힘]", close_status_code, close_msg)


if __name__ == "__main__":
    ws = websocket.WebSocketApp(
        WS_URL,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )
    # ping 간격/타임아웃은 환경에 맞게
    ws.run_forever(ping_interval=20, ping_timeout=10)
