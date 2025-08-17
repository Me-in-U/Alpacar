# test_jetson_sender.py
import json
import math
import random
import threading
import time
from typing import Dict, List, Any, Optional
from contextlib import suppress

import websocket

WS_URL = "wss://i13e102.p.ssafy.io/ws/jetson/"
# WS_URL = "ws://localhost:8000/ws/jetson/"

# ==== 환경/레이아웃 (프론트 오버레이 좌표와 맞춤) ====
CANVAS_W, CANVAS_H = 900, 550

MY_PLATE = "157고4895"
OTHER_PLATES = ["12가3456", "11가1111"]

ALL_SLOTS = ["B1", "B2", "B3", "C1", "C2", "C3", "A1", "A2", "A3", "A4", "A5"]

# 초기 슬롯 상태
BASE_SLOT_MAP: Dict[str, str] = {
    "B1": "occupied",
    "B2": "occupied",
    "B3": "free",
    "C1": "occupied",
    "C2": "occupied",
    "C3": "occupied",
    "A1": "occupied",
    "A2": "occupied",
    "A3": "occupied",
    "A4": "occupied",
    "A5": "occupied",
}

# 토글 후보
TOGGLE_CANDIDATES = ["B2", "C3", "A1", "A3", "A4"]

# ===== 내부 공유 상태 (요청 처리 시 사용) =====
_state_lock = threading.RLock()
_current_slot_map: Dict[str, str] = BASE_SLOT_MAP.copy()


def get_slot_map_copy() -> Dict[str, str]:
    with _state_lock:
        return dict(_current_slot_map)


def set_slot_status(label: str, status: str):
    with _state_lock:
        _current_slot_map[label] = status


def replace_slot_map(m: Dict[str, str]):
    with _state_lock:
        _current_slot_map.clear()
        _current_slot_map.update(m)


# ✅ BASE_SLOT_MAP까지 함께 반영
def reserve_slot_globally(label: str):
    with _state_lock:
        BASE_SLOT_MAP[label] = "reserved"
        _current_slot_map[label] = "reserved"


# ===== 유틸 =====
def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def rect_corners(
    cx: float, cy: float, w: float, h: float, angle_deg: float
) -> List[List[float]]:
    ang = math.radians(angle_deg)
    ca, sa = math.cos(ang), math.sin(ang)
    local = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
    world = []
    for x, y in local:
        rx = x * ca - y * sa
        ry = x * sa + y * ca
        world.append([clamp(cx + rx, 0, CANVAS_W - 1), clamp(cy + ry, 0, CANVAS_H - 1)])
    return world


def suggested_slot_for_my_car(slot_map: Dict[str, str]) -> str:
    for s in ALL_SLOTS:
        if slot_map.get(s) == "free":
            return s
    return ""


def build_frame(t: float, slot_map: Dict[str, str]) -> Dict[str, Any]:
    cx = 450 + 160 * math.cos(t * 0.5)
    cy = 275 + 90 * math.sin(t * 0.5)
    angle = 15.0 * math.sin(t * 0.7)
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

    cx2 = (100 + (t * 60)) % (CANVAS_W + 120) - 60
    cy2 = 140
    car2 = {
        "plate": OTHER_PLATES[0],
        "center": {"x": round(cx2, 1), "y": round(cy2, 1)},
        "corners": rect_corners(cx2, cy2, 100, 44, 0),
        "state": "moving",
        "suggested": "",
    }

    cx3 = (CANVAS_W - 100 - (t * 80)) % (CANVAS_W + 200) - 100
    cy3 = 420
    car3 = {
        "plate": OTHER_PLATES[1],
        "center": {"x": round(cx3, 1), "y": round(cy3, 1)},
        "corners": rect_corners(cx3, cy3, 110, 48, 180),
        "state": "moving",
        "suggested": "",
    }

    return {
        "message_type": "car_position",
        "slot": slot_map,
        "vehicles": [my_car, car2, car3],
    }


def slot_map_with_toggles(base: Dict[str, str], t: float) -> Dict[str, str]:
    m = base.copy()
    if int(t) % 6 == 0:
        # ✅ reserved 슬롯은 토글 대상에서 제외
        candidates = [c for c in TOGGLE_CANDIDATES if m.get(c) != "reserved"]
        if candidates:
            target = random.choice(candidates)
            cur = m.get(target, "free")
            m[target] = (
                random.choice(["occupied", "reserved"]) if cur == "free" else "free"
            )
    return m


# ===== 슬롯 선택 로직 =====
def pick_assignment(size_class: Optional[str]) -> Optional[str]:
    """
    매우 단순한 선택 규칙:
      1) 현재 free인 슬롯 중 ALL_SLOTS 순서대로 첫 번째
      2) size_class는 여기선 구분하지 않고 로그만 남김 (필요 시 규칙 확장)
    """
    m = get_slot_map_copy()
    for label in ALL_SLOTS:
        if m.get(label) == "free":
            return label
    return None


# ===== 송신 루프 =====
def sender_loop(ws, fps: float = 2.0):
    print("[송신 시작] car_position 프레임을 주기적으로 전송합니다.")
    t = 0.0
    dt = 1.0 / fps
    local_map = get_slot_map_copy()

    try:
        while True:
            # 토글 + 공유 상태 반영
            local_map = slot_map_with_toggles(local_map, t)
            replace_slot_map(local_map)

            frame = build_frame(t, local_map)
            with suppress(Exception):
                ws.send(json.dumps(frame, ensure_ascii=False))

            # 콘솔 확인용
            print(
                f"[보냄] t={t:.1f}s vehicles={len(frame['vehicles'])} "
                f"suggested={frame['vehicles'][0]['suggested']} slots.changed=maybe"
            )
            print(json.dumps(frame, ensure_ascii=False, indent=2))
            time.sleep(dt)
            t += dt
    except KeyboardInterrupt:
        print("\n[중단] 사용자 종료")
    except Exception as e:
        print("[송신 오류]", e)


# ===== 요청 처리(장고 → 젯슨) =====
def handle_request_assignment(ws, payload: Dict[str, Any]):
    plate = payload.get("license_plate")
    size_class = payload.get("size_class")
    print(f"[요청 수신] request_assignment plate={plate} size_class={size_class}")

    slot = pick_assignment(size_class)
    if not slot:
        print("[배정 실패] 빈 슬롯 없음")
        return

    # ✅ 전역/현재 맵 모두 예약 처리 → 이후 프레임/리셋에도 반영
    reserve_slot_globally(slot)

    resp = {
        "message_type": "assignment",
        "license_plate": plate,
        "assignment": slot,
    }
    print("[회신] assignment =>", json.dumps(resp, ensure_ascii=False))
    with suppress(Exception):
        ws.send(json.dumps(resp, ensure_ascii=False))

    # (옵션) 몇 초 후 score 전송
    def _send_score_later():
        time.sleep(15)
        score = {"message_type": "score", "license_plate": plate, "score": 100}
        print("[후속] score =>", json.dumps(score, ensure_ascii=False))
        with suppress(Exception):
            ws.send(json.dumps(score, ensure_ascii=False))

    threading.Thread(target=_send_score_later, daemon=True).start()


# ===== websocket 콜백 =====
def on_open(ws):
    print("[연결 성공] /ws/jetson/ 로 송신을 시작합니다.")
    threading.Thread(target=sender_loop, args=(ws,), daemon=True).start()


def on_message(ws, message):
    try:
        data = json.loads(message)
    except Exception:
        print("[장고→젯슨 수신][raw]", message)
        return

    mtype = data.get("message_type")
    print("[장고→젯슨 수신]", json.dumps(data, ensure_ascii=False))

    if mtype == "request_assignment":
        handle_request_assignment(ws, data)
    else:
        # 그 외 메시지는 그대로 로그만
        pass


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
