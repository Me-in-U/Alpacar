import asyncio
import json
import math
import os
os.environ["OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS"] = "0"
import queue
import threading
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Callable, Awaitable, Type
import logging

import cv2
import numpy as np
import websocket
from ultralytics import YOLO
from ml.recommender import recommend_best_zone

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)

# =============================
# Configuration
# =============================

VIDEO_PATH = 0
# VIDEO_PATH = "WIN_20250817_00_00_55_Pro.mp4"
MODEL_PATH = "track-obb.pt"
TRACKER_CFG_NAME = "bytetrack.yaml"
WSS_URL = "wss://i13e102.p.ssafy.io/ws/jetson/"


OUTPUT_WIDTH = 900
OUTPUT_HEIGHT = 550

# Recommender grid resolution (for feature inputs)
GRID_W = 56
GRID_H = 24

IMG_SIZE = 1280
IMG_HEIGHT = 720
IMG_WIDTH = 1280
CONF_THRES = 0.4
IOU_THRES = 0.6

ENTER_THRESHOLD_SECONDS = 3.0
EXIT_THRESHOLD_SECONDS = 2.0

LOST_THRESHOLD_SECONDS = float(os.getenv("LOST_THRESHOLD_SECONDS", "2.0"))

SNAPSHOT_INTERVAL_S = 0.5
SNAPSHOT_PATH = str(Path(__file__).with_name("status_snapshot.json"))

PARKING_ZONES_NORM: List[Dict[str, Any]] = [
    {
        "id": "B1", 
        "rect": [0.378086, 0.004115, 0.45679, 0.245542],
        "left_zone": "",
        "right_zone": "B2",
        "left_pillar": True,
        "right_pillar": False,
        "small_only": False,
    },
    {
        "id": "B2", 
        "rect": [0.454475, 0.005487, 0.530864, 0.245542],
        "left_zone": "B1",
        "right_zone": "B3",
        "left_pillar": False,
        "right_pillar": False,
        "small_only": False,
    },
    {
        "id": "B3", 
        "rect": [0.530864, 0.005487, 0.608796, 0.246914],
        "left_zone": "B2",
        "right_zone": "",
        "left_pillar": False,
        "right_pillar": True,
        "small_only": False,
    },
    {
        "id": "C1", 
        "rect": [0.636574, 0.002743, 0.715278, 0.215364],
        "left_zone": "",
        "right_zone": "C2",
        "left_pillar": True,
        "right_pillar": False,
        "small_only": True,
    },
    {
        "id": "C2", 
        "rect": [0.709877, 0.005487, 0.79321, 0.215364],
        "left_zone": "C1",
        "right_zone": "C3",
        "left_pillar": False,
        "right_pillar": False,
        "small_only": True,
    },
    {
        "id": "C3", 
        "rect": [0.782407, 0.00823, 0.861883, 0.21262],
        "left_zone": "C2",
        "right_zone": "",
        "left_pillar": False,
        "right_pillar": True,
        "small_only": True,
    },
    {
        "id": "A1", 
        "rect": [0.371914, 0.72428, 0.453704, 0.99177],
        "left_zone": "A2",
        "right_zone": "",
        "left_pillar": False,
        "right_pillar": True,
        "small_only": False,
    },
    {
        "id": "A2", 
        "rect": [0.451389, 0.725652, 0.534722, 1.0],
        "left_zone": "A3",
        "right_zone": "A1",
        "left_pillar": False,
        "right_pillar": False,
        "small_only": False,
    },
    {
        "id": "A3", 
        "rect": [0.533179, 0.725652, 0.615741, 0.997257],
        "left_zone": "",
        "right_zone": "A2",
        "left_pillar": True,
        "right_pillar": False,
        "small_only": False,
    },
    {
        "id": "A4", 
        "rect": [0.645062, 0.720165, 0.733796, 0.994513],
        "left_zone": "A5",
        "right_zone": "",
        "left_pillar": False,
        "right_pillar": True,
        "small_only": False,
    },
    {
        "id": "A5", 
        "rect": [0.725309, 0.720165, 0.813272, 0.989026],
        "left_zone": "",
        "right_zone": "A4",
        "left_pillar": True,
        "right_pillar": False,
        "small_only": False,
    },
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


class VehicleSpecsHelper:
    
    SIZE_CLASS_SPECS = {
        "compact": {"width": 2.0, "length": 4.2, "size_code": 1},
        "midsize": {"width": 2.5, "length": 5.0, "size_code": 2},
        "suv": {"width": 2.8, "length": 5.2, "size_code": 3}
    }
    
    SIZE_CLASS_BOXES = {
        "compact": (200, 80),
        "midsize": (250, 100),
        "suv": (300, 120)
    }
    
    @classmethod
    def get_specs_from_size_class(cls, size_class: Optional[str]) -> Dict[str, Any]:
        default_specs = {"width": 2.5, "length": 5.0, "size_code": 2}
        if not size_class or not isinstance(size_class, str):
            return default_specs

        normalized_size_class = size_class.strip()
        return cls.SIZE_CLASS_SPECS.get(normalized_size_class, default_specs)
    
    @classmethod
    def get_box_size_from_size_class(cls, size_class: Optional[str]) -> Tuple[int, int]:
        if not size_class:
            return (250, 100)
        
        return cls.SIZE_CLASS_BOXES.get(size_class, (250, 100))
    
    @classmethod
    def parse_size_class_string(cls, size_class: str) -> Tuple[int, int]:
        try:
            if "," in size_class:
                width, length = map(float, size_class.split(","))
                return (int(width * 100), int(length * 100))
        except Exception:
            pass
        return cls.get_box_size_from_size_class(size_class)


class ZoneInfoHelper:
    @staticmethod
    def find_zone_by_id(zones_norm: List[Dict[str, Any]], zone_id: str) -> Optional[Dict[str, Any]]:
        for zone in zones_norm:
            if zone["id"] == zone_id:
                return zone
        return None
    
    @staticmethod
    def get_adjacent_zone_info(zones_norm: List[Dict[str, Any]], zone_info: Dict[str, Any], slot_map: Dict[str, str], 
                              occupant_to_zone: Dict[int, str], last_angle_by_id: Dict[int, float],
                              last_center_by_id: dict[int, tuple[float, float]], plate_mgr) -> dict[str, any]:
        result = {
            "left_occupied": 0, "left_angle": 0.0, "left_offset": 0.0, "left_size": 0,
            "left_width": 0, "left_length": 0, "left_has_pillar": 0,
            "right_occupied": 0, "right_angle": 0.0, "right_offset": 0.0, "right_size": 0,
            "right_width": 0, "right_length": 0, "right_has_pillar": 0
        }
        
        left_zone_id = zone_info.get("left_zone", "")
        if left_zone_id:
            result["left_occupied"] = 1 if slot_map.get(left_zone_id) != "free" else 0
            result["left_has_pillar"] = 1 if zone_info.get("left_pillar", False) else 0
            
            if result["left_occupied"]:
                ZoneInfoHelper._fill_adjacent_vehicle_info(
                    zones_norm, left_zone_id, occupant_to_zone, last_angle_by_id, last_center_by_id, plate_mgr, result, "left"
                )
        
        right_zone_id = zone_info.get("right_zone", "")
        if right_zone_id:
            result["right_occupied"] = 1 if slot_map.get(right_zone_id) != "free" else 0
            result["right_has_pillar"] = 1 if zone_info.get("right_pillar", False) else 0
            
            if result["right_occupied"]:
                ZoneInfoHelper._fill_adjacent_vehicle_info(
                    zones_norm, right_zone_id, occupant_to_zone, last_angle_by_id, last_center_by_id, plate_mgr, result, "right"
                )
        
        # logger.info(f"[ZoneInfoHelper] result: {result}")
        return result
    
    @staticmethod
    def _fill_adjacent_vehicle_info(zones_norm: List[Dict[str, Any]], zone_upper: str, occupant_to_zone: Dict[int, str], 
                                   last_angle_by_id: Dict[int, float], last_center_by_id: Dict[int, Tuple[float, float]], 
                                   plate_mgr, result: Dict[str, Any], side: str):
        found_vehicle = False
        for tid, occupied_zone in occupant_to_zone.items():
            if occupied_zone == zone_upper:
                found_vehicle = True
                angle_rad = last_angle_by_id.get(tid, 0.0)
                result[f"{side}_angle"] = angle_rad
                
                # vehicle_center = last_center_by_id.get(tid)
                # if vehicle_center:
                #     zone_info = ZoneInfoHelper.find_zone_by_id(zones_norm, zone_upper)
                #     if zone_info and "rect" in zone_info:
                #         zone_rect = zone_info["rect"]
                #         # 주차 구역 중심 계산 (정규화된 좌표)
                #         zone_cx = (zone_rect[0] + zone_rect[2]) / 2
                #         zone_cy = (zone_rect[1] + zone_rect[3]) / 2
                #         # 차량 중심 (정규화된 좌표)
                #         vehicle_cx, vehicle_cy = vehicle_center
                #         # 유클리드 거리 계산
                #         offset = math.sqrt((vehicle_cx - zone_cx)**2 + (vehicle_cy - zone_cy)**2)
                #         result[f"{side}_offset"] = offset
                #         # logger.debug(f"[Feature] {side} offset calculated: {offset:.4f}")
                #     else:
                #         result[f"{side}_offset"] = 0.0
                # else:
                #     result[f"{side}_offset"] = 0.0
                
                size_class = None
                if tid is not None:
                    license_plate = plate_mgr.get(tid)
                    if license_plate:
                        size_class = plate_mgr.get_size_class(license_plate)
                if not size_class:
                    size_class = "midsize"
                specs = VehicleSpecsHelper.get_specs_from_size_class(size_class)
                result[f"{side}_width"] = specs.get("width", 2.5)
                result[f"{side}_length"] = specs.get("length", 5.0)
                result[f"{side}_size"] = specs.get("size_code", 2)
                break
        
    @staticmethod
    def calculate_goal_position(zone_rect: List[float], frame_wh: Optional[Tuple[int, int]] = None) -> Tuple[float, float]:
        cx = (zone_rect[0] + zone_rect[2]) / 2
        cy = (zone_rect[1] + zone_rect[3]) / 2
        if frame_wh:
            fw, fh = frame_wh
            return cx * float(fw), cy * float(fh)
        return cx * float(GRID_W), cy * float(GRID_H)


class ExceptionHandler:
    @staticmethod
    def safe_execute(func: Callable, *args, default=None, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.debug(f"Safe execute failed for {func.__name__}: {e}")
            return default
    
    @staticmethod
    def safe_async_execute(func: Callable, *args, default=None, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.debug(f"Safe async execute failed for {func.__name__}: {e}")
            return default


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

    def assemble_slot_status(self, reserved: set[str]) -> Dict[str, str]:
        slot: Dict[str, str] = {}
        for z in self.zones_norm:
            zid = z["id"]
            st = self.state[zid]
            if zid in reserved:
                slot[zid] = "reserved"
            elif st.occupant_id is not None:
                slot[zid] = "occupied"
            else:
                slot[zid] = "free"
        return slot

    def occupant_to_zone(self) -> Dict[int, str]:
        mapping: Dict[int, str] = {}
        for zone in self.zones_norm:
            zid = zone["id"]
            st = self.state.get(zid)
            if st and st.occupant_id is not None:
                mapping[int(st.occupant_id)] = zid
        return mapping


# =============================
# Reservation Manager
# =============================


class ReservationManager:
    def __init__(self) -> None:
        self._reserved: set[str] = set()
        self._assigned_by_plate: Dict[str, str] = {}
        self._size_class_by_plate: Dict[str, str] = {}
        self._completed_zones: set[str] = set()

    # --- Getters (read-only copies) ---
    def get_reserved(self) -> set[str]:
        return set(self._reserved)

    def get_assigned_by_plate(self) -> Dict[str, str]:
        return dict(self._assigned_by_plate)

    def get_size_class_by_plate(self) -> Dict[str, str]:
        return dict(self._size_class_by_plate)

    def get_size_class(self, plate: str) -> str:
        return str(self._size_class_by_plate.get(plate, ""))

    def get_zone_to_assigned_plate_map(self) -> Dict[str, str]:
        return {zone: plate for plate, zone in self._assigned_by_plate.items()}

    def has_completed(self, zone_id: str) -> bool:
        return zone_id in self._completed_zones

    # --- Mutators ---
    def set_size_class(self, plate: str, size_class: str) -> None:
        if plate and size_class:
            self._size_class_by_plate[plate] = size_class

    def reserve(self, plate: str, zone: str, slot_map: Dict[str, str], send_snapshot: Callable[[], None]) -> bool:
        if not zone or slot_map.get(zone) != "free":
            return False
        self._reserved.add(zone)
        self._completed_zones.discard(zone)
        if plate:
            self._assigned_by_plate[plate] = zone
        logger.info(f"[Reservation] created: plate={plate} zone={zone}")
        try:
            send_snapshot()
        except Exception:
            pass
        return True

    def complete(self, plate: str, zone: str, send_snapshot: Callable[[], None]) -> None:
        self._reserved.discard(zone)
        if plate:
            self._assigned_by_plate.pop(plate, None)
            self._size_class_by_plate.pop(plate, None)
        self._completed_zones.add(zone)
        logger.info(f"[ParkingCompleted] plate={plate} zone={zone}")
        try:
            send_snapshot()
        except Exception:
            pass

    def preempt_zone(self, zone: str) -> Optional[str]:
        self._reserved.discard(zone)
        plate = None
        for p, z in list(self._assigned_by_plate.items()):
            if z == zone:
                plate = p
                self._assigned_by_plate.pop(p, None)
                break
        return plate

    def release_mispark(self, occupant_to_zone: Dict[int, str], plate_mgr: "PlateManager") -> None:
        try:
            vehicles_to_release: List[str] = []
            for plate, assigned_zone in list(self._assigned_by_plate.items()):
                tid = plate_mgr.get_track_id_by_plate(plate)
                if tid is None:
                    continue
                actual_zone = occupant_to_zone.get(int(tid))
                if actual_zone is None:
                    continue
                if actual_zone != assigned_zone:
                    self._reserved.discard(assigned_zone)
                    logger.info(
                        f"[Reservation] release by mispark: plate={plate} zone={assigned_zone} actual={actual_zone}"
                    )
                    vehicles_to_release.append(plate)
            for plate in vehicles_to_release:
                self._assigned_by_plate.pop(plate, None)
                self._size_class_by_plate.pop(plate, None)
        except Exception:
            pass

# WebSocket Wrapper
# =============================

class WSClient:
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
        logger.info(f"[WebSocket] Connected to {self.url}")

    def _on_message(self, ws, message: str) -> None: 
        try:
            self._queue.put_nowait(message)
        except Exception:
            pass

    def _on_error(self, ws, error) -> None: 
        logger.error(f"[WebSocket] error: {error}")

    def _on_close(self, ws, code, msg) -> None: 
        self._connected.clear()
        logger.warning(f"[WebSocket] closed code={code} msg={msg}")

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
                logger.exception(f"[WebSocket] run_forever error: {e}")
            if not self._stop_flag.is_set():
                logger.info("[WebSocket] Reconnecting in 1s...")
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
            logger.error(f"[WebSocket] send failed: {e}")


    def is_connected(self) -> bool:
        return self._connected.is_set()

    async def wait_connected(self, timeout: Optional[float] = None) -> bool:
        try:
            return await asyncio.to_thread(self._connected.wait, timeout)
        except Exception:
            return False



    async def recv(self) -> str:
        return await asyncio.to_thread(self._queue.get)

    def close(self) -> None:
        try:
            logger.info("[WebSocket] 연결 종료 시작")
            self._stop_flag.set()
            if self.wsapp is not None:
                try:
                    logger.info("[WebSocket] WebSocketApp 종료 중...")
                    self.wsapp.close()
                except Exception as e:
                    logger.error(f"[WebSocket] WebSocketApp 종료 중 오류: {e}")
            if self._thread and self._thread.is_alive():
                logger.info("[WebSocket] 백그라운드 스레드 종료 대기 중...")
                try:
                    self._thread.join(timeout=3.0)  # 3초 타임아웃
                    if self._thread.is_alive():
                        logger.warning("[WebSocket] 백그라운드 스레드 종료 타임아웃")
                except Exception as e:
                    logger.error(f"[WebSocket] 스레드 종료 중 오류: {e}")
            logger.info("[WebSocket] 연결 종료 완료")
        except Exception as e:
            logger.error(f"[WebSocket] 종료 중 예상치 못한 오류: {e}")

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
        reserved: Optional[set[str]] = None,
    ) -> None:
        try:
            font = cv2.FONT_HERSHEY_SIMPLEX
            zone_ids = [z["id"] for z in self.prk.zones_norm]
            slot_map = self.prk.assemble_slot_status(reserved or set())
            reserved_list: List[str] = []
            occupied: List[Tuple[str, int]] = []
            free: List[str] = []
            for zid in zone_ids:
                status = slot_map.get(zid, "free")
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
                status = slot_map.get(zid, "free")
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


def extract_centers_by_id(result: Any) -> Dict[int, Tuple[float, float]]:
    """현재 프레임의 트랙 ID별 차량 중심점을 추출한다."""
    id_to_center: Dict[int, Tuple[float, float]] = {}
    try:
        if not hasattr(result, "obb") or result.obb is None:
            return id_to_center
        ids_t = getattr(result.obb, "id", None)
        xyxyxyxy = getattr(result.obb, "xyxyxyxy", None)
        if ids_t is None or xyxyxyxy is None:
            return id_to_center
        ids = ids_t.cpu().numpy().tolist() if hasattr(ids_t, "cpu") else list(ids_t)
        for i, tid in enumerate(ids):
            try:
                pts = xyxyxyxy[i].cpu().numpy().reshape(-1, 2)
                cx = float(np.mean(pts[:, 0]))
                cy = float(np.mean(pts[:, 1]))
                id_to_center[int(tid)] = (cx, cy)
            except Exception:
                continue
    except Exception:
        return id_to_center
    return id_to_center


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
    reserved: set[str],
    assigned_by_plate: Dict[str, str],
) -> Dict[str, Any]:
    slot_map = parking.assemble_slot_status(reserved)

    occupant_to_zone: Dict[int, str] = {}
    for zone in parking.zones_norm:
        zid = zone["id"]
        state = parking.state[zid]
        if state.occupant_id is not None:
            occupant_to_zone[int(state.occupant_id)] = zid

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

        is_parked = tid in occupant_to_zone
        state_str = "parked" if is_parked else "running"
        # 제안 구역: plate 기반 예약/배정 정보가 있으면 그 값을, 없으면 현재 점유 구역(있다면)을 제공
        suggested_zone = assigned_by_plate.get(plate, occupant_to_zone.get(tid, ""))
        
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
# Ideal Parking Template Generator
# =============================

class IdealParkingTemplate:
    """이상적인 주차 템플릿 생성기"""
    
    def __init__(self):
        self.default_angle = 90.0  # 기본 주차 각도 (수직)
        self.default_margin = 0.1  # 기본 여백 (10%)
    
    def generate_template(self, zone_rect: List[float], frame_width: int, frame_height: int, 
                         vehicle_specs: Optional[Dict] = None) -> Dict:
        """
        주차 구역에 대한 이상적인 템플릿 생성
        
        Args:
            zone_rect: 주차 구역 좌표 [x1, y1, x2, y2] (정규화됨)
            frame_width: 프레임 너비
            frame_height: 프레임 높이
            vehicle_specs: 차량 사양 정보 (선택사항)
            
        Returns:
            dict: 이상적인 템플릿 정보
        """
        # 정규화된 좌표를 픽셀 좌표로 변환
        x1n, y1n, x2n, y2n = zone_rect
        x1 = int(x1n * frame_width)
        y1 = int(y1n * frame_height)
        x2 = int(x2n * frame_width)
        y2 = int(y2n * frame_height)
        
        # 여백 적용
        margin_x = int((x2 - x1) * self.default_margin)
        margin_y = int((y2 - y1) * self.default_margin)
        
        ideal_x1 = x1 + margin_x
        ideal_y1 = y1 + margin_y
        ideal_x2 = x2 - margin_x
        ideal_y2 = y2 - margin_y
        
        # 이상적인 주차 구역 폴리곤 생성
        zone_poly = np.array([
            [ideal_x1, ideal_y1],
            [ideal_x2, ideal_y1],
            [ideal_x2, ideal_y2],
            [ideal_x1, ideal_y2]
        ])
        
        # 차량 크기에 따른 이상적인 박스 크기 계산
        if vehicle_specs:
            ideal_width = vehicle_specs.get('width', 2.5) * 100  # 미터를 픽셀로 변환
            ideal_length = vehicle_specs.get('length', 5.0) * 100
        else:
            ideal_width = 250  # 기본값 (픽셀)
            ideal_length = 500
        
        # 이상적인 중심점 계산
        center_x = (ideal_x1 + ideal_x2) / 2
        center_y = (ideal_y1 + ideal_y2) / 2
        
        return {
            'angle': self.default_angle,
            'center': (center_x, center_y),
            'zone_poly': zone_poly,
            'ideal_width': ideal_width,
            'ideal_length': ideal_length,
            'zone_rect': [ideal_x1, ideal_y1, ideal_x2, ideal_y2],
            'margin': self.default_margin
        }


# =============================
# Template Matching Scorer
# =============================

class TemplateMatchingScorer:
    """템플릿 매칭 기반 점수 계산기"""
    
    def __init__(self):
        self.template_generator = IdealParkingTemplate()
    
    def calculate_template_matching_score(self, actual_vehicle_box, ideal_template, actual_angle, vehicle_specs):
        """
        실제 차량과 이상적 템플릿 비교하여 각도 점수 계산
        
        Args:
            actual_vehicle_box: 실제 검출된 차량 박스 (4개 점)
            ideal_template: 이상적인 템플릿 정보
            actual_angle: 실제 차량 각도
            vehicle_specs: 차량 사양 정보 (사용 안함, 호환성 유지)
            
        Returns:
            dict: 점수 정보
        """
        # 각도 편차 계산
        ideal_angle = ideal_template['angle']
        corrected_angle = self.apply_yolo_angle_correction(actual_angle)
        
        angle_diffs = [
            abs(corrected_angle - ideal_angle),
            abs(corrected_angle - ideal_angle + 180),
            abs(corrected_angle - ideal_angle - 180),
            abs(corrected_angle - (ideal_angle + 90)),
            abs(corrected_angle - (ideal_angle - 90))
        ]
        
        angle_diff = min(angle_diffs)
        if angle_diff > 90:
            angle_diff = 180 - angle_diff
        
        # 각도 점수 (3단계 기준 + 차선 침범 감점)
        angle_score = self._calculate_tiered_angle_score(angle_diff, actual_vehicle_box, ideal_template)
        
        # 최종 점수 (각도만 사용)
        total_score = angle_score
        
        return {
            'total_score': round(total_score, 1),
            'angle_score': round(angle_score, 1),
            'details': {
                'angle_diff': round(angle_diff, 1),
                'ideal_angle': ideal_angle,
                'actual_angle': round(actual_angle, 1),
                'corrected_angle': round(corrected_angle, 1),
                'skill_level': self._get_skill_level(angle_diff),
                'lane_violation': self._check_lane_violation(actual_vehicle_box, ideal_template)
            }
        }
    
    def _calculate_tiered_angle_score(self, angle_diff, actual_vehicle_box, ideal_template):
        """
        3단계 각도 평가 시스템
        - 5도 이하: 고득점 (상급자) 80-100점
        - 6-10도: 중급자 40-79점  
        - 11도 이상: 초급자 0-39점
        + 6도 이상 + 차선 침범 시 추가 큰 감점
        """
        base_score = 0
        
        # 1. 기본 3단계 점수
        if angle_diff <= 5:
            # 고득점 구간 (상급자): 80-100점
            base_score = 100 - (angle_diff * 4)  # 0도=100점, 5도=80점
            
        elif angle_diff <= 10:
            # 중급자 구간: 40-79점
            base_score = 80 - ((angle_diff - 5) * 8)  # 6도=72점, 10도=40점
            
        else:
            # 초급자 구간: 0-39점
            base_score = max(0, 40 - ((angle_diff - 10) * 2))  # 11도=38점, 30도=0점
        
        # 2. 차선 침범 추가 감점 (6도 이상일 때만)
        if angle_diff >= 6:
            lane_violation = self._check_lane_violation(actual_vehicle_box, ideal_template)
            if lane_violation:
                # 큰 감점: 기본 점수의 30-50% 추가 감점
                penalty = base_score * 0.4  # 40% 감점
                base_score = max(0, base_score - penalty)
                logger.warning(f"🚨 차선 침범 감점! 각도: {angle_diff:.1f}도, 감점: -{penalty:.1f}점")
        
        return base_score
    
    def _get_skill_level(self, angle_diff):
        """각도에 따른 숙련도 레벨 반환"""
        if angle_diff <= 5:
            return "Expert"
        elif angle_diff <= 10:
            return "Intermediate"
        else:
            return "Beginner"
    
    def _check_lane_violation(self, actual_vehicle_box, ideal_template):
        """
        차선 침범 검사
        실제 차량이 주차 구역을 얼마나 벗어났는지 확인
        """
        try:
            # 차량 박스와 주차 구역의 교집합 계산
            vehicle_poly = actual_vehicle_box.reshape(-1, 1, 2).astype(np.int32)
            zone_poly = ideal_template['zone_poly'].reshape(-1, 1, 2).astype(np.int32)
            
            # 교집합 면적 계산
            intersection = cv2.intersectConvexConvex(vehicle_poly, zone_poly)[1]
            if intersection is None:
                return True  # 교집합이 없으면 완전히 벗어남
            
            intersection_area = cv2.contourArea(intersection)
            vehicle_area = cv2.contourArea(vehicle_poly)
            
            if vehicle_area == 0:
                return False
            
            # 차량이 구역 내에 있는 비율
            overlap_ratio = intersection_area / vehicle_area
            
            # 70% 미만이 구역 내에 있으면 차선 침범으로 판정
            return overlap_ratio < 0.7
            
        except Exception as e:
            logger.error(f"⚠️ 차선 침범 검사 오류: {e}")
            return False
    
    def apply_yolo_angle_correction(self, angle):
        """YOLO 각도 인식 오류 보정"""
        # 87-93도 범위: 완벽한 보정 (90도로 인식됨)
        if 87 <= angle <= 93:
            return 90.0
        
        # 73-77도 범위: 부분 보정 (실제로는 더 작은 각도)
        elif 73 <= angle <= 77:
            return angle - 60
        
        # -3도에서 +3도 범위: 0도로 보정
        elif -3 <= angle <= 3 or 177 <= angle <= 183:
            return 0.0
        
        # 그 외: 원본 그대로
        else:
            return angle


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
        self.template_scorer = TemplateMatchingScorer()  # 새로운 스코어러 추가
        self.vis = Visualizer(self.plate_mgr, self.parking)
        self._last_snapshot_ts = 0.0
        self.resv = ReservationManager()
        self._last_slot_map: Dict[str, str] = {}
        self._last_seen_by_id: Dict[int, float] = {}
        self._reported_lost: set[int] = set()
        self._last_angle_by_id: Dict[int, float] = {}
        self._last_center_by_id: Dict[int, Tuple[float, float]] = {}
        self._last_zone_to_tid: Dict[str, int] = {}
        self._last_poly_by_id: Dict[int, np.ndarray] = {}
        self._last_frame_wh: Tuple[int, int] = (0, 0)

        self._event_queue: "asyncio.Queue[Dict[str, Any]]" = asyncio.Queue()
        self._event_handlers: Dict[str, List[Callable[[Dict[str, Any]], Awaitable[None]]]] = {}
        self._event_loop_task: Optional[asyncio.Task] = None

    # ============ In-file EventBus ============
    def _on(self, message_type: str, handler: Callable[[Dict[str, Any]], Awaitable[None]]) -> None:
        self._event_handlers.setdefault(message_type, []).append(handler)

    async def _emit(self, payload: Dict[str, Any]) -> None:
        # payload MUST contain 'message_type'
        await self._event_queue.put(payload)

    async def _event_loop(self) -> None:
        logger.info("[EventBus] 이벤트 루프 시작")
        try:
            while True:
                try:
                    payload = await self._event_queue.get()
                    msg_type = str(payload.get("message_type", ""))
                    for handler in self._event_handlers.get(msg_type, []):
                        try:
                            await handler(payload)
                        except Exception as e:
                            logger.exception(f"[EventBus] handler error for {msg_type}: {e}")
                except asyncio.CancelledError:
                    logger.info("[EventBus] 이벤트 루프 취소됨")
                    break
                except Exception as e:
                    logger.error(f"[EventBus] 이벤트 루프 오류: {e}")
                    await asyncio.sleep(0.1)  # 잠시 대기 후 계속
        except Exception as e:
            logger.error(f"[EventBus] 이벤트 루프 예상치 못한 오류: {e}")
        finally:
            logger.info("[EventBus] 이벤트 루프 종료")

    async def _send_ws(self, payload: Dict[str, Any]) -> None:
        await asyncio.to_thread(self.ws.send_json, payload)

    # --- Score strategy injection ---
    def _default_score(self, occupant_tid: int, zone_id_upper: str) -> float:
        """기본 스코어링 방법 (기존 로직 유지)"""
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

        st = self.parking.state.get(zone_id_upper)
        time_adj = 0.0
        if st and st.parked_since is not None:
            now_ts = time.time()
            actual_sec = float(max(0.0, now_ts - st.parked_since))
            expected_sec = float(os.getenv("EXPECTED_PARKING_TIME_S", "10"))
            delta = actual_sec - expected_sec
            time_adj = float(clamp(-0.5 * delta, -10.0, 10.0))

        score = clamp(base + time_adj, 0.0, 100.0)
        return float(round(score, 1))

    def _template_matching_score(self, occupant_tid: int, zone_id_upper: str) -> float:
        """템플릿 매칭 기반 스코어링 (새로운 방법)"""
        try:
            # 차량 정보 가져오기
            angle_rad = float(self._last_angle_by_id.get(occupant_tid, 0.0))
            angle_deg = math.degrees(angle_rad)
            
            # 차량 박스 정보 가져오기 (실제 구현에서는 추적 정보에서 가져와야 함)
            vehicle_box = self._get_vehicle_box(occupant_tid)
            if vehicle_box is None:
                return self._default_score(occupant_tid, zone_id_upper)
            
            # 주차 구역 정보 찾기
            zone_info = ZoneInfoHelper.find_zone_by_id(PARKING_ZONES_NORM, zone_id_upper)
            
            if zone_info is None:
                return self._default_score(occupant_tid, zone_id_upper)
            
            # 이상적인 템플릿 생성
            fw, fh = self._last_frame_wh
            fw = fw or OUTPUT_WIDTH
            fh = fh or OUTPUT_HEIGHT
            ideal_template = self.template_scorer.template_generator.generate_template(
                zone_info["rect"],
                fw,
                fh,
            )
            
            # 차량 사양 정보 (선택사항)
            vehicle_specs = ExceptionHandler.safe_execute(
                lambda: VehicleSpecsHelper.get_specs_from_size_class(
                    self.plate_mgr.get_size_class(self.plate_mgr.get(occupant_tid) or "")
                ),
                default=None
            )
            
            # 템플릿 매칭 점수 계산
            score_result = self.template_scorer.calculate_template_matching_score(
                vehicle_box, ideal_template, angle_deg, vehicle_specs
            )
            
            # 시간 보정 적용 (기존 로직과 동일)
            st = self.parking.state.get(zone_id_upper)
            time_adj = 0.0
            if st and st.parked_since is not None:
                now_ts = time.time()
                actual_sec = float(max(0.0, now_ts - st.parked_since))
                expected_sec = float(os.getenv("EXPECTED_PARKING_TIME_S", "10"))
                delta = actual_sec - expected_sec
                time_adj = float(clamp(-0.5 * delta, -10.0, 10.0))
            
            final_score = clamp(score_result['total_score'] + time_adj, 0.0, 100.0)
            
            # 디버그 정보 출력
            logger.info("템플릿 매칭 점수: %.1f (angle=%.1f diff=%.1f, lane=%s)",
                        final_score, score_result['details']['actual_angle'],
                        score_result['details']['angle_diff'],
                        score_result['details']['lane_violation'])
            
            return float(round(final_score, 1))
            
        except Exception as e:
            logger.error(f"⚠️ 템플릿 매칭 점수 계산 오류: {e}")
            return self._default_score(occupant_tid, zone_id_upper)

    def _get_vehicle_box(self, track_id: int) -> Optional[np.ndarray]:
        """트랙 ID에 해당하는 차량 박스 정보 반환 (최근 프레임 기준)"""
        poly = self._last_poly_by_id.get(int(track_id))
        if poly is None:
            return None
        # cv2.intersectConvexConvex는 (N,1,2) int32 형태를 선호
        try:
            if isinstance(poly, np.ndarray):
                if poly.ndim == 2 and poly.shape[1] == 2:
                    return poly.reshape((-1, 1, 2)).astype(np.int32)
                elif poly.ndim == 3 and poly.shape[2] == 2:
                    return poly.astype(np.int32)
        except Exception:
            return None
        return None

    def _get_vehicle_specs_from_size_class(self, size_class: str) -> Dict:
        return VehicleSpecsHelper.get_specs_from_size_class(size_class)

    def set_score_strategy(self, fn: Callable[[int, str], float]) -> None:
        self._score_strategy = fn

    def _calculate_parking_score(self, occupant_tid: int, zone_id_upper: str) -> float:
        fn = getattr(self, "_score_strategy", None) or self._template_matching_score
        return float(fn(occupant_tid, zone_id_upper))

    def _build_features_for_free_zones(self, size_class: Optional[str], free_zones: List[str]) -> List[Dict]:
        # 차량 사양 정보 가져오기
        specs = VehicleSpecsHelper.get_specs_from_size_class(size_class)
        width_m = specs.get("width", 2.0)
        length_m = specs.get("length", 4.5)

        # 현재 주차 상태 가져오기
        slot_map = self._get_slot_map()
        occupant_to_zone = self.parking.occupant_to_zone()
        
        # 디버깅: 현재 주차 상태 로깅
        logger.debug(f"[Feature] Current occupant_to_zone: {occupant_to_zone}")
        logger.debug(f"[Feature] Current last_angle_by_id keys: {list(self._last_angle_by_id.keys())}")

        features: List[Dict] = []
        for zid in free_zones:
            zone_info = ZoneInfoHelper.find_zone_by_id(self.parking.zones_norm, zid)
                

            # 만약 구역이 차종과 매칭되지 않으면 continue
            # small_only가 True면 compact만 허용, False면 compact 외만 허용
            small_only = zone_info.get("small_only", False)
            if (small_only and size_class != "compact") or (not small_only and size_class == "compact"):
                continue

            feature = {
                "left_occupied": 0, "left_angle": 0.0, "left_offset": 0.0, "left_size": 0,
                "left_width": 0, "left_length": 0, "left_has_pillar": 0,
                "right_occupied": 0, "right_angle": 0.0, "right_offset": 0.0, "right_size": 0,
                "right_width": 0, "right_length": 0, "right_has_pillar": 0,
                "controlled_width": width_m, "controlled_length": length_m,
                "zone_id": str(zid),
                "agent_angle_tier": "intermediate",
                "left_angle_deg": 0.0,
                "right_angle_deg": 0.0,
            }
            logger.debug(f"[Feature] Zone {zid}: no zone info, using defaults")

            adjacent_info = ZoneInfoHelper.get_adjacent_zone_info(
                self.parking.zones_norm, zone_info, slot_map, occupant_to_zone, self._last_angle_by_id, self._last_center_by_id, self.plate_mgr
            )
            
            feature = {
                **adjacent_info,
                "controlled_width": width_m,
                "controlled_length": length_m,
                "zone_id": str(zid),
                "agent_angle_tier": "intermediate",
                # 각도는 '슬롯 정렬(수직) 기준 편차'를 도 단위로 제공: abs(rad->deg - 90) 그리고 [0, 90]로 클램프
                "left_angle_deg": max(0.0, min(90.0, abs(adjacent_info.get("left_angle", 0.0) * 180 / np.pi - 90.0))),
                "right_angle_deg": max(0.0, min(90.0, abs(adjacent_info.get("right_angle", 0.0) * 180 / np.pi - 90.0))),
            }
            
            # 각도 및 offset 정보 디버깅
            # left_angle = feature.get("left_angle", 0.0)
            # right_angle = feature.get("right_angle", 0.0)
            # left_offset = feature.get("left_offset", 0.0)
            # right_offset = feature.get("right_offset", 0.0)
            # logger.debug(f"[Feature] Zone {zid}: left_angle={left_angle:.4f}rad, right_angle={right_angle:.4f}rad, left_offset={left_offset:.4f}, right_offset={right_offset:.4f}")
            
            # logger.info(f"feature: {feature}")
            features.append(feature)

        return features

    def get_box_size(self, size_class: Optional[str]) -> Tuple[int, int]:
        """size_class에 따라 박스 크기를 반환한다."""
        return VehicleSpecsHelper.get_box_size_from_size_class(size_class)

    def extract_boxes_size(self, track_ids: List[int]) -> List[Tuple[int, int]]:
        """track ID 목록에 대해 각각의 박스 크기를 계산하여 반환한다."""
        return [
            VehicleSpecsHelper.get_box_size_from_size_class(
                self.plate_mgr.plate_to_size_class.get(self.plate_mgr.get(track_id) or "")
            )
            for track_id in track_ids
        ]

    async def _listen_dummy_assignment_request(self) -> None:
        try:
            # WebSocket 연결 완료 대기 (_on_open 이후 실행 보장)
            connected = await self.ws.wait_connected(5.0)
            if not connected:
                logger.error("[DummyAssignment] WS 연결 대기 타임아웃")
                return
            # 서버로 hello 요청을 보냄
            await asyncio.to_thread(self.ws.send_json, {"message_type": "hello"})
            # 응답을 기다림
            msg = await self.ws.recv()
            try:
                data = json.loads(msg)
            except Exception as e:
                logger.debug(f"[DummyAssignment] JSON 파싱 오류: {e}")
                return

            # 여러 대의 차량 정보를 받을 수 있도록 처리
            vehicles = data.get("vehicles")
            if vehicles and isinstance(vehicles, list):
                for vehicle in vehicles:
                    license_plate = str(vehicle.get("license_plate") or "")
                    if license_plate:
                        self.plate_mgr.enqueue_plate(license_plate)
                    size_class = str(vehicle.get("size_class") or "")
                    if license_plate and size_class:
                        self.plate_mgr.plate_to_size_class[license_plate] = size_class
                        self.resv.set_size_class(license_plate, size_class)
            else:
                # 기존 단일 차량 처리 (호환성)
                license_plate = str(data.get("license_plate") or "")
                if license_plate:
                    self.plate_mgr.enqueue_plate(license_plate)
                size_class = str(data.get("size_class") or "")
                if license_plate and size_class:
                    self.plate_mgr.plate_to_size_class[license_plate] = size_class
                    self.resv.set_size_class(license_plate, size_class)

            logger.info("[DummyAssignment] 초기 할당 요청 처리 완료")
        except Exception as e:
            logger.error(f"[DummyAssignment] 예외 발생: {e}")
            
    async def _listen_assignment_request(self) -> None:
        logger.info("[Assignment] 할당 요청 리스너 시작")
        try:
            while True:
                try:
                    msg = await self.ws.recv()
                    try:
                        data = json.loads(msg)
                    except Exception as e:
                        logger.debug(f"[Assignment] JSON 파싱 오류: {e}")
                        continue
                    if not isinstance(data, dict):
                        continue
                    if data.get("message_type") == "request_assignment":
                        logger.info(f"assignment request: {data}")
                        slot_map = self._get_slot_map()

                        license_plate = str(data.get("license_plate") or "")
                        if license_plate:
                            self.plate_mgr.enqueue_plate(license_plate)
                        size_class = str(data.get("size_class") or "")

                        if license_plate and size_class:
                            self.plate_mgr.plate_to_size_class[license_plate] = size_class
                            self.resv.set_size_class(license_plate, size_class)

                        # free인 구역들만 추출
                        free_zones = [z for z, state in slot_map.items() if state == "free"]
                        
                        # 사용자 실력 레벨 가져오기
                        user_skill_level = data.get("user_skill_level", "beginner")
                                     
                        suggested_zone = self._get_suggested_zone_from_recommender(size_class, free_zones, user_skill_level)
                        if suggested_zone:
                            logger.info(f"[Recommender] 추천 구역: {suggested_zone}")
                        else:
                            logger.info(f"[Recommender] 추천 구역 없음")

                        # 추천 구역이 free이면 사용, 아니면 fallback
                        assigned_zone = ""
                        if suggested_zone and suggested_zone in free_zones:
                            assigned_zone = suggested_zone
                            logger.info(f"[Assignment] 추천 구역 사용: {assigned_zone}")
                        elif free_zones:
                            assigned_zone = free_zones[0]
                            logger.info(f"[Assignment] fallback 구역 사용: {assigned_zone}")

                        await self._reserve_zone(license_plate, assigned_zone, slot_map)

                        await self._emit({
                            "message_type": "assignment",
                            "license_plate": license_plate,
                            "assignment": assigned_zone,
                            "user_skill_level": user_skill_level,
                        })
                except asyncio.CancelledError:
                    logger.info("[Assignment] 할당 요청 리스너 취소됨")
                    break
                except Exception as e:
                    logger.error(f"[Assignment] 메시지 처리 중 오류: {e}")
                    # 잠시 대기 후 계속
                    await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"[Assignment] 리스너 루프 오류: {e}")
        finally:
            logger.info("[Assignment] 할당 요청 리스너 종료")

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
            for zid, cur in sorted(slot_map_now.items()):
                prev = self._last_slot_map.get(zid)
                if prev is None and cur is not None:
                     logger.info(f"[Slot] {zid}: None -> {cur}")
                elif prev is not None and prev != cur:
                     logger.info(f"[Slot] {zid}: {prev} -> {cur}")
        except Exception:
            pass

    async def _send_snapshot(self, result_obj: Any | None, frame_w: int, frame_h: int) -> None:
        try:
            if result_obj is not None:
                payload = build_wss_payload_from_result(result_obj, frame_w, frame_h)
            else:
                payload = []
            await asyncio.to_thread(
                self.ws.send_json,
                build_logging_snapshot(
                    payload,
                    self.plate_mgr,
                    self.parking,
                    self.resv.get_reserved(),
                    self.resv.get_assigned_by_plate(),
                ),
            )
            slot_map_now = self.parking.assemble_slot_status(self.resv.get_reserved())
            self._log_slot_changes(slot_map_now)
            self._last_slot_map = slot_map_now.copy()
        except Exception:
            pass

    def _get_slot_map(self) -> Dict[str, str]:
        return self.parking.assemble_slot_status(self.resv.get_reserved())

    def _get_occupant_map(self) -> Dict[int, str]:
        return self.parking.occupant_to_zone()

    def _get_zone_to_tid_map(self) -> Dict[str, int]:
        mapping: Dict[str, int] = {}
        for zone in self.parking.zones_norm:
            zone_id = zone["id"]
            st = self.parking.state.get(zone_id)
            if st and st.occupant_id is not None:
                mapping[zone_id] = int(st.occupant_id)
        return mapping

    def _release_state_for_tid(self, tid: int, plate: str = "") -> None:
        tid = int(tid)

        try:
            zone = self._get_occupant_map().get(tid, "")
            if zone:
                st = self.parking.state.get(zone)
                if st and st.occupant_id == tid:
                    self.parking.state[zone] = ZoneState()
        except Exception:
            pass

        try:
            if plate:
                assigned = self.resv.get_assigned_by_plate().get(plate)
                if assigned:
                    self.resv.preempt_zone(assigned)
            else:
                if 'zone' in locals() and zone:
                    self.resv.preempt_zone(zone)
        except Exception:
            pass

        try:
            self._last_seen_by_id.pop(tid, None)
            self._reported_lost.discard(tid)
            self._last_angle_by_id.pop(tid, None)
            self._last_center_by_id.pop(tid, None)
            self._last_poly_by_id.pop(tid, None)
            self._last_zone_to_tid = {z: t for z, t in self._last_zone_to_tid.items() if t != tid}
            self.plate_mgr.track_to_plate.pop(tid, None)
        except Exception:
            pass

    async def _handle_exit_events(self) -> None:
        """구역이 비워진 경우에만 출차 이벤트를 전송한다."""
        try:
            cur_zone_to_tid = self._get_zone_to_tid_map()
            for zid, prev_tid in list(self._last_zone_to_tid.items()):
                cur_tid = cur_zone_to_tid.get(zid)
                if cur_tid is None:
                    plate = self.plate_mgr.get(prev_tid) or ""
                    if plate:
                        await self._emit({
                            "message_type": "exit",
                            "license_plate": plate,
                            "zone": zid,
                        })
                        self._release_state_for_tid(prev_tid, plate)
                        await self._send_snapshot(None, 0, 0)
            self._last_zone_to_tid = cur_zone_to_tid
        except Exception:
            pass

    async def _handle_lost_tracks(self, now_ts: float) -> None:
        try:
            lost_ids = [tid for tid, ts in list(self._last_seen_by_id.items()) if now_ts - ts >= LOST_THRESHOLD_SECONDS]
            if not lost_ids:
                return

            occupant_map = self._get_occupant_map()
            did_release = False
            for tid in lost_ids:
                if tid in self._reported_lost:
                    continue

                plate = self.plate_mgr.get(tid) or ""
                zone = occupant_map.get(int(tid), "")

                await self._emit({
                    "message_type": "exit",
                    "license_plate": plate,
                    "zone": zone,
                })

                self._release_state_for_tid(tid, plate)
                did_release = True

            if did_release:
                await self._send_snapshot(None, 0, 0)
        except Exception:
            logger.exception("[LostTracks] handler error")

    def _choose_zone_for_assignment(
        self, slot_map: Dict[str, str], size_class: Optional[str]
    ) -> str:
        free_zones = [z for z, state in slot_map.items() if state == "free"]
        
        if not free_zones:
            logger.warning("[Assignment] 사용 가능한 free 구역이 없습니다.")
            return ""
        
        suggested_zone = self._get_suggested_zone_from_recommender(size_class or "", free_zones)
        if suggested_zone and suggested_zone in free_zones:
            logger.info(f"[Assignment] 추천 모델 사용: {suggested_zone}")
            return suggested_zone
        
        fallback_zone = free_zones[0]
        logger.info(f"[Assignment] fallback 사용: {fallback_zone}")
        return fallback_zone
    
    def _get_suggested_zone_from_recommender(self, size_class: str, free_zones: List[str], user_skill_level: str = "beginner") -> str:
        """추천 모델에서 구역 제안 받기 (사용자 실력 레벨 고려)"""
        try:
            feats = self._build_features_for_free_zones(size_class, free_zones)
            logger.info(f"[Recommender] 사용자 실력 레벨: {user_skill_level}")
            for feat in feats:
                logger.debug(f"[Recommender] 입력 특성: {feat}")
            
            best = recommend_best_zone(feats, user_skill_level=user_skill_level)
            logger.info(f"[Recommender] 추천 결과: {best}")
            
            if best:
                if size_class == "compact":
                    small_only_zones = [item for item in best if item.get("small_only", False)]
                    if small_only_zones:
                        top = small_only_zones[0]
                        logger.info(f"[Recommender] compact 차량, small_only 우선 추천: {top}")
                        return str(top.get("zone_id") or "").strip()
                # 그 외에는 best[0] 사용
                top = best[0]
                logger.info(f"[Recommender] 추천 구역: {top}")
                return str(top.get("zone_id") or "").strip()
            
            logger.warning("[Recommender] 추천 결과가 없습니다.")
            return ""
            
        except Exception as e:
            logger.error(f"[Recommender] 예측 모델 오류: {e}")
            logger.info("[Recommender] fallback으로 첫 번째 free 구역 사용")
            return free_zones[0] if free_zones else ""

    async def _reserve_zone(self, license_plate: str, assigned_zone: str, slot_map: Dict[str, str]) -> None:
        if not assigned_zone:
            return
        self.resv.reserve(license_plate, assigned_zone, slot_map, lambda: asyncio.create_task(self._send_snapshot(None, 0, 0)))

    async def _handle_parking_completion(self) -> None:
        try:
            zone_to_assigned_plate: Dict[str, str] = self.resv.get_zone_to_assigned_plate_map()
            for zid in list(self.resv.get_reserved()):
                if self.resv.has_completed(zid):
                    continue
                st = self.parking.state.get(zid)
                if not st or st.occupant_id is None:
                    continue
                assigned_vehicle = zone_to_assigned_plate.get(zid)
                if not assigned_vehicle:
                    continue
                occupant_tid = int(st.occupant_id)
                occupant_vehicle = self.plate_mgr.get(occupant_tid) or ""
                if occupant_vehicle and occupant_vehicle == assigned_vehicle:
                    score = self._calculate_parking_score(occupant_tid, zid)

                    await self._emit({
                        "message_type": "score",
                        "license_plate": assigned_vehicle,
                        "score": round(score, 2),
                        "zone_id": zid,
                    })
                    self.resv.complete(assigned_vehicle, zid, lambda: asyncio.create_task(self._send_snapshot(None, 0, 0)))
                    logger.info(f"[ParkingCompletion] 예약 완료 처리: plate={assigned_vehicle}, zone={zid}")

        except Exception as e:
            logger.exception(f"[ParkingCompletion] 예외 발생: {e}")

    async def _handle_mispark_release(self, occupant_to_zone: Dict[int, str]) -> None:
        try:
            # mispark 감지 및 해제
            vehicles_to_release: List[str] = []
            for plate, assigned_zone in list(self.resv._assigned_by_plate.items()):
                tid = self.plate_mgr.get_track_id_by_plate(plate)
                if tid is None:
                    continue
                actual_zone = occupant_to_zone.get(int(tid))
                if actual_zone is None:
                    continue
                if actual_zone != assigned_zone:
                    # mispark 감지 - 점수 계산 및 전송
                    score = self._calculate_parking_score(int(tid), actual_zone)
                    await self._emit({
                        "message_type": "score",
                        "license_plate": plate,
                        "score": round(score, 2),
                        "zone_id": actual_zone,
                    })
                    logger.info(f"[Mispark] 점수 계산 완료: plate={plate}, zone={actual_zone}, score={round(score, 2)}")
                    vehicles_to_release.append(plate)
            
            # 기존 release_mispark 로직 실행
            self.resv.release_mispark(occupant_to_zone, self.plate_mgr)
        except Exception as e:
            logger.exception(f"[Mispark] 점수 계산 중 오류: {e}")

    async def _handle_preemption_and_reassign(self) -> None:
        try:
            zone_to_assigned_plate: Dict[str, str] = self.resv.get_zone_to_assigned_plate_map()
            for zid in list(self.resv.get_reserved()):
                st = self.parking.state.get(zid)
                if st is None or st.occupant_id is None:
                    continue
                assigned_plate = zone_to_assigned_plate.get(zid)
                occupant_tid = int(st.occupant_id)
                occupant_plate = self.plate_mgr.get(occupant_tid)
                if assigned_plate is not None and occupant_plate != assigned_plate:
                    size_class = self.resv.get_size_class(assigned_plate or "") if assigned_plate else ""

                    removed_plate = self.resv.preempt_zone(zid)
                    logger.info(
                        f"[Preempted] zone={zid} by={occupant_plate or occupant_tid} (assigned={removed_plate or ''})"
                    )
                    if assigned_plate:
                        score = self._calculate_parking_score(occupant_tid, zid)
                        await self._emit({
                            "message_type": "score",
                            "license_plate": occupant_plate,
                            "score": round(score, 2),
                            "zone_id": zid,
                        })
                        logger.info(f"[선점] zone={zid}가 {occupant_plate or occupant_tid}에 의해 선점됨 (기존 배정={removed_plate or ''})")
                        
                        slot_map_now = self._get_slot_map()
                        new_zone = self._choose_zone_for_assignment(slot_map_now, size_class)
                        if new_zone and slot_map_now.get(new_zone) == "free":
                            self.resv.reserve(assigned_plate, new_zone, slot_map_now, lambda: asyncio.create_task(self._send_snapshot(None, 0, 0)))
                            await self._emit({
                                "message_type": "re-assignment",
                                "license_plate": assigned_plate,
                                "assignment": new_zone,
                            })
                            logger.info(f"[Reservation] re-assigned: plate={assigned_plate} -> {new_zone}")
        except Exception:
            pass

    async def run(self) -> None:
        if self._event_loop_task is None:
            self._event_loop_task = asyncio.create_task(self._event_loop())
            self._on("exit", self._send_ws)
            self._on("score", self._send_ws)
            self._on("assignment", self._send_ws)
            self._on("re-assignment", self._send_ws)

        logger.info("[Main] 프로그램 시작 시 초기 할당 요청 실행")
        try:
            await self._listen_dummy_assignment_request()
        except Exception as e:
            logger.error(f"[Main] 초기 할당 요청 실행 중 오류: {e}")

        self.model = YOLO(MODEL_PATH)
        
        cap = cv2.VideoCapture(VIDEO_PATH)
        if not cap.isOpened():
            logger.error(f"[VideoCapture] 비디오 소스를 열 수 없습니다: {VIDEO_PATH}")
            return
        
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, IMG_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, IMG_HEIGHT)
        
        headless = os.getenv("HEADLESS", "1") == "1"
        window_name = "Tracking"
        if not headless:
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        prev_ts = time.time()
        fps_ema = 0.0

        listener_task = None
        try:
            listener_task = asyncio.create_task(self._listen_assignment_request())

            while cap.isOpened():
                success, frame = cap.read()
                if not success:
                    logger.warning("[VideoCapture] 프레임을 읽을 수 없습니다. 비디오 종료 또는 오류")
                    break
                
                results = self.model.track(
                    frame, 
                    persist=True,
                    imgsz=IMG_SIZE,
                    conf=CONF_THRES,
                    iou=IOU_THRES,
                    tracker=self.tracker_cfg,
                    verbose=False
                )
                
                if not results or len(results) == 0:
                    continue
                    
                r = results[0]
                try:
                    im0 = r.orig_img if hasattr(r, "orig_img") else None
                    if im0 is None:
                        continue
                    angles = self.vis.draw_direction_arrows(im0, r)
                    
                    ids = extract_track_ids(r) or []
                    now_ts = time.time()
                    for tid in ids:
                        tid_i = int(tid)
                        self._last_seen_by_id[tid_i] = now_ts
                        self._reported_lost.discard(tid_i)
                    self.plate_mgr.ensure_mapping(ids)

                    dets = get_detections_with_ids(r)
                    self.vis.draw_plate_labels(im0, dets)

                    now_ts = time.time()
                    h_full, w_full = im0.shape[:2]
                    
                    boxes_size = self.extract_boxes_size(ids)

                    polys, centers = self.vis.draw_boxes(im0, r, angles, boxes_size=boxes_size)
                    
                    self.parking.update(centers, ids, w_full, h_full, now_ts)
                    await self._handle_exit_events()

                    try:
                        self._last_frame_wh = (w_full, h_full)
                        if polys and ids:
                            for idx, tid in enumerate(ids):
                                if idx < len(polys):
                                    self._last_poly_by_id[int(tid)] = polys[idx]
                    except Exception:
                        pass


                    if not headless:
                        self.vis.draw_parking_zones(im0)
                    self.vis.draw_status_panel(im0, (10, 10), self.resv.get_reserved())
                    try:
                        self._last_angle_by_id.update(extract_angles_by_id(r))
                        self._last_center_by_id.update(extract_centers_by_id(r))
                    except Exception:
                        pass

                    await self._handle_parking_completion()

                    await self._handle_mispark_release(self._get_occupant_map())
                    await self._handle_preemption_and_reassign()
                    await self._handle_exit_events()

                    await self._handle_lost_tracks(now_ts)

                    if now_ts - self._last_snapshot_ts >= SNAPSHOT_INTERVAL_S:
                        await self._send_snapshot(r, w_full, h_full)
                        self._last_snapshot_ts = now_ts

                    cur = time.time()
                    dt = max(1e-6, cur - prev_ts)
                    prev_ts = cur
                    inst_fps = 1.0 / dt
                    fps_ema = inst_fps if fps_ema == 0.0 else (0.9 * fps_ema + 0.1 * inst_fps)
                    if not headless:
                        cv2.putText(im0, f"FPS: {fps_ema:.1f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2, cv2.LINE_AA)

                    if not headless:
                        im_disp = self._resize_for_display(im0, OUTPUT_WIDTH, OUTPUT_HEIGHT)
                        cv2.imshow(window_name, im_disp)
                        key = cv2.waitKey(1) & 0xFF
                        if key == 27:
                            logger.info("[Main] ESC 키로 종료 요청됨")
                            break
                        try:
                            if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                                logger.info("[Main] 윈도우가 닫혀서 종료")
                                break
                        except Exception:
                            pass
                except KeyboardInterrupt:
                    logger.info("[Main] KeyboardInterrupt로 종료 요청됨")
                    break
                except Exception as loop_err:
                    logger.exception(f"[RunLoop] error: {loop_err}")
                finally:
                    await asyncio.sleep(0)
            
            cap.release()
            
        except KeyboardInterrupt:
            logger.info("[Main] KeyboardInterrupt로 종료 요청됨")
        except Exception as e:
            logger.exception(f"[Main] 예상치 못한 오류: {e}")
        finally:
            logger.info("[Main] 프로그램 종료 중...")
            try:
                if listener_task and not listener_task.done():
                    logger.info("[Main] listener_task 취소 중...")
                    listener_task.cancel()
                    try:
                        await asyncio.wait_for(listener_task, timeout=2.0)
                    except asyncio.TimeoutError:
                        logger.warning("[Main] listener_task 취소 타임아웃")
                    except Exception:
                        pass
            except Exception as e:
                logger.error(f"[Main] listener_task 정리 중 오류: {e}")
            
            try:
                if self._event_loop_task and not self._event_loop_task.done():
                    logger.info("[Main] event_loop_task 취소 중...")
                    self._event_loop_task.cancel()
                    try:
                        await asyncio.wait_for(self._event_loop_task, timeout=2.0)
                    except asyncio.TimeoutError:
                        logger.warning("[Main] event_loop_task 취소 타임아웃")
                    except Exception:
                        pass
            except Exception as e:
                logger.error(f"[Main] event_loop_task 정리 중 오류: {e}")
            
            try:
                logger.info("[Main] WebSocket 연결 종료 중...")
                self.ws.close()
            except Exception as e:
                logger.error(f"[Main] WebSocket 종료 중 오류: {e}")
            
            try:
                if not headless:
                    logger.info("[Main] OpenCV 윈도우 정리 중...")
                    cv2.destroyAllWindows()
            except Exception as e:
                logger.error(f"[Main] OpenCV 윈도우 정리 중 오류: {e}")
            
            logger.info("[Main] 프로그램 종료 완료")

if __name__ == "__main__":
    try:
        ws = WSClient(WSS_URL)
        logger.info("[Main] 프로그램 시작")
        asyncio.run(TrackerApp(ws).run())
    except KeyboardInterrupt:
        logger.info("[Main] KeyboardInterrupt로 프로그램 종료")
    except Exception as e:
        logger.exception(f"[Main] 프로그램 실행 중 오류: {e}")
    finally:
        logger.info("[Main] 프로그램 완전 종료")
