from ultralytics import YOLO
import cv2
from pathlib import Path
import math
import numpy as np
import time
import random
from collections import deque
import json
import os

# ------------------------------
# 주차구역 정규화 좌표 (parking_check copy.py에서 복사)
# ------------------------------
PARKING_ZONES_NORM = [
    {
        "id": "b1",
        "rect": [0.371914, 0.00823, 0.45216, 0.26749]
    },
    {
        "id": "b2",
        "rect": [0.448302, 0.010974, 0.527778, 0.268861]
    },
    {
        "id": "b3",
        "rect": [0.522377, 0.006859, 0.603395, 0.266118]
    },
    {
        "id": "c1",
        "rect": [0.633488, 0.005487, 0.709105, 0.237311]
    },
    {
        "id": "c2",
        "rect": [0.706019, 0.006859, 0.783951, 0.242798]
    },
    {
        "id": "c3",
        "rect": [0.783951, 0.009602, 0.858796, 0.238683]
    },
    {
        "id": "a1",
        "rect": [0.374228, 0.727023, 0.450617, 0.969822]
    },
    {
        "id": "a2",
        "rect": [0.448302, 0.727023, 0.524691, 0.973937]
    },
    {
        "id": "a3",
        "rect": [0.523148, 0.72428, 0.60108, 0.973937]
    },
    {
        "id": "a4",
        "rect": [0.631173, 0.73251, 0.707562, 0.971193]
    },
    {
        "id": "a5",
        "rect": [0.704475, 0.733882, 0.781636, 0.975309]
    }
]

# 주차/출차 판정 임계값(초)
ENTER_THRESHOLD_SECONDS = 3.0  # 구역 내에서 이 시간 이상 머무르면 '주차'로 판정
EXIT_THRESHOLD_SECONDS = 2.0   # 주차 중인 차량이 구역 밖으로 이 시간 이상 벗어나면 '출차'로 판정

# 구역 상태: zone_id -> { 'occupant_id': int|None, 'parked_since': float|None, 'last_inside_ts': float|None }
zone_state = {z["id"]: {"occupant_id": None, "parked_since": None, "last_inside_ts": None} for z in PARKING_ZONES_NORM}

# 주차 후보: zone_id -> { track_id -> first_inside_ts }
zone_candidates = {z["id"]: {} for z in PARKING_ZONES_NORM}

# 차량번호 큐(임시) 및 매핑 - 영어 형식 번호판 생성
ENG_PLATE_LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

def generate_plate() -> str:
    # 예: ABC-1234 (영문 3자 + 하이픈 + 숫자 4자리)
    letters = ''.join(random.choices(ENG_PLATE_LETTERS, k=3))
    digits = random.randint(1000, 9999)
    return f"{letters}-{digits}"

# 20개 큐 준비, 각 큐에 임의 번호 10개 채우기 (영문 번호판)
license_queues = [deque([generate_plate() for _ in range(10)]) for _ in range(20)]
_rr_queue_index = 0
track_id_to_plate = {}

def get_next_plate_from_queues() -> str:
    global _rr_queue_index
    n = len(license_queues)
    for i in range(n):
        idx = (_rr_queue_index + i) % n
        if license_queues[idx]:
            plate = license_queues[idx].popleft()
            _rr_queue_index = (idx + 1) % n
            return plate
    # 모든 큐가 비었으면 즉시 생성
    return generate_plate()

def ensure_plate_mapping(ids):
    if not ids:
        return
    for tid in ids:
        tid_int = int(tid)
        if tid_int not in track_id_to_plate:
            track_id_to_plate[tid_int] = get_next_plate_from_queues()

# 예약 구역(대문자 표기 사용) 설정: 필요하면 외부에서 갱신 가능
RESERVED_ZONES = set()  # 예: {'A1'}

# 스냅샷 저장 경로 및 주기
SNAPSHOT_PATH = str(Path(__file__).with_name('status_snapshot.json'))
_last_snapshot_ts = 0.0
_snapshot_interval_s = 0.5

def get_zone_center(rect_norm, frame_w, frame_h):
    x1n, y1n, x2n, y2n = rect_norm
    cx = (x1n + x2n) * 0.5 * frame_w
    cy = (y1n + y2n) * 0.5 * frame_h
    return float(cx), float(cy)

def assemble_slot_status(zones_norm, state, reserved_upper_set):
    slot = {}
    for zone in zones_norm:
        zid_lower = zone['id']
        zid_upper = zid_lower.upper()
        if zid_upper in reserved_upper_set:
            slot[zid_upper] = 'reserved'
        elif state.get(zid_lower, {}).get('occupant_id') is not None:
            slot[zid_upper] = 'occupied'
        else:
            slot[zid_upper] = 'free'
    return slot

def vehicle_state_from_zone_state(track_id):
    if track_id is None:
        return 'running'
    for st in zone_state.values():
        if st.get('occupant_id') == int(track_id):
            return 'parked'
    return 'running'

def suggest_zone_for_vehicle(cx, cy, zones_norm, frame_w, frame_h, state, reserved_upper_set):
    # 가장 가까운 free 구역 추천 (reserved 제외)
    best_zid_upper = None
    best_dist2 = None
    for zone in zones_norm:
        zid_lower = zone['id']
        zid_upper = zid_lower.upper()
        if zid_upper in reserved_upper_set:
            continue
        if state.get(zid_lower, {}).get('occupant_id') is not None:
            continue
        zcx, zcy = get_zone_center(zone['rect'], frame_w, frame_h)
        d2 = (zcx - cx) ** 2 + (zcy - cy) ** 2
        if best_dist2 is None or d2 < best_dist2:
            best_dist2 = d2
            best_zid_upper = zid_upper
    return best_zid_upper

def assemble_snapshot(center_list, xyxyxyxy_list, ids, zones_norm, frame_w, frame_h):
    # 슬롯 상태
    slot = assemble_slot_status(zones_norm, zone_state, RESERVED_ZONES)
    # 차량 목록
    vehicles = []
    if center_list and ids:
        for idx, ((cx, cy), tid) in enumerate(zip(center_list, ids)):
            plate = track_id_to_plate.get(int(tid))
            state_str = vehicle_state_from_zone_state(tid)
            # corners 추출: draw_boxes에서 생성한 pts_poly 사용
            corners = None
            try:
                pts_poly = xyxyxyxy_list[idx]
                pts = pts_poly.reshape(-1, 2)
                corners = [[float(x), float(y)] for x, y in pts]
            except Exception:
                corners = None
            # 구역 추천은 보류 → suggested는 None으로 유지
            suggested = None
            vehicles.append({
                'plate': plate if plate else f'ID{int(tid)}',
                'center': {'x': float(cx), 'y': float(cy)},
                'corners': corners,
                'state': state_str,
                'suggested': suggested,
            })
    snapshot = {'slot': slot, 'vehicles': vehicles}
    return snapshot

def save_status_snapshot(snapshot: dict, path: str = SNAPSHOT_PATH):
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(snapshot, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def point_in_norm_rect(cx: float, cy: float, frame_w: int, frame_h: int, rect_norm) -> bool:
    x1n, y1n, x2n, y2n = rect_norm
    x1, y1 = x1n * frame_w, y1n * frame_h
    x2, y2 = x2n * frame_w, y2n * frame_h
    return x1 <= cx <= x2 and y1 <= cy <= y2

# 비디오 파일 경로 지정 (예시: 'input.mp4')
video_path = 'data/video_part_1.mp4'

# 모델 로드 (last.pt 사용)
model = YOLO(
    'last.pt',
    )

# 트래킹 결과를 스트림으로 받아와 원하는 크기로 표시
_tracker_cfg = str(Path(__file__).with_name('bytetrack.yaml'))

def extract_track_ids(result):
    """Ultralytics 결과 객체에서 트래킹 ID 배열을 안전하게 추출한다.
    OBB 우선(result.obb.id), 없으면 boxes.id를 시도한다.
    return: list[int] | None
    """
    try:
        ids_tensor = None
        # OBB 트래킹 ID 우선
        if hasattr(result, 'obb') and result.obb is not None:
            ids_tensor = getattr(result.obb, 'id', None)
        # 일반 박스 트래킹 ID 보조
        if ids_tensor is None and hasattr(result, 'boxes') and result.boxes is not None:
            ids_tensor = getattr(result.boxes, 'id', None)

        if ids_tensor is None:
            return None

        # 텐서/리스트 모두 대응
        try:
            # 텐서인 경우
            if hasattr(ids_tensor, 'cpu'):
                arr = ids_tensor.cpu().numpy().tolist()
            else:
                arr = list(ids_tensor)
            # 정수 변환
            return [int(x) for x in arr]
        except Exception:
            return None
    except Exception:
        return None

def draw_direction_arrows(frame, result, arrow_color=(0, 255, 255), arrow_len=40):
    """Ultralytics OBB 결과를 사용해 각 객체의 진행 방향 화살표를 그린다.
    - frame: np.ndarray, 주석이 입혀진 프레임
    - result: Ultralytics YOLO 결과 객체 (r)
    - arrow_color: (B, G, R)
    - arrow_len: 화살표 길이 (px)
    return: result 별 방향값(angle)
    """
    try:
        if not hasattr(result, 'obb') or result.obb is None:
            return None
        xywhr = getattr(result.obb, 'xywhr', None)
        xyxyxyxy = getattr(result.obb, 'xyxyxyxy', None)
        if xywhr is None or xyxyxyxy is None:
            return None
        num_objs = len(xywhr)
        angles = []
        for i in range(num_objs):
            try:
                pts = xyxyxyxy[i].cpu().numpy().reshape(-1, 2)
                cx = int(np.mean(pts[:, 0]))
                cy = int(np.mean(pts[:, 1]))

                w_px = float(xywhr[i][2].item())
                h_px = float(xywhr[i][3].item())
                angle = float(xywhr[i][4].item())
                # 긴 변을 진행 축으로 가정
                if w_px < h_px:
                    angle += math.pi / 2.0

                ex = int(cx + arrow_len * math.cos(angle))
                ey = int(cy + arrow_len * math.sin(angle))
                cv2.arrowedLine(frame, (cx, cy), (ex, ey), arrow_color, 2, tipLength=0.3)
                angles.append(angle)
            except Exception:
                angles.append(None)
                continue
        return angles
    except Exception:
        return None

def draw_boxes(frame, result, angle, box_color=(0, 255, 255), box_thickness=2, box_size=(250, 100)):
    """
    중심점을 기준으로 angle(라디안) 방향으로 회전된 고정 크기 박스를 폴리라인으로 그린다.
    - box_size: 박스 크기 (w, h)
    - angle: 각 객체별 방향값(radian) 리스트 또는 None
    return: xyxyxyxy 폴리라인 좌표, 중심점 좌표
    """
    try:
        if not hasattr(result, 'obb') or result.obb is None:
            return None
        xywhr = getattr(result.obb, 'xywhr', None)
        xyxyxyxy = getattr(result.obb, 'xyxyxyxy', None)
        if xywhr is None or xyxyxyxy is None:
            return None
        num_objs = len(xywhr)
        xyxyxyxy_list = []
        center_list = []
        for i in range(num_objs):
            try:
                pts = xyxyxyxy[i].cpu().numpy().reshape(-1, 2)
                cx = float(np.mean(pts[:, 0]))
                cy = float(np.mean(pts[:, 1]))
                w = box_size[0]
                h = box_size[1]
                # 각도 추출 (angle이 None이면 obb에서 angle 사용)
                if angle is not None and angle[i] is not None:
                    theta = angle[i]
                else:
                    # obb의 angle 값 사용
                    theta = float(xywhr[i][4].item())
                    # 긴 변이 세로일 때 90도 보정
                    w_px = float(xywhr[i][2].item())
                    h_px = float(xywhr[i][3].item())
                    if w_px < h_px:
                        theta += math.pi / 2.0
                # 중심 기준 회전 사각형 꼭짓점 계산
                box_corners = np.array([
                    [-w/2, -h/2],
                    [ w/2, -h/2],
                    [ w/2,  h/2],
                    [-w/2,  h/2]
                ])
                # 회전 행렬 적용
                rot = np.array([
                    [np.cos(theta), -np.sin(theta)],
                    [np.sin(theta),  np.cos(theta)]
                ])
                rotated = np.dot(box_corners, rot.T)
                # 중심 이동
                rotated += np.array([cx, cy])
                pts_poly = rotated.astype(np.int32).reshape((-1, 1, 2))
                cv2.polylines(frame, [pts_poly], isClosed=True, color=box_color, thickness=box_thickness)
                xyxyxyxy_list.append(pts_poly)
                center_list.append((cx, cy))
            except Exception:
                continue
        return xyxyxyxy_list, center_list
    except Exception:
        return None

def draw_center_id(frame, center_list, ids,
                   font_scale=1.2, thickness=3,
                   text_color=(0, 255, 0), outline_color=(0, 0, 0)):
    """
    각 박스의 중심에 트래킹 ID를 표시한다.
    return: None
    """
    try:
        if not center_list or not ids or len(center_list) != len(ids):
            return None
        font = cv2.FONT_HERSHEY_SIMPLEX
        for i, (center, obj_id) in enumerate(zip(center_list, ids)):
            cx, cy = int(center[0]), int(center[1])
            plate = track_id_to_plate.get(int(obj_id), None)
            text = str(plate) if plate is not None else f"ID:{int(obj_id)}"
            text_size, baseline = cv2.getTextSize(text, font, font_scale, thickness)
            text_w, text_h = text_size
            org = (int(cx - text_w / 2), int(cy + text_h / 2))
            # 가독성을 위한 외곽선 → 본문 순으로 두 번 그리기
            cv2.putText(frame, text, org, font, font_scale, outline_color, thickness + 2, cv2.LINE_AA)
            cv2.putText(frame, text, org, font, font_scale, text_color, thickness, cv2.LINE_AA)
        return None
    except Exception:
        return None

def get_detections_with_ids(result):
    """결과 객체에서 (cx, cy, id) 리스트를 추출한다.
    - OBB(id, xyxyxyxy)가 우선, 없으면 boxes(id, xyxy)
    return: [{ 'cx': float, 'cy': float, 'id': int }, ...]
    """
    detections = []
    try:
        # OBB 우선
        if hasattr(result, 'obb') and result.obb is not None:
            ids_t = getattr(result.obb, 'id', None)
            polys = getattr(result.obb, 'xyxyxyxy', None)
            if ids_t is not None and polys is not None:
                ids = ids_t.cpu().numpy().tolist() if hasattr(ids_t, 'cpu') else list(ids_t)
                for i, tid in enumerate(ids):
                    try:
                        pts = polys[i].cpu().numpy().reshape(-1, 2)
                        cx = float(np.mean(pts[:, 0])); cy = float(np.mean(pts[:, 1]))
                        detections.append({'cx': cx, 'cy': cy, 'id': int(tid)})
                    except Exception:
                        continue
                if detections:
                    return detections
        # boxes 보조
        if hasattr(result, 'boxes') and result.boxes is not None:
            ids_t = getattr(result.boxes, 'id', None)
            xyxy = getattr(result.boxes, 'xyxy', None)
            if ids_t is not None and xyxy is not None:
                ids = ids_t.cpu().numpy().tolist() if hasattr(ids_t, 'cpu') else list(ids_t)
                arr = xyxy.cpu().numpy() if hasattr(xyxy, 'cpu') else np.array(xyxy)
                for i, tid in enumerate(ids):
                    try:
                        x1, y1, x2, y2 = arr[i]
                        cx = float((x1 + x2) / 2.0); cy = float((y1 + y2) / 2.0)
                        detections.append({'cx': cx, 'cy': cy, 'id': int(tid)})
                    except Exception:
                        continue
    except Exception:
        return []
    return detections

def draw_plate_labels(frame, detections,
                      font_scale=1.2, thickness=3,
                      text_color=(0, 255, 0), outline_color=(0, 0, 0)):
    """(cx, cy, id) 리스트를 받아 각 위치에 번호판 텍스트를 그린다."""
    try:
        if not detections:
            return
        font = cv2.FONT_HERSHEY_SIMPLEX
        for det in detections:
            cx, cy, tid = int(det['cx']), int(det['cy']), int(det['id'])
            plate = track_id_to_plate.get(tid)
            text = str(plate) if plate else f"ID:{tid}"
            text_size, _ = cv2.getTextSize(text, font, font_scale, thickness)
            text_w, text_h = text_size
            org = (int(cx - text_w / 2), int(cy + text_h / 2))
            cv2.putText(frame, text, org, font, font_scale, outline_color, thickness + 2, cv2.LINE_AA)
            cv2.putText(frame, text, org, font, font_scale, text_color, thickness, cv2.LINE_AA)
    except Exception:
        pass

def draw_parking_zones(frame, zones_norm, state=None,
                       color_free=(0, 0, 255), color_busy=(0, 200, 0),
                       thickness=2, font_scale=0.8, font_thickness=2):
    """
    정규화된 주차구역 좌표를 실제 프레임에 그린다. 상태에 따라 색상/라벨을 그린다.
    - state: zone_id -> { 'occupant_id': int|None, 'parked_since': float|None, 'last_inside_ts': float|None }
    """
    h, w = frame.shape[:2]
    font = cv2.FONT_HERSHEY_SIMPLEX
    for zone in zones_norm:
        zid = zone["id"]
        x1n, y1n, x2n, y2n = zone["rect"]
        x1, y1 = int(x1n * w), int(y1n * h)
        x2, y2 = int(x2n * w), int(y2n * h)
        is_busy = bool(state and state.get(zid, {}).get("occupant_id") is not None)
        color = color_busy if is_busy else color_free
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
        # 라벨
        label = zid
        if is_busy:
            occ = state[zid]["occupant_id"]
            plate = track_id_to_plate.get(int(occ))
            label = f"{zid} - {plate if plate else f'ID:{occ}'}"
        text_size, _ = cv2.getTextSize(label, font, font_scale, font_thickness)
        text_w, text_h = text_size
        org = (x1 + 5, y1 + text_h + 5)
        cv2.putText(frame, label, org, font, font_scale, (0, 0, 0), font_thickness + 2, cv2.LINE_AA)
        cv2.putText(frame, label, org, font, font_scale, color, font_thickness, cv2.LINE_AA)

def update_parking_states(center_list, ids, zones_norm, frame_w, frame_h, now_ts):
    """
    주차/출차 상태를 갱신한다.
    - center_list: [(cx, cy), ...]
    - ids: [track_id, ...]
    - zones_norm: 주차 구역 리스트
    - now_ts: 현재 시각 (time.time())
    전역 zone_state, zone_candidates를 갱신한다.
    """
    if not center_list or not ids:
        # 프레임에 객체가 없는 경우: 출차 판정 타이머만 진행
        for zone in zones_norm:
            zid = zone["id"]
            st = zone_state[zid]
            if st["occupant_id"] is not None and st["last_inside_ts"] is not None:
                if now_ts - st["last_inside_ts"] >= EXIT_THRESHOLD_SECONDS:
                    st["occupant_id"] = None
                    st["parked_since"] = None
                    st["last_inside_ts"] = None
        return

    # 현재 프레임에서 구역별로 안에 있는 id 집합을 계산
    zone_ids_inside = {zone["id"]: [] for zone in zones_norm}
    for (cx, cy), tid in zip(center_list, ids):
        for zone in zones_norm:
            if point_in_norm_rect(cx, cy, frame_w, frame_h, zone["rect"]):
                zone_ids_inside[zone["id"]].append(int(tid))

    # 각 구역 상태 갱신
    for zone in zones_norm:
        zid = zone["id"]
        inside_ids = zone_ids_inside[zid]
        st = zone_state[zid]
        candidates = zone_candidates[zid]

        # 주차 중인 차량이 있는 경우: 이 차량이 아직 안에 있는지 체크
        if st["occupant_id"] is not None:
            occ = st["occupant_id"]
            if occ in inside_ids:
                st["last_inside_ts"] = now_ts
            else:
                # 구역 밖으로 나간 상태가 EXIT_THRESHOLD를 넘으면 출차
                if st["last_inside_ts"] is None:
                    st["last_inside_ts"] = now_ts
                elif now_ts - st["last_inside_ts"] >= EXIT_THRESHOLD_SECONDS:
                    st["occupant_id"] = None
                    st["parked_since"] = None
                    st["last_inside_ts"] = None
            # 주차 중이면 후보 초기화(점유 중 다른 후보는 무시)
            zone_candidates[zid] = {}
            continue

        # 주차 중인 차량이 없는 경우: 후보 dwell 누적/판정
        # 후보 dwell 시간 갱신
        # 프레임 내 inside인 id는 누적, 밖으로 나간 id는 후보에서 제거
        current_inside_set = set(inside_ids)
        # 제거 대상
        for cand_id in list(candidates.keys()):
            if cand_id not in current_inside_set:
                del candidates[cand_id]
        # 추가/유지
        for tid in inside_ids:
            if tid not in candidates:
                candidates[tid] = now_ts  # 최초 inside 시각
        # 임계 초과 후보가 있으면 가장 오래 머문 id를 점유자로 선정
        ready = [tid for tid, since_ts in candidates.items() if now_ts - since_ts >= ENTER_THRESHOLD_SECONDS]
        if ready:
            # 가장 오래 머문 id
            best_tid = max(ready, key=lambda t: now_ts - candidates[t])
            st["occupant_id"] = best_tid
            st["parked_since"] = now_ts
            st["last_inside_ts"] = now_ts
            zone_candidates[zid] = {}

def draw_parking_status_panel(frame, zones_norm, state,
                              anchor=(10, 10),
                              font_scale=0.6,
                              text_thickness=1,
                              padding=10,
                              bg_alpha=0.4,
                              bg_color=(0, 0, 0),
                              text_color=(255, 255, 255)):
    """
    화면 좌측 상단(anchor)에 주차 상태 요약 패널을 그린다.
    - Occupied/Free 개수, Free 구역 목록, 각 구역 점유 현황 일부 표시
    """
    try:
        font = cv2.FONT_HERSHEY_SIMPLEX
        zone_ids = [z["id"] for z in zones_norm]
        occupied = []
        free = []
        for zid in zone_ids:
            occ = state.get(zid, {}).get("occupant_id")
            if occ is None:
                free.append(zid)
            else:
                occupied.append((zid, occ))

        lines = []
        lines.append("Parking Status")
        lines.append(f"Occupied: {len(occupied)}  Free: {len(free)}")
        if free:
            lines.append("Free: " + ", ".join(free[:8]) + ("..." if len(free) > 8 else ""))
        # 각 구역 한 줄 요약 (최대 6줄)
        max_zone_lines = 10
        for zid in zone_ids[:max_zone_lines]:
            occ = state.get(zid, {}).get("occupant_id")
            if occ is None:
                line = f"{zid}: Free"
            else:
                plate = track_id_to_plate.get(int(occ))
                line = f"{zid}: {plate if plate else f'ID {occ}'}"
            lines.append(line)

        # 패널 크기 계산
        text_sizes = [cv2.getTextSize(t, font, font_scale, text_thickness)[0] for t in lines]
        line_height = max(h for (w, h) in text_sizes) + 6
        panel_w = max(w for (w, h) in text_sizes) + padding * 2
        panel_h = line_height * len(lines) + padding * 2
        x, y = anchor

        # 반투명 배경
        overlay = frame.copy()
        cv2.rectangle(overlay, (x, y), (x + panel_w, y + panel_h), bg_color, thickness=-1)
        cv2.addWeighted(overlay, bg_alpha, frame, 1 - bg_alpha, 0, dst=frame)

        # 텍스트 그리기
        cursor_y = y + padding + (line_height - (text_sizes[0][1]))
        for i, text in enumerate(lines):
            cv2.putText(frame, text, (x + padding, cursor_y), font, font_scale, text_color, text_thickness, cv2.LINE_AA)
            cursor_y += line_height
    except Exception:
        pass

results = model.track(
    source=video_path,
    stream=True,
    imgsz=1080,
    conf=0.1,
    iou=0.6,
    tracker=_tracker_cfg,
    visualize=False,
)

window_name = 'Tracking'
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

# 최대 창 크기 지정 (원하는 값으로 조정)
max_width, max_height = 640, 640

for r in results:
    # im0 = r.plot()  # 주석(박스/라벨) 그려진 프레임 대신 원본 프레임 사용
    im0 = r.orig_img.copy() if hasattr(r, 'orig_img') else None
    if im0 is None:
        continue

    # 시각화 함수 직접 호출
    angles = draw_direction_arrows(im0, r)
    xyxyxyxy_list, center_list = draw_boxes(im0, r, angles)
    ids = extract_track_ids(r)
    # 새로 탐지된 id에 번호판 매핑 보장
    ensure_plate_mapping(ids)
    # 번호판 텍스트를 중심에 표시
    dets = get_detections_with_ids(r)
    draw_plate_labels(im0, dets)

    # 주차구역 시각화
    # 주차 상태 업데이트
    now_ts = time.time()
    h_full, w_full = im0.shape[:2]
    update_parking_states(center_list, ids, PARKING_ZONES_NORM, w_full, h_full, now_ts)

    # 주차구역 시각화(상태 반영)
    draw_parking_zones(im0, PARKING_ZONES_NORM, state=zone_state, thickness=2)
    # 좌측 상단 주차 상태 패널 (크기 확대)
    draw_parking_status_panel(
        im0,
        PARKING_ZONES_NORM,
        zone_state,
        anchor=(10, 10),
        font_scale=0.9,
        text_thickness=2,
        padding=16,
        bg_alpha=0.55,
    )

    # JSON 스냅샷 저장 (주기적으로)
    try:
        now = time.time()
        if now - _last_snapshot_ts >= _snapshot_interval_s:
            snapshot = assemble_snapshot(center_list, xyxyxyxy_list, ids, PARKING_ZONES_NORM, w_full, h_full)
            save_status_snapshot(snapshot, SNAPSHOT_PATH)
            _last_snapshot_ts = now
    except Exception:
        pass
    

    # 오버레이 이후 리사이즈 적용
    h, w = im0.shape[:2]
    scale = min(max_width / w, max_height / h, 1.0)
    if scale < 1.0:
        im_disp = cv2.resize(im0, (int(w * scale), int(h * scale)))
    else:
        im_disp = im0

    cv2.imshow(window_name, im_disp)
    if cv2.waitKey(1) & 0xFF == 27:  # ESC로 종료
        break

cv2.destroyAllWindows()
