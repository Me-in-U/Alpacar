from __future__ import annotations

import asyncio
import json
import math
import os
import queue
import threading
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Callable, Awaitable, Type

import cv2
import numpy as np
import websocket
from ultralytics import YOLO
try:
    from ml.recommender import recommend_best_zone
    from ml.step_predictor import load_model
except Exception:
    recommend_best_zone = None  # type: ignore
    load_model = None  # type: ignore

# =============================
# Configuration
# =============================

# VIDEO_PATH = 0
VIDEO_PATH = "data/video_part_1.mp4"
MODEL_PATH = "last (2).pt"
TRACKER_CFG_NAME = "bytetrack.yaml"
WSS_URL = "wss://i13e102.p.ssafy.io/ws/jetson/"


OUTPUT_WIDTH = 900
OUTPUT_HEIGHT = 550

IMG_SIZE = 1080
CONF_THRES = 0.2
IOU_THRES = 0.6

ENTER_THRESHOLD_SECONDS = 3.0
EXIT_THRESHOLD_SECONDS = 2.0

SNAPSHOT_INTERVAL_S = 0.5
SNAPSHOT_PATH = str(Path(__file__).with_name("status_snapshot.json"))

# Parking zones (normalized)
PARKING_ZONES_NORM: List[Dict[str, Any]] = [
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



# =============================
# Utilities
# =============================

def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def point_in_norm_rect(
    cx: float, cy: float, frame_w: int, frame_h: int, rect_norm: Sequence[float]
) -> bool:
    x1n, y1n, x2n, y2n = rect_norm
    x1, y1 = x1n * frame_w, y1n * frame_h
    x2, y2 = x2n * frame_w, y2n * frame_h
    return x1 <= cx <= x2 and y1 <= cy <= y2


# =============================
# Plate Manager
# =============================


class PlateManager:
    def __init__(self) -> None:
        self.plate_queue: deque[str] = deque()
        self.track_to_plate: Dict[int, str] = {}
        self.plate_to_size_class: Dict[str, str] = {}

    def enqueue_plate(self, plate: str) -> None:
        if not plate:
            return
        self.plate_queue.append(plate)

    def ensure_mapping(self, ids: Optional[Iterable[int]]) -> None:
        if not ids:
            return
        for tid in ids:
            tid_int = int(tid)
            if tid_int not in self.track_to_plate and self.plate_queue:
                plate = self.plate_queue.popleft()
                self.track_to_plate[tid_int] = plate

    def get(self, tid: int) -> Optional[str]:
        return self.track_to_plate.get(int(tid))

    def get_track_id_by_plate(self, plate: str) -> Optional[int]:
        for track_id, mapped_plate in self.track_to_plate.items():
            if mapped_plate == plate:
                return int(track_id)
        return None

    def get_size_class(self, plate: str) -> Optional[str]:
        return self.plate_to_size_class.get(plate, None)


# =============================
# Parking Manager
# =============================

@dataclass
class ZoneState:
    occupant_id: Optional[int] = None
    parked_since: Optional[float] = None
    last_inside_ts: Optional[float] = None


class ParkingManager:
    def __init__(self, zones_norm: List[Dict[str, Any]]) -> None:
        self.zones_norm = zones_norm
        self.state: Dict[str, ZoneState] = {z["id"]: ZoneState() for z in zones_norm}
        self.candidates: Dict[str, Dict[int, float]] = {z["id"]: {} for z in zones_norm}

    def update(
        self,
        centers: Sequence[Tuple[float, float]],
        ids: Sequence[int],
        frame_w: int,
        frame_h: int,
        now_ts: float,
    ) -> None:
        if not centers or not ids:
            for zid, st in self.state.items():
                if st.occupant_id is not None and st.last_inside_ts is not None:
                    if now_ts - st.last_inside_ts >= EXIT_THRESHOLD_SECONDS:
                        self.state[zid] = ZoneState()
            return

        zone_ids_inside: Dict[str, List[int]] = {z["id"]: [] for z in self.zones_norm}
        for (cx, cy), tid in zip(centers, ids):
            for zone in self.zones_norm:
                if point_in_norm_rect(cx, cy, frame_w, frame_h, zone["rect"]):
                    zone_ids_inside[zone["id"]].append(int(tid))

        for zone in self.zones_norm:
            zid = zone["id"]
            inside_ids = zone_ids_inside[zid]
            st = self.state[zid]
            cands = self.candidates[zid]

            if st.occupant_id is not None:
                if st.occupant_id in inside_ids:
                    st.last_inside_ts = now_ts
                else:
                    st.last_inside_ts = st.last_inside_ts or now_ts
                    if now_ts - st.last_inside_ts >= EXIT_THRESHOLD_SECONDS:
                        self.state[zid] = ZoneState()
                self.candidates[zid] = {}
                continue

            current_inside = set(inside_ids)
            for cand_id in list(cands.keys()):
                if cand_id not in current_inside:
                    del cands[cand_id]
            for tid in inside_ids:
                if tid not in cands:
                    cands[tid] = now_ts

            ready = [tid for tid, since in cands.items() if now_ts - since >= ENTER_THRESHOLD_SECONDS]
            if ready:
                best_tid = max(ready, key=lambda t: now_ts - cands[t])
                self.state[zid] = ZoneState(
                    occupant_id=best_tid, parked_since=now_ts, last_inside_ts=now_ts
                )
                self.candidates[zid] = {}

    def assemble_slot_status(self, reserved_upper: set[str]) -> Dict[str, str]:
        slot: Dict[str, str] = {}
        for z in self.zones_norm:
            zid_upper = z["id"].upper()
            st = self.state[z["id"]]
            if zid_upper in reserved_upper:
                slot[zid_upper] = "reserved"
            elif st.occupant_id is not None:
                slot[zid_upper] = "occupied"
            else:
                slot[zid_upper] = "free"
        return slot

    def occupant_to_zone_upper(self) -> Dict[int, str]:
        mapping: Dict[int, str] = {}
        for zone in self.zones_norm:
            zid = zone["id"]
            st = self.state.get(zid)
            if st and st.occupant_id is not None:
                mapping[int(st.occupant_id)] = zid.upper()
        return mapping


# =============================
# WebSocket Wrapper
# =============================

class WSClient:
    """WebSocketApp 기반 클라이언트. 백그라운드 스레드에서 run_forever."""

    def __init__(self, url: str) -> None:
        self.url = url
        self.wsapp: Optional[websocket.WebSocketApp] = None
        self._queue: "queue.Queue[str]" = queue.Queue()
        self._thread: Optional[threading.Thread] = None
        self._stop_flag = threading.Event()
        self._connected = threading.Event()
        self._start_background()

    def _on_open(self, ws) -> None: 
        self._connected.set()
        print(f"[WebSocket] Connected to {self.url}")

    def _on_message(self, ws, message: str) -> None: 
        try:
            self._queue.put_nowait(message)
        except Exception:
            pass

    def _on_error(self, ws, error) -> None: 
        print(f"[WebSocket] error: {error}")

    def _on_close(self, ws, code, msg) -> None: 
        self._connected.clear()
        print(f"[WebSocket] closed code={code} msg={msg}")

    def _run_forever_loop(self) -> None:
        while not self._stop_flag.is_set():
            try:
                self.wsapp = websocket.WebSocketApp(
                    self.url,
                    on_open=self._on_open,
                    on_message=self._on_message,
                    on_error=self._on_error,
                    on_close=self._on_close,
                )
                self.wsapp.run_forever(ping_interval=20, ping_timeout=10)
            except Exception as e:
                print(f"[WebSocket] run_forever error: {e}")
            if not self._stop_flag.is_set():
                print("[WebSocket] Reconnecting in 1s...")
                time.sleep(1)

    def _start_background(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_flag.clear()
        self._thread = threading.Thread(target=self._run_forever_loop, daemon=True)
        self._thread.start()

    def send_json(self, obj: Any) -> None:
        payload = json.dumps(obj, ensure_ascii=False)
        try:
            if self.wsapp and self._connected.is_set() and self.wsapp.sock and self.wsapp.sock.connected:
                self.wsapp.send(payload)
            else:
                raise RuntimeError("socket not connected")
        except Exception as e:
            print(f"[WebSocket] send failed: {e}")



    async def recv(self) -> str:
        return await asyncio.to_thread(self._queue.get)

    def close(self) -> None:
        try:
            self._stop_flag.set()
            if self.wsapp is not None:
                try:
                    self.wsapp.close()
                except Exception:
                    pass
            if self._thread and self._thread.is_alive():
                pass
        except Exception:
            pass

# =============================
# Drawing / Visualization
# =============================

class Visualizer:
    def __init__(self, plate_mgr: PlateManager, parking: ParkingManager) -> None:
        self.pm = plate_mgr
        self.prk = parking

    def draw_direction_arrows(
        self, frame: np.ndarray, result: Any, arrow_len: int = 40
    ) -> List[Optional[float]]:
        try:
            if not hasattr(result, "obb") or result.obb is None:
                return []
            xywhr = getattr(result.obb, "xywhr", None)
            xyxyxyxy = getattr(result.obb, "xyxyxyxy", None)
            if xywhr is None or xyxyxyxy is None:
                return []
            num_objs = len(xywhr)
            angles: List[Optional[float]] = []
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
                    cv2.arrowedLine(frame, (cx, cy), (ex, ey), (0, 255, 255), 2, tipLength=0.3)
                    angles.append(angle)
                except Exception:
                    angles.append(None)
            return angles
        except Exception:
            return []

    def draw_boxes(
        self,
        frame: np.ndarray,
        result: Any,
        angles: Sequence[Optional[float]],
        boxes_size: List[Tuple[int, int]],
    ) -> Tuple[List[np.ndarray], List[Tuple[float, float]]]:
        xyxyxyxy_list: List[np.ndarray] = []
        center_list: List[Tuple[float, float]] = []
        try:
            if not hasattr(result, "obb") or result.obb is None:
                return xyxyxyxy_list, center_list
            xywhr = getattr(result.obb, "xywhr", None)
            xyxyxyxy = getattr(result.obb, "xyxyxyxy", None)
            if xywhr is None or xyxyxyxy is None:
                return xyxyxyxy_list, center_list
            num_objs = len(xywhr)
            for i in range(num_objs):
                try:
                    w, h = boxes_size[i]
                    pts = xyxyxyxy[i].cpu().numpy().reshape(-1, 2)
                    cx = float(np.mean(pts[:, 0]))
                    cy = float(np.mean(pts[:, 1]))

                    angle_i = angles[i] if i < len(angles) else None
                    theta = (
                        angle_i
                        if angle_i is not None
                        else float(xywhr[i][4].item())
                    )
                    w_px = float(xywhr[i][2].item())
                    h_px = float(xywhr[i][3].item())
                    if angle_i is None and w_px < h_px:
                        theta += math.pi / 2.0

                    box_corners = np.array(
                        [[-w / 2, -h / 2], [w / 2, -h / 2], [w / 2, h / 2], [-w / 2, h / 2]]
                    )
                    rot = np.array(
                        [[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]]
                    )
                    rotated = box_corners @ rot.T
                    rotated += np.array([cx, cy])
                    pts_poly = rotated.astype(np.int32).reshape((-1, 1, 2))
                    cv2.polylines(frame, [pts_poly], True, (0, 255, 255), 2)
                    xyxyxyxy_list.append(pts_poly)
                    center_list.append((cx, cy))
                except Exception:
                    continue
            return xyxyxyxy_list, center_list
        except Exception:
            return xyxyxyxy_list, center_list

    def draw_plate_labels(self, frame: np.ndarray, detections: Sequence[Dict[str, float]]) -> None:
        if not detections:
            return
        font = cv2.FONT_HERSHEY_SIMPLEX
        for det in detections:
            cx, cy, tid = int(det["cx"]), int(det["cy"]), int(det["id"])
            text = self.pm.get(tid) or f"ID:{tid}"
            text_size, _ = cv2.getTextSize(text, font, 1.2, 3)
            text_w, text_h = text_size
            org = (int(cx - text_w / 2), int(cy + text_h / 2))
            cv2.putText(frame, text, org, font, 1.2, (0, 0, 0), 5, cv2.LINE_AA)
            cv2.putText(frame, text, org, font, 1.2, (0, 255, 0), 3, cv2.LINE_AA)

    def draw_parking_zones(self, frame: np.ndarray) -> None:
        h, w = frame.shape[:2]
        font = cv2.FONT_HERSHEY_SIMPLEX
        for zone in self.prk.zones_norm:
            zid = zone["id"]
            x1n, y1n, x2n, y2n = zone["rect"]
            x1, y1, x2, y2 = int(x1n * w), int(y1n * h), int(x2n * w), int(y2n * h)
            st = self.prk.state[zid]
            is_busy = st.occupant_id is not None
            color = (0, 200, 0) if is_busy else (0, 0, 255)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            label = zid
            if is_busy:
                plate = self.pm.get(st.occupant_id or -1)
                label = f"{zid} - {plate if plate else f'ID:{st.occupant_id}'}"
            text_size, _ = cv2.getTextSize(label, font, 0.8, 2)
            org = (x1 + 5, y1 + text_size[1] + 5)
            cv2.putText(frame, label, org, font, 0.8, (0, 0, 0), 4, cv2.LINE_AA)
            cv2.putText(frame, label, org, font, 0.8, color, 2, cv2.LINE_AA)

    def draw_status_panel(
        self,
        frame: np.ndarray,
        anchor: Tuple[int, int] = (10, 10),
        reserved_upper: Optional[set[str]] = None,
    ) -> None:
        try:
            font = cv2.FONT_HERSHEY_SIMPLEX
            zone_ids = [z["id"] for z in self.prk.zones_norm]
            slot_map = self.prk.assemble_slot_status(reserved_upper or set())
            reserved_list: List[str] = []
            occupied: List[Tuple[str, int]] = []
            free: List[str] = []
            for zid in zone_ids:
                status = slot_map.get(zid.upper(), "free")
                if status == "reserved":
                    reserved_list.append(zid)
                elif status == "occupied":
                    occ = self.prk.state[zid].occupant_id
                    occupied.append((zid, occ if occ is not None else -1))
                else:
                    free.append(zid)

            lines: List[str] = []
            lines.append("Parking Status")
            lines.append(f"Reserved: {len(reserved_list)}  Occupied: {len(occupied)}  Free: {len(free)}")
            if free:
                lines.append(
                    "Free: " + ", ".join(free[:8]) + ("..." if len(free) > 8 else "")
                )
            if reserved_list:
                lines.append(
                    "Reserved: " + ", ".join(reserved_list[:8]) + ("..." if len(reserved_list) > 8 else "")
                )
            for zid in zone_ids[:10]:
                status = slot_map.get(zid.upper(), "free")
                if status == "reserved":
                    lines.append(f"{zid}: Reserved")
                elif status == "occupied":
                    occ = self.prk.state[zid].occupant_id
                    if occ is None:
                        lines.append(f"{zid}: Occupied")
                    else:
                        plate = self.pm.get(occ)
                        lines.append(f"{zid}: {plate if plate else f'ID {occ}'}")
                else:
                    lines.append(f"{zid}: Free")

            sizes = [cv2.getTextSize(t, font, 0.9, 2)[0] for t in lines]
            line_h = max(h for (_, h) in sizes) + 6
            panel_w = max(w for (w, _) in sizes) + 32
            panel_h = line_h * len(lines) + 20
            x, y = anchor

            overlay = frame.copy()
            cv2.rectangle(overlay, (x, y), (x + panel_w, y + panel_h), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, dst=frame)

            cursor_y = y + 20
            for text in lines:
                cv2.putText(
                    frame, text, (x + 16, cursor_y), font, 0.9, (255, 255, 255), 2, cv2.LINE_AA
                )
                cursor_y += line_h
        except Exception:
            pass


# =============================
# Detection / Postprocessing
# =============================

def extract_track_ids(result: Any) -> Optional[List[int]]:
    try:
        ids_tensor = None
        if hasattr(result, "obb") and result.obb is not None:
            ids_tensor = getattr(result.obb, "id", None)
        if ids_tensor is None:
            return None
        if hasattr(ids_tensor, "cpu"):
            return [int(x) for x in ids_tensor.cpu().numpy().tolist()]
        return [int(x) for x in list(ids_tensor)]
    except Exception:
        return None


def get_detections_with_ids(result: Any) -> List[Dict[str, float]]:
    detections: List[Dict[str, float]] = []
    try:
        if hasattr(result, "obb") and result.obb is not None:
            ids_t = getattr(result.obb, "id", None)
            polys = getattr(result.obb, "xyxyxyxy", None)
            if ids_t is not None and polys is not None:
                ids = ids_t.cpu().numpy().tolist() if hasattr(ids_t, "cpu") else list(ids_t)
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
    except Exception:
        return []
    return detections


def extract_angles_by_id(result: Any) -> Dict[int, float]:
    """현재 프레임의 트랙 ID별 차량 각도(rad)를 추출한다."""
    id_to_angle: Dict[int, float] = {}
    try:
        if not hasattr(result, "obb") or result.obb is None:
            return id_to_angle
        ids_t = getattr(result.obb, "id", None)
        xywhr = getattr(result.obb, "xywhr", None)
        if ids_t is None or xywhr is None:
            return id_to_angle
        ids = ids_t.cpu().numpy().tolist() if hasattr(ids_t, "cpu") else list(ids_t)
        for i, tid in enumerate(ids):
            try:
                try:
                    w_px = float(xywhr[i][2].item())
                    h_px = float(xywhr[i][3].item())
                    theta = float(xywhr[i][4].item())
                except Exception:
                    arr = (
                        xywhr[i].cpu().numpy().tolist() if hasattr(xywhr[i], "cpu") else list(xywhr[i])
                    )
                    w_px, h_px, theta = float(arr[2]), float(arr[3]), float(arr[4])
                if w_px < h_px:
                    theta += math.pi / 2.0
                id_to_angle[int(tid)] = theta
            except Exception:
                continue
    except Exception:
        return id_to_angle
    return id_to_angle

def build_logging_snapshot(
    payload: List[Dict[str, Any]],
    plate_mgr: PlateManager,
    parking: "ParkingManager",
    reserved_upper: set[str],
) -> Dict[str, Any]:
    slot_map = parking.assemble_slot_status(reserved_upper)

    occupant_to_zone_upper: Dict[int, str] = {}
    for zone in parking.zones_norm:
        zid = zone["id"]
        state = parking.state[zid]
        if state.occupant_id is not None:
            occupant_to_zone_upper[int(state.occupant_id)] = zid.upper()

    vehicles_log: List[Dict[str, Any]] = []
    for det in payload:
        tid = int(det.get("track_id"))
        plate = plate_mgr.get(tid) or f"ID:{tid}"
        cx, cy = det.get("center", [0.0, 0.0])
        c8 = det.get("corners", [])
        corners_pairs: List[List[float]] = []
        if isinstance(c8, list) and len(c8) >= 8:
            corners_pairs = [
                [float(c8[0]), float(c8[1])],
                [float(c8[2]), float(c8[3])],
                [float(c8[4]), float(c8[5])],
                [float(c8[6]), float(c8[7])],
            ]

        is_parked = tid in occupant_to_zone_upper
        state_str = "parked" if is_parked else "running"
        suggested_zone = occupant_to_zone_upper.get(tid, "")
        
        vehicles_log.append(
            {
                "plate": plate,
                "center": {"x": float(cx), "y": float(cy)},
                "corners": corners_pairs,
                "state": state_str,
                "suggested": suggested_zone,
            }
        )

    return {
        "message_type": "car_position", 
        "slot": slot_map, 
        "vehicles": vehicles_log
        }


def build_wss_payload_from_result(
    result: Any, frame_w: int, frame_h: int
) -> List[Dict[str, Any]]:
    payload: List[Dict[str, Any]] = []
    try:
        obb = getattr(result, "obb", None)
        if obb is None:
            return payload
        ids_t = getattr(obb, "id", None)
        xywhr = getattr(obb, "xywhr", None)
        corners = getattr(obb, "xyxyxyxy", None)
        if ids_t is None or xywhr is None or corners is None:
            return payload
        ids_list = ids_t.cpu().numpy().tolist() if hasattr(ids_t, "cpu") else list(ids_t)
        num = min(len(ids_list), len(xywhr), len(corners))
        for i in range(num):
            tid = ids_list[i]
            if tid is None:
                continue

            try:
                pts = corners[i].cpu().numpy().reshape(-1, 2)
            except Exception:
                pts = np.array(corners[i]).reshape(-1, 2)
            cx = float(np.mean(pts[:, 0]))
            cy = float(np.mean(pts[:, 1]))

            try:
                w_px = float(xywhr[i][2].item())
                h_px = float(xywhr[i][3].item())
                theta = float(xywhr[i][4].item())
            except Exception:
                arr = (
                    xywhr[i].cpu().numpy().tolist() if hasattr(xywhr[i], "cpu") else list(xywhr[i])
                )
                w_px, h_px, theta = float(arr[2]), float(arr[3]), float(arr[4])
            if w_px < h_px:
                theta += math.pi / 2.0

            w_box, h_box = 250.0, 100.0
            box_corners = np.array(
                [[-w_box / 2.0, -h_box / 2.0], [w_box / 2.0, -h_box / 2.0], [w_box / 2.0, h_box / 2.0], [-w_box / 2.0, h_box / 2.0]]
            )
            rot = np.array([[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]])
            rotated = box_corners @ rot.T
            rotated += np.array([cx, cy])
            c8 = rotated.reshape(-1).tolist()

            if frame_w and frame_h:
                s = min(
                    float(OUTPUT_WIDTH) / float(frame_w),
                    float(OUTPUT_HEIGHT) / float(frame_h),
                )
                out_w = float(frame_w) * s
                out_h = float(frame_h) * s
                off_x = (float(OUTPUT_WIDTH) - out_w) / 2.0
                off_y = (float(OUTPUT_HEIGHT) - out_h) / 2.0

                cx = clamp(cx * s + off_x, 0.0, float(OUTPUT_WIDTH - 1))
                cy = clamp(cy * s + off_y, 0.0, float(OUTPUT_HEIGHT - 1))
                for idx in range(0, len(c8), 2):
                    c8[idx] = clamp(float(c8[idx]) * s + off_x, 0.0, float(OUTPUT_WIDTH - 1))
                    c8[idx + 1] = clamp(
                        float(c8[idx + 1]) * s + off_y, 0.0, float(OUTPUT_HEIGHT - 1)
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


# =============================
# Main Application
# =============================

class TrackerApp:
    def __init__(self, ws: WSClient) -> None:
        self.model = None
        self.tracker_cfg = str(Path(__file__).with_name(TRACKER_CFG_NAME))
        self.ws = ws
        self.plate_mgr = PlateManager()
        self.parking = ParkingManager(PARKING_ZONES_NORM)
        self.vis = Visualizer(self.plate_mgr, self.parking)
        self._last_snapshot_ts = 0.0
        self._reserved_upper: set[str] = set()
        self._assigned_by_plate: Dict[str, str] = {}
        self._size_class_by_plate: Dict[str, str] = {}
        self._last_slot_map: Dict[str, str] = {}
        self._completed_zones: set[str] = set()
        self._last_angle_by_id: Dict[int, float] = {}
        self._last_zone_to_tid: Dict[str, int] = {}

        self.recommender_model = None
        # in-file EventBus (lightweight)
        self._event_queue: "asyncio.Queue[Dict[str, Any]]" = asyncio.Queue()
        self._event_handlers: Dict[str, List[Callable[[Dict[str, Any]], Awaitable[None]]]] = {}
        self._event_loop_task: Optional[asyncio.Task] = None
        try:
            if load_model is not None:
                default_path = Path(__file__).parents[1] / "ml" / "artifacts" / "best_step_model.joblib"
                model_path = Path(os.getenv("RECOMMENDER_MODEL_PATH", str(default_path)))
                if model_path.exists():
                    self.recommender_model = load_model(str(model_path))
                    print(f"[Recommender] 모델 로드: {model_path}")
                else:
                    print(f"[Recommender] 모델 파일 없음: {model_path}")
        except Exception as e:
            print(f"[Recommender] 모델 로드 실패: {e}")

    # ============ In-file EventBus ============
    def _on(self, message_type: str, handler: Callable[[Dict[str, Any]], Awaitable[None]]) -> None:
        self._event_handlers.setdefault(message_type, []).append(handler)

    async def _emit(self, payload: Dict[str, Any]) -> None:
        # payload MUST contain 'message_type'
        await self._event_queue.put(payload)

    async def _event_loop(self) -> None:
        while True:
            payload = await self._event_queue.get()
            msg_type = str(payload.get("message_type", ""))
            for handler in self._event_handlers.get(msg_type, []):
                try:
                    await handler(payload)
                except Exception as e:
                    print(f"[EventBus] handler error for {msg_type}: {e}")

    async def _send_ws(self, payload: Dict[str, Any]) -> None:
        await asyncio.to_thread(self.ws.send_json, payload)

    def _calculate_parking_score(self, occupant_tid: int, zone_id_lower: str) -> float:
        """주차 완료 시 점수를 계산한다."""
        angle_rad = float(self._last_angle_by_id.get(occupant_tid, 0.0))
        angle_deg = abs(math.degrees(angle_rad)) % 180.0
        if angle_deg > 90.0:
            angle_deg = 180.0 - angle_deg

        if angle_deg <= 5.0:
            base = 100.0 - (angle_deg * 4.0)
        elif angle_deg <= 10.0:
            base = 80.0 - ((angle_deg - 5.0) * 8.0)
        else:
            base = max(0.0, 40.0 - ((angle_deg - 10.0) * 2.0))

        st = self.parking.state.get(zone_id_lower)
        time_adj = 0.0
        if st and st.parked_since is not None:
            now_ts = time.time()
            actual_sec = float(max(0.0, now_ts - st.parked_since))
            expected_sec = float(os.getenv("EXPECTED_PARKING_TIME_S", "10"))
            delta = actual_sec - expected_sec
            time_adj = float(clamp(-0.5 * delta, -10.0, 10.0))

        score = clamp(base + time_adj, 0.0, 100.0)
        return float(round(score, 1))

    def _build_features_for_free_zones(self, size_class: Optional[str], slot_map: Dict[str, str]) -> List[Dict]:
        # size_class 문자열을 (폭[m], 길이[m])로 파싱
        width_m, length_m = 2.5, 5.0
        if size_class:
            try:
                s = size_class.strip().lower()
                if "," in s:
                    width_m, length_m = map(float, s.split(","))
                elif s == "compact":
                    width_m, length_m = 2.0, 4.2
                elif s == "midsize":
                    width_m, length_m = 2.5, 5.0
                elif s == "suv":
                    width_m, length_m = 2.8, 5.2
            except Exception:
                pass

        features: List[Dict] = []
        for i in range(5):
            feature = {
                "left_occupied": 0,
                "left_angle": 0.0,
                "left_offset": 0.0,
                "left_size": 2,
                "left_width": 2.5,
                "left_length": 5.0,
                "left_has_pillar": 0,
                "right_occupied": 0,
                "right_angle": 0.0,
                "right_offset": 0.0,
                "right_size": 2,
                "right_width": 2.5,
                "right_length": 5.0,
                "right_has_pillar": 0,
                "controlled_x": 10.0 + i,
                "controlled_y": 20.0 + i,
                "controlled_width": width_m,
                "controlled_length": length_m,
                "zone_id": f"zone_{i+1}"
            }
            features.append(feature)

        return features

    def get_box_size(self, size_class: Optional[str]) -> Tuple[int, int]:
        """size_class에 따라 박스 크기를 반환한다."""
        if size_class:
            try:
                if "," in size_class:
                    width, length = map(float, size_class.split(","))
                    return (int(width * 100), int(length * 100))
                elif size_class.lower() == "compact":
                    return (200, 80)
                elif size_class.lower() == "midsize":
                    return (250, 100)
                elif size_class.lower() == "suv":
                    return (300, 120)
            except Exception:
                pass
        return (250, 100)

    def extract_boxes_size(self, track_ids: List[int]) -> List[Tuple[int, int]]:
        """track ID 목록에 대해 각각의 박스 크기를 계산하여 반환한다."""
        boxes_size = []
        for track_id in track_ids:
            license_plate = self.plate_mgr.get(track_id)
            if license_plate:
                size_class = self.plate_mgr.plate_to_size_class.get(license_plate)
                box_size = self.get_box_size(size_class)
            else:
                box_size = self.get_box_size(None)
            boxes_size.append(box_size)
        return boxes_size

    async def _listen_assignment_request(self) -> None:
        while True:
            try:
                msg = await self.ws.recv()
                try:
                    data = json.loads(msg)
                except Exception:
                    continue
                if not isinstance(data, dict):
                    continue
                if data.get("message_type") == "request_assignment":
                    print(f"서버에서 주차 할당 요청: {data}")
                    slot_map = self._get_slot_map()

                    license_plate = str(data.get("license_plate") or "")
                    if license_plate:
                        self.plate_mgr.enqueue_plate(license_plate)
                    size_class = str(data.get("size_class") or "")

                    if license_plate and size_class:
                        self.plate_mgr.plate_to_size_class[license_plate] = size_class
                        self._size_class_by_plate[license_plate] = size_class

                    suggested_zone = ""
                    if self.recommender_model is not None and recommend_best_zone is not None:
                        try:
                            feats = self._build_features_for_free_zones(size_class, slot_map)
                            print(f"[Recommender] 추천 구역 예측: {feats}")
                            best = recommend_best_zone(self.recommender_model, feats)
                            if best and isinstance(best, dict):
                                suggested_zone = str(best.get("zone_id") or "")
                        except Exception as e:
                            print(f"[Recommender] 예측 실패: {e}")

                    assigned_zone_upper = self._choose_zone_for_assignment(slot_map, size_class)

                    await self._reserve_zone(license_plate, assigned_zone_upper, slot_map)

                    await self._emit({
                        "message_type": "assignment",
                        "license_plate": license_plate,
                        "assignment": assigned_zone_upper,
                    })
            except Exception:
                break

    def _resize_for_display(
        self, im: np.ndarray, max_w: int = OUTPUT_WIDTH, max_h: int = OUTPUT_HEIGHT
    ) -> np.ndarray:
        h, w = im.shape[:2]
        scale = min(max_w / w, max_h / h, 1.0)
        if scale < 1.0:
            return cv2.resize(im, (int(w * scale), int(h * scale)))
        return im

    def _log_slot_changes(self, slot_map_now: Dict[str, str]) -> None:
        try:
            for zid_upper, cur in sorted(slot_map_now.items()):
                prev = self._last_slot_map.get(zid_upper)
                if prev is None and cur is not None:
                    print(f"[Slot] {zid_upper}: None -> {cur}")
                elif prev is not None and prev != cur:
                    print(f"[Slot] {zid_upper}: {prev} -> {cur}")
        except Exception:
            pass

    async def _send_snapshot(self, result_obj: Any | None, frame_w: int, frame_h: int) -> None:
        try:
            if result_obj is not None:
                payload = build_wss_payload_from_result(result_obj, frame_w, frame_h)
            else:
                payload = []
            await asyncio.to_thread(self.ws.send_json, 
                build_logging_snapshot(payload, self.plate_mgr, self.parking, self._reserved_upper)
            )
            slot_map_now = self.parking.assemble_slot_status(self._reserved_upper)
            self._log_slot_changes(slot_map_now)
            self._last_slot_map = slot_map_now.copy()
        except Exception:
            pass

    def _get_slot_map(self) -> Dict[str, str]:
        return self.parking.assemble_slot_status(self._reserved_upper)

    def _get_occupant_map(self) -> Dict[int, str]:
        return self.parking.occupant_to_zone_upper()

    def _get_zone_to_tid_map(self) -> Dict[str, int]:
        mapping: Dict[str, int] = {}
        for zone in self.parking.zones_norm:
            zid_lower = zone["id"]
            st = self.parking.state.get(zid_lower)
            if st and st.occupant_id is not None:
                mapping[zid_lower.upper()] = int(st.occupant_id)
        return mapping

    async def _handle_exit_events(self) -> None:
        """구역이 비워진 경우에만 출차 이벤트를 전송한다."""
        try:
            cur_zone_to_tid = self._get_zone_to_tid_map()
            for zid_upper, prev_tid in list(self._last_zone_to_tid.items()):
                cur_tid = cur_zone_to_tid.get(zid_upper)
                if cur_tid is None:
                    plate = self.plate_mgr.get(prev_tid) or ""
                    if plate:
                        await self._emit({
                            "message_type": "exit",
                            "license_plate": plate,
                            "zone": zid_upper,
                        })
            self._last_zone_to_tid = cur_zone_to_tid
        except Exception:
            pass

    def _choose_zone_for_assignment(
        self, slot_map: Dict[str, str], size_class: Optional[str]
    ) -> str:
        suggested_zone = ""
        if self.recommender_model is not None and recommend_best_zone is not None:
            try:
                feats = self._build_features_for_free_zones(size_class or "", slot_map)
                best = recommend_best_zone(self.recommender_model, feats)
                if best and isinstance(best, dict):
                    suggested_zone = str(best.get("zone_id") or "").strip().upper()
            except Exception:
                suggested_zone = ""
        if suggested_zone and slot_map.get(suggested_zone) == "free":
            return suggested_zone
        for zid_upper, state in slot_map.items():
            if state == "free":
                return zid_upper
        return ""

    async def _reserve_zone(self, license_plate: str, assigned_zone_upper: str, slot_map: Dict[str, str]) -> None:
        if not assigned_zone_upper:
            return
        if slot_map.get(assigned_zone_upper) != "free":
            return
        self._reserved_upper.add(assigned_zone_upper)
        self._completed_zones.discard(assigned_zone_upper)
        if license_plate:
            self._assigned_by_plate[license_plate] = assigned_zone_upper
        print(f"[Reservation] 예약 생성: plate={license_plate} zone={assigned_zone_upper}")
        await self._send_snapshot(None, 0, 0)

    async def _handle_parking_completion(self) -> None:
        """예약된 구역에 배정 차량이 실제로 주차 완료되었을 때 이벤트를 전송하고 예약을 해제한다."""
        try:
            zone_to_assigned_plate: Dict[str, str] = {z: p for p, z in self._assigned_by_plate.items()}
            for zid_upper in list(self._reserved_upper):
                if zid_upper in self._completed_zones:
                    continue
                zid_lower = zid_upper.lower()
                st = self.parking.state.get(zid_lower)
                if not st or st.occupant_id is None:
                    continue
                assigned_vehicle = zone_to_assigned_plate.get(zid_upper)
                if not assigned_vehicle:
                    continue
                occupant_tid = int(st.occupant_id)
                occupant_vehicle = self.plate_mgr.get(occupant_tid) or ""
                if occupant_vehicle and occupant_vehicle == assigned_vehicle:
                    score = self._calculate_parking_score(occupant_tid, zid_lower)

                    await self._emit({
                        "message_type": "score",
                        "license_plate": assigned_vehicle,
                        "score": round(score, 4),
                    })
                    self._reserved_upper.discard(zid_upper)
                    self._assigned_by_plate.pop(assigned_vehicle, None)
                    self._size_class_by_plate.pop(assigned_vehicle, None)
                    self._completed_zones.add(zid_upper)
                    print(f"[ParkingCompleted] plate={assigned_vehicle} zone={zid_upper}")
                    await self._send_snapshot(None, 0, 0)

        except Exception:
            pass

    def _handle_mispark_release(self, occupant_to_zone_upper: Dict[int, str]) -> None:
        try:
            vehicles_to_release: List[str] = []
            for plate, assigned_zone_upper in list(self._assigned_by_plate.items()):
                tid = self.plate_mgr.get_track_id_by_plate(plate)
                if tid is None:
                    continue
                actual_zone_upper = occupant_to_zone_upper.get(int(tid))
                if actual_zone_upper is None:
                    continue
                if actual_zone_upper != assigned_zone_upper:
                    self._reserved_upper.discard(assigned_zone_upper)
                    print(
                        f"[Reservation] 다른 구역 주차로 예약 해제: plate={plate} zone={assigned_zone_upper} actual={actual_zone_upper}"
                    )
                    vehicles_to_release.append(plate)
            for plate in vehicles_to_release:
                self._assigned_by_plate.pop(plate, None)
                self._size_class_by_plate.pop(plate, None)
        except Exception:
            pass

    async def _handle_preemption_and_reassign(self) -> None:
        try:
            zone_to_assigned_plate: Dict[str, str] = {zone: plate for plate, zone in self._assigned_by_plate.items()}
            for zid_upper in list(self._reserved_upper):
                zid_lower = zid_upper.lower()
                st = self.parking.state.get(zid_lower)
                if st is None or st.occupant_id is None:
                    continue
                assigned_plate = zone_to_assigned_plate.get(zid_upper)
                occupant_tid = int(st.occupant_id)
                occupant_plate = self.plate_mgr.get(occupant_tid)
                if assigned_plate is None or occupant_plate != assigned_plate:
                    self._reserved_upper.discard(zid_upper)
                    if assigned_plate:
                        self._assigned_by_plate.pop(assigned_plate, None)
                        self._size_class_by_plate.pop(assigned_plate, None)

                    print(
                        f"[Preempted] zone={zid_upper} by={occupant_plate or occupant_tid} (assigned={assigned_plate or ''})"
                    )
                    if assigned_plate:
                        slot_map_now = self._get_slot_map()
                        size_class = self._size_class_by_plate.get(assigned_plate, "")
                        new_zone_upper = self._choose_zone_for_assignment(slot_map_now, size_class)
                        if new_zone_upper and slot_map_now.get(new_zone_upper) == "free":
                            self._reserved_upper.add(new_zone_upper)
                            self._assigned_by_plate[assigned_plate] = new_zone_upper
                            await self._emit({
                                "message_type": "re-assignment",
                                "license_plate": assigned_plate,
                                "assignment": new_zone_upper,
                            })
                            print(f"[Reservation] 재할당: plate={assigned_plate} -> {new_zone_upper}")
        except Exception:
            pass

    async def run(self) -> None:
        # EventBus 시작 및 기본 핸들러 등록
        if self._event_loop_task is None:
            self._event_loop_task = asyncio.create_task(self._event_loop())
            # 핸들러: exit, score, assignment, re-assignment → WS 전송
            self._on("exit", self._send_ws)
            self._on("score", self._send_ws)
            self._on("assignment", self._send_ws)
            self._on("re-assignment", self._send_ws)

        self.model = YOLO(MODEL_PATH)
        results = self.model.track(
            source=VIDEO_PATH,
            stream=True,
            imgsz=IMG_SIZE,
            conf=CONF_THRES,
            iou=IOU_THRES,
            tracker=self.tracker_cfg,
            visualize=False,
            verbose=False,
        )

        window_name = "Tracking"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        prev_ts = time.time()
        fps_ema = 0.0

        try:
            listener_task = asyncio.create_task(self._listen_assignment_request())

            for r in results:
                try:
                    im0 = r.orig_img if hasattr(r, "orig_img") else None
                    if im0 is None:
                        continue
                    angles = self.vis.draw_direction_arrows(im0, r)
                    
                    ids = extract_track_ids(r) or []
                    self.plate_mgr.ensure_mapping(ids)

                    dets = get_detections_with_ids(r)
                    self.vis.draw_plate_labels(im0, dets)

                    now_ts = time.time()
                    h_full, w_full = im0.shape[:2]
                    
                    boxes_size = self.extract_boxes_size(ids)

                    _, centers = self.vis.draw_boxes(im0, r, angles, boxes_size=boxes_size)
                    
                    self.parking.update(centers, ids, w_full, h_full, now_ts)

                    await self._handle_exit_events()

                    self.vis.draw_parking_zones(im0)
                    self.vis.draw_status_panel(im0, (10, 10), self._reserved_upper)
                    try:
                        self._last_angle_by_id.update(extract_angles_by_id(r))
                    except Exception:
                        pass

                    await self._handle_parking_completion()

                    self._handle_mispark_release(self._get_occupant_map())
                    await self._handle_preemption_and_reassign()

                    if now_ts - self._last_snapshot_ts >= SNAPSHOT_INTERVAL_S:
                        await self._send_snapshot(r, w_full, h_full)
                        self._last_snapshot_ts = now_ts

                    cur = time.time()
                    dt = max(1e-6, cur - prev_ts)
                    prev_ts = cur
                    inst_fps = 1.0 / dt
                    fps_ema = inst_fps if fps_ema == 0.0 else (0.9 * fps_ema + 0.1 * inst_fps)
                    cv2.putText(im0, f"FPS: {fps_ema:.1f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2, cv2.LINE_AA)

                    im_disp = self._resize_for_display(im0, OUTPUT_WIDTH, OUTPUT_HEIGHT)
                    cv2.imshow(window_name, im_disp)
                    if cv2.waitKey(1) & 0xFF == 27:
                        break
                    try:
                        if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                            break
                    except Exception:
                        pass
                except Exception as loop_err:
                    print(f"[RunLoop] error: {loop_err}")
                finally:
                    await asyncio.sleep(0)
        finally:
            try:
                if 'listener_task' in locals() and not listener_task.done():
                    listener_task.cancel()
                    try:
                        await listener_task
                    except Exception:
                        pass
            except Exception:
                pass
            try:
                self.ws.close()
            except Exception:
                pass
            cv2.destroyAllWindows()

if __name__ == "__main__":
    ws = WSClient(WSS_URL)
    asyncio.run(TrackerApp(ws).run())
