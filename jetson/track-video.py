from ultralytics import YOLO
import cv2
from pathlib import Path
import math
import numpy as np
import time
import random
from collections import deque
import json
import websocket

# ------------------------------
# 주차구역 정규화 좌표 (parking_check copy.py에서 복사)
# ------------------------------
PARKING_ZONES_NORM = [
    {"id": "b1", "rect": [0.371914, 0.00823, 0.45216, 0.26749]},
    {"id": "b2", "rect": [0.448302, 0.010974, 0.527778, 0.268861]},
    {"id": "b3", "rect": [0.522377, 0.006859, 0.603395, 0.266118]},
    {"id": "c1", "rect": [0.633488, 0.005487, 0.709105, 0.237311]},
    {"id": "c2", "rect": [0.706019, 0.006859, 0.783951, 0.242798]},
    {"id": "c3", "rect": [0.783951, 0.009602, 0.858796, 0.238683]},
    {"id": "a1", "rect": [0.374228, 0.727023, 0.450617, 0.969822]},
    {"id": "a2", "rect": [0.448302, 0.727023, 0.524691, 0.973937]},
    {"id": "a3", "rect": [0.523148, 0.72428, 0.60108, 0.973937]},
    {"id": "a4", "rect": [0.631173, 0.73251, 0.707562, 0.971193]},
    {"id": "a5", "rect": [0.704475, 0.733882, 0.781636, 0.975309]},
]

ENTER_THRESHOLD_SECONDS = 3.0
EXIT_THRESHOLD_SECONDS = 2.0

zone_state = {
    z["id"]: {"occupant_id": None, "parked_since": None, "last_inside_ts": None}
    for z in PARKING_ZONES_NORM
}
zone_candidates = {z["id"]: {} for z in PARKING_ZONES_NORM}

ENG_PLATE_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def generate_plate():
    letters = "".join(random.choices(ENG_PLATE_LETTERS, k=3))
    digits = random.randint(1000, 9999)
    return f"{letters}-{digits}"


license_queues = [deque([generate_plate() for _ in range(10)]) for _ in range(20)]
_rr_queue_index = 0
track_id_to_plate = {}


def get_next_plate_from_queues():
    global _rr_queue_index
    n = len(license_queues)
    for i in range(n):
        idx = (_rr_queue_index + i) % n
        if license_queues[idx]:
            plate = license_queues[idx].popleft()
            _rr_queue_index = (idx + 1) % n
            return plate
    return generate_plate()


def ensure_plate_mapping(ids):
    if not ids:
        return
    for tid in ids:
        tid_int = int(tid)
        if tid_int not in track_id_to_plate:
            track_id_to_plate[tid_int] = get_next_plate_from_queues()


RESERVED_ZONES = set()

SNAPSHOT_PATH = str(Path(__file__).with_name("status_snapshot.json"))
_last_snapshot_ts = 0.0
_snapshot_interval_s = 0.5


def assemble_slot_status(zones_norm, state, reserved_upper_set):
    slot = {}
    for zone in zones_norm:
        zid_lower = zone["id"]
        zid_upper = zid_lower.upper()
        if zid_upper in reserved_upper_set:
            slot[zid_upper] = "reserved"
        elif state.get(zid_lower, {}).get("occupant_id") is not None:
            slot[zid_upper] = "occupied"
        else:
            slot[zid_upper] = "free"
    return slot


def vehicle_state_from_zone_state(track_id):
    if track_id is None:
        return "running"
    for st in zone_state.values():
        if st.get("occupant_id") == int(track_id):
            return "parked"
    return "running"


def assemble_snapshot(center_list, xyxyxyxy_list, ids, zones_norm, frame_w, frame_h):
    slot = assemble_slot_status(zones_norm, zone_state, RESERVED_ZONES)
    vehicles = []
    if center_list and ids:
        for idx, ((cx, cy), tid) in enumerate(zip(center_list, ids)):
            plate = track_id_to_plate.get(int(tid))
            state_str = vehicle_state_from_zone_state(tid)
            corners = None
            try:
                pts_poly = xyxyxyxy_list[idx]
                pts = pts_poly.reshape(-1, 2)
                corners = [[float(x), float(y)] for x, y in pts]
            except Exception:
                corners = None
            suggested = None
            vehicles.append(
                {
                    "plate": plate if plate else f"ID{int(tid)}",
                    "center": {"x": float(cx), "y": float(cy)},
                    "corners": corners,
                    "state": state_str,
                    "suggested": suggested,
                }
            )
    snapshot = {"slot": slot, "vehicles": vehicles}
    return snapshot


def save_status_snapshot(snapshot, path=SNAPSHOT_PATH):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def point_in_norm_rect(cx, cy, frame_w, frame_h, rect_norm):
    x1n, y1n, x2n, y2n = rect_norm
    x1, y1 = x1n * frame_w, y1n * frame_h
    x2, y2 = x2n * frame_w, y2n * frame_h
    return x1 <= cx <= x2 and y1 <= cy <= y2


video_path = "data/video_part_1.mp4"

model = YOLO(
    "last.pt",
)

_tracker_cfg = str(Path(__file__).with_name("bytetrack.yaml"))

WSS_URL = "wss://i13e102.p.ssafy.io/ws/car-position/"

OUTPUT_WIDTH = 900
OUTPUT_HEIGHT = 550


def connect_ws():
    while True:
        try:
            if hasattr(websocket, "create_connection"):
                ws = websocket.create_connection(WSS_URL)
            elif hasattr(websocket, "WebSocket") and hasattr(
                websocket.WebSocket, "connect"
            ):
                ws = websocket.WebSocket()
                ws.connect(WSS_URL)
            else:
                raise RuntimeError(
                    "websocket-client 모듈이 필요합니다 (pip install websocket-client)."
                )
            print(f"[WebSocket] Connected to {WSS_URL}")
            return ws
        except Exception as e:
            print(f"[WebSocket] Connection failed: {e}. Retrying in 1s...")
            time.sleep(1)


ws = connect_ws()


def extract_track_ids(result):
    try:
        ids_tensor = None
        if hasattr(result, "obb") and result.obb is not None:
            ids_tensor = getattr(result.obb, "id", None)
        if ids_tensor is None and hasattr(result, "boxes") and result.boxes is not None:
            ids_tensor = getattr(result.boxes, "id", None)

        if ids_tensor is None:
            return None

        try:
            if hasattr(ids_tensor, "cpu"):
                arr = ids_tensor.cpu().numpy().tolist()
            else:
                arr = list(ids_tensor)
            return [int(x) for x in arr]
        except Exception:
            return None
    except Exception:
        return None


def draw_direction_arrows(frame, result, arrow_color=(0, 255, 255), arrow_len=40):
    try:
        if not hasattr(result, "obb") or result.obb is None:
            return None
        xywhr = getattr(result.obb, "xywhr", None)
        xyxyxyxy = getattr(result.obb, "xyxyxyxy", None)
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
                if w_px < h_px:
                    angle += math.pi / 2.0

                ex = int(cx + arrow_len * math.cos(angle))
                ey = int(cy + arrow_len * math.sin(angle))
                cv2.arrowedLine(
                    frame, (cx, cy), (ex, ey), arrow_color, 2, tipLength=0.3
                )
                angles.append(angle)
            except Exception:
                angles.append(None)
                continue
        return angles
    except Exception:
        return None


def draw_boxes(
    frame, result, angle, box_color=(0, 255, 255), box_thickness=2, box_size=(250, 100)
):
    try:
        if not hasattr(result, "obb") or result.obb is None:
            return None
        xywhr = getattr(result.obb, "xywhr", None)
        xyxyxyxy = getattr(result.obb, "xyxyxyxy", None)
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
                if angle is not None and angle[i] is not None:
                    theta = angle[i]
                else:
                    theta = float(xywhr[i][4].item())
                    w_px = float(xywhr[i][2].item())
                    h_px = float(xywhr[i][3].item())
                    if w_px < h_px:
                        theta += math.pi / 2.0
                box_corners = np.array(
                    [[-w / 2, -h / 2], [w / 2, -h / 2], [w / 2, h / 2], [-w / 2, h / 2]]
                )
                rot = np.array(
                    [[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]]
                )
                rotated = np.dot(box_corners, rot.T)
                rotated += np.array([cx, cy])
                pts_poly = rotated.astype(np.int32).reshape((-1, 1, 2))
                cv2.polylines(
                    frame,
                    [pts_poly],
                    isClosed=True,
                    color=box_color,
                    thickness=box_thickness,
                )
                xyxyxyxy_list.append(pts_poly)
                center_list.append((cx, cy))
            except Exception:
                continue
        return xyxyxyxy_list, center_list
    except Exception:
        return None


def draw_center_id(
    frame,
    center_list,
    ids,
    font_scale=1.2,
    thickness=3,
    text_color=(0, 255, 0),
    outline_color=(0, 0, 0),
):
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
            cv2.putText(
                frame,
                text,
                org,
                font,
                font_scale,
                outline_color,
                thickness + 2,
                cv2.LINE_AA,
            )
            cv2.putText(
                frame, text, org, font, font_scale, text_color, thickness, cv2.LINE_AA
            )
        return None
    except Exception:
        return None


def get_detections_with_ids(result):
    detections = []
    try:
        if hasattr(result, "obb") and result.obb is not None:
            ids_t = getattr(result.obb, "id", None)
            polys = getattr(result.obb, "xyxyxyxy", None)
            if ids_t is not None and polys is not None:
                ids = (
                    ids_t.cpu().numpy().tolist()
                    if hasattr(ids_t, "cpu")
                    else list(ids_t)
                )
                for i, tid in enumerate(ids):
                    try:
                        pts = polys[i].cpu().numpy().reshape(-1, 2)
                        cx = float(np.mean(pts[:, 0]))
                        cy = float(np.mean(pts[:, 1]))
                        detections.append({"cx": cx, "cy": cy, "id": int(tid)})
                    except Exception:
                        continue
                if detections:
                    return detections
        if hasattr(result, "boxes") and result.boxes is not None:
            ids_t = getattr(result.boxes, "id", None)
            xyxy = getattr(result.boxes, "xyxy", None)
            if ids_t is not None and xyxy is not None:
                ids = (
                    ids_t.cpu().numpy().tolist()
                    if hasattr(ids_t, "cpu")
                    else list(ids_t)
                )
                arr = xyxy.cpu().numpy() if hasattr(xyxy, "cpu") else np.array(xyxy)
                for i, tid in enumerate(ids):
                    try:
                        x1, y1, x2, y2 = arr[i]
                        cx = float((x1 + x2) / 2.0)
                        cy = float((y1 + y2) / 2.0)
                        detections.append({"cx": cx, "cy": cy, "id": int(tid)})
                    except Exception:
                        continue
    except Exception:
        return []
    return detections


def draw_plate_labels(
    frame,
    detections,
    font_scale=1.2,
    thickness=3,
    text_color=(0, 255, 0),
    outline_color=(0, 0, 0),
):
    try:
        if not detections:
            return
        font = cv2.FONT_HERSHEY_SIMPLEX
        for det in detections:
            cx, cy, tid = int(det["cx"]), int(det["cy"]), int(det["id"])
            plate = track_id_to_plate.get(tid)
            text = str(plate) if plate else f"ID:{tid}"
            text_size, _ = cv2.getTextSize(text, font, font_scale, thickness)
            text_w, text_h = text_size
            org = (int(cx - text_w / 2), int(cy + text_h / 2))
            cv2.putText(
                frame,
                text,
                org,
                font,
                font_scale,
                outline_color,
                thickness + 2,
                cv2.LINE_AA,
            )
            cv2.putText(
                frame, text, org, font, font_scale, text_color, thickness, cv2.LINE_AA
            )
    except Exception:
        pass


def build_wss_payload_from_result(result, frame_w, frame_h):
    payload = []
    try:
        obb = getattr(result, "obb", None)
        if obb is None:
            return payload

        ids_t = getattr(obb, "id", None)
        xywhr = getattr(obb, "xywhr", None)
        corners = getattr(obb, "xyxyxyxy", None)
        if ids_t is None or xywhr is None or corners is None:
            return payload

        ids_list = (
            ids_t.cpu().numpy().tolist() if hasattr(ids_t, "cpu") else list(ids_t)
        )
        num = min(len(ids_list), len(xywhr), len(corners))
        for i in range(num):
            tid = ids_list[i]
            if tid is None:
                continue
            try:
                cx = float(xywhr[i][0].item())
                cy = float(xywhr[i][1].item())
            except Exception:
                arr = (
                    xywhr[i].cpu().numpy().tolist()
                    if hasattr(xywhr[i], "cpu")
                    else list(xywhr[i])
                )
                cx, cy = float(arr[0]), float(arr[1])

            try:
                c8 = corners[i].cpu().numpy().flatten().tolist()
            except Exception:
                c8 = np.array(corners[i]).reshape(-1).tolist()

            if frame_w and frame_h:
                s = min(
                    float(OUTPUT_WIDTH) / float(frame_w),
                    float(OUTPUT_HEIGHT) / float(frame_h),
                )
                out_w = float(frame_w) * s
                out_h = float(frame_h) * s
                off_x = (float(OUTPUT_WIDTH) - out_w) / 2.0
                off_y = (float(OUTPUT_HEIGHT) - out_h) / 2.0

                cx = cx * s + off_x
                cy = cy * s + off_y
                for idx in range(0, len(c8), 2):
                    c8[idx] = float(c8[idx]) * s + off_x
                    c8[idx + 1] = float(c8[idx + 1]) * s + off_y

                cx = max(0.0, min(cx, float(OUTPUT_WIDTH - 1)))
                cy = max(0.0, min(cy, float(OUTPUT_HEIGHT - 1)))
                for idx in range(0, len(c8), 2):
                    c8[idx] = max(0.0, min(float(c8[idx]), float(OUTPUT_WIDTH - 1)))
                    c8[idx + 1] = max(
                        0.0, min(float(c8[idx + 1]), float(OUTPUT_HEIGHT - 1))
                    )

            payload.append(
                {
                    "track_id": int(tid),
                    "center": [round(cx, 1), round(cy, 1)],
                    "corners": [round(float(v), 1) for v in c8],
                }
            )
    except Exception:
        return []
    return payload


def draw_parking_zones(
    frame,
    zones_norm,
    state=None,
    color_free=(0, 0, 255),
    color_busy=(0, 200, 0),
    thickness=2,
    font_scale=0.8,
    font_thickness=2,
):
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
        label = zid
        if is_busy:
            occ = state[zid]["occupant_id"]
            plate = track_id_to_plate.get(int(occ))
            label = f"{zid} - {plate if plate else f'ID:{occ}'}"
        text_size, _ = cv2.getTextSize(label, font, font_scale, font_thickness)
        text_w, text_h = text_size
        org = (x1 + 5, y1 + text_h + 5)
        cv2.putText(
            frame,
            label,
            org,
            font,
            font_scale,
            (0, 0, 0),
            font_thickness + 2,
            cv2.LINE_AA,
        )
        cv2.putText(
            frame, label, org, font, font_scale, color, font_thickness, cv2.LINE_AA
        )


def update_parking_states(center_list, ids, zones_norm, frame_w, frame_h, now_ts):
    if not center_list or not ids:
        for zone in zones_norm:
            zid = zone["id"]
            st = zone_state[zid]
            if st["occupant_id"] is not None and st["last_inside_ts"] is not None:
                if now_ts - st["last_inside_ts"] >= EXIT_THRESHOLD_SECONDS:
                    st["occupant_id"] = None
                    st["parked_since"] = None
                    st["last_inside_ts"] = None
        return

    zone_ids_inside = {zone["id"]: [] for zone in zones_norm}
    for (cx, cy), tid in zip(center_list, ids):
        for zone in zones_norm:
            if point_in_norm_rect(cx, cy, frame_w, frame_h, zone["rect"]):
                zone_ids_inside[zone["id"]].append(int(tid))

    for zone in zones_norm:
        zid = zone["id"]
        inside_ids = zone_ids_inside[zid]
        st = zone_state[zid]
        candidates = zone_candidates[zid]

        if st["occupant_id"] is not None:
            occ = st["occupant_id"]
            if occ in inside_ids:
                st["last_inside_ts"] = now_ts
            else:
                if st["last_inside_ts"] is None:
                    st["last_inside_ts"] = now_ts
                elif now_ts - st["last_inside_ts"] >= EXIT_THRESHOLD_SECONDS:
                    st["occupant_id"] = None
                    st["parked_since"] = None
                    st["last_inside_ts"] = None
            zone_candidates[zid] = {}
            continue

        current_inside_set = set(inside_ids)
        for cand_id in list(candidates.keys()):
            if cand_id not in current_inside_set:
                del candidates[cand_id]
        for tid in inside_ids:
            if tid not in candidates:
                candidates[tid] = now_ts
        ready = [
            tid
            for tid, since_ts in candidates.items()
            if now_ts - since_ts >= ENTER_THRESHOLD_SECONDS
        ]
        if ready:
            best_tid = max(ready, key=lambda t: now_ts - candidates[t])
            st["occupant_id"] = best_tid
            st["parked_since"] = now_ts
            st["last_inside_ts"] = now_ts
            zone_candidates[zid] = {}


def draw_parking_status_panel(
    frame,
    zones_norm,
    state,
    anchor=(10, 10),
    font_scale=0.6,
    text_thickness=1,
    padding=10,
    bg_alpha=0.4,
    bg_color=(0, 0, 0),
    text_color=(255, 255, 255),
):
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
            lines.append(
                "Free: " + ", ".join(free[:8]) + ("..." if len(free) > 8 else "")
            )
        max_zone_lines = 10
        for zid in zone_ids[:max_zone_lines]:
            occ = state.get(zid, {}).get("occupant_id")
            if occ is None:
                line = f"{zid}: Free"
            else:
                plate = track_id_to_plate.get(int(occ))
                line = f"{zid}: {plate if plate else f'ID {occ}'}"
            lines.append(line)

        text_sizes = [
            cv2.getTextSize(t, font, font_scale, text_thickness)[0] for t in lines
        ]
        line_height = max(h for (w, h) in text_sizes) + 6
        panel_w = max(w for (w, h) in text_sizes) + padding * 2
        panel_h = line_height * len(lines) + padding * 2
        x, y = anchor

        overlay = frame.copy()
        cv2.rectangle(
            overlay, (x, y), (x + panel_w, y + panel_h), bg_color, thickness=-1
        )
        cv2.addWeighted(overlay, bg_alpha, frame, 1 - bg_alpha, 0, dst=frame)

        cursor_y = y + padding + (line_height - (text_sizes[0][1]))
        for i, text in enumerate(lines):
            cv2.putText(
                frame,
                text,
                (x + padding, cursor_y),
                font,
                font_scale,
                text_color,
                text_thickness,
                cv2.LINE_AA,
            )
            cursor_y += line_height
    except Exception:
        pass


def track_loop():
    global _last_snapshot_ts, ws

    results = model.track(
        source=video_path,
        stream=True,
        imgsz=1080,
        conf=0.1,
        iou=0.6,
        tracker=_tracker_cfg,
        visualize=False,
    )

    window_name = "Tracking"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    max_width, max_height = 900, 550

    for r in results:
        im0 = r.orig_img.copy() if hasattr(r, "orig_img") else None
        if im0 is None:
            continue

        angles = draw_direction_arrows(im0, r)
        xyxyxyxy_list, center_list = draw_boxes(im0, r, angles)
        ids = extract_track_ids(r)
        ensure_plate_mapping(ids)
        dets = get_detections_with_ids(r)
        draw_plate_labels(im0, dets)

        now_ts = time.time()
        h_full, w_full = im0.shape[:2]
        update_parking_states(
            center_list, ids, PARKING_ZONES_NORM, w_full, h_full, now_ts
        )

        draw_parking_zones(im0, PARKING_ZONES_NORM, state=zone_state, thickness=2)
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

        try:
            now = time.time()
            if now - _last_snapshot_ts >= _snapshot_interval_s:
                payload = build_wss_payload_from_result(r, w_full, h_full)
                msg = json.dumps(payload, ensure_ascii=False)
                print(">>> Sending via WSS:", msg)
                try:
                    ws.send(msg)
                    print("[WebSocket] 전송 성공")
                except Exception as e:
                    print(f"[WebSocket] 전송 실패: {e}. Reconnecting...")
                    try:
                        ws.close()
                    except Exception:
                        pass
                    ws = connect_ws()
                    try:
                        ws.send(msg)
                        time.sleep(0.1)
                        print("[WebSocket] 재전송 성공")
                    except Exception as e2:
                        print(f"[WebSocket] 재전송 실패: {e2}")

                _last_snapshot_ts = now
        except Exception:
            pass

        h, w = im0.shape[:2]
        scale = min(max_width / w, max_height / h, 1.0)
        if scale < 1.0:
            im_disp = cv2.resize(im0, (int(w * scale), int(h * scale)))
        else:
            im_disp = im0

        cv2.imshow(window_name, im_disp)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    track_loop()
