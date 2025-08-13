import cv2
from ultralytics import YOLO
import os
import numpy as np
import math
from collections import defaultdict
import time
from datetime import datetime

class ParkingStatus:
    """주차 상태를 관리하는 클래스"""
    def __init__(self):
        self.parked_vehicles = {}  # {track_id: {'start_time': timestamp, 'duration': seconds, 'position': (x, y)}}
        self.parking_threshold = 3.0  # 주차로 판단할 시간 (초)
        self.movement_threshold = 50   # 움직임으로 판단할 픽셀 거리
        self.parking_zones = []        # 주차 구역 정의
        
    def add_parking_zone(self, x1, y1, x2, y2):
        """주차 구역 추가"""
        self.parking_zones.append((x1, y1, x2, y2))
    
    def is_in_parking_zone(self, x, y):
        """좌표가 주차 구역 내에 있는지 확인"""
        for x1, y1, x2, y2 in self.parking_zones:
            if x1 <= x <= x2 and y1 <= y <= y2:
                return True
        return False
    
    def update_vehicle_status(self, track_id, position, timestamp):
        """차량의 주차 상태 업데이트"""
        if track_id not in self.parked_vehicles:
            # 새로운 차량 등록
            self.parked_vehicles[track_id] = {
                'start_time': timestamp,
                'duration': 0,
                'position': position,
                'last_position': position,
                'is_parked': False
            }
        else:
            # 기존 차량 위치 업데이트
            vehicle = self.parked_vehicles[track_id]
            last_pos = vehicle['last_position']
            
            # 이동 거리 계산
            distance = math.sqrt((position[0] - last_pos[0])**2 + (position[1] - last_pos[1])**2)
            
            if distance < self.movement_threshold:
                # 움직임이 적으면 주차 시간 누적
                vehicle['duration'] = timestamp - vehicle['start_time']
                if vehicle['duration'] >= self.parking_threshold and not vehicle['is_parked']:
                    vehicle['is_parked'] = True
            else:
                # 움직임이 크면 주차 상태 리셋
                vehicle['start_time'] = timestamp
                vehicle['duration'] = 0
                vehicle['is_parked'] = False
            
            vehicle['last_position'] = position
    
    def get_parking_status(self, track_id):
        """차량의 주차 상태 반환"""
        if track_id in self.parked_vehicles:
            return self.parked_vehicles[track_id]
        return None
    
    def get_parked_vehicles_count(self):
        """주차된 차량 수 반환"""
        return sum(1 for vehicle in self.parked_vehicles.values() if vehicle['is_parked'])

class EnhancedVideoProcessor:
    def __init__(self, model_path="best (6).pt"):
        """
        향상된 비디오 처리 시스템 초기화
        
        Args:
            model_path (str): YOLO 모델 경로
        """
        self.model = YOLO(model_path)
        self.track_history = defaultdict(list)
        self.current_active_track_ids = set()
        self.parking_status = ParkingStatus()
        
        # 추적 설정
        self.conf_threshold = 0.05
        self.iou_threshold = 0.3
        
        # 카메라 밝기 조절 설정
        self.brightness_adjustment = 0.0
        self.contrast_adjustment = 1.0
        self.gamma_adjustment = 1.0
        
        # 주차 구역 설정 (예시 - 실제 환경에 맞게 조정 필요)
        self.setup_parking_zones()
        
        print(f"모델 로드 완료: {model_path}")
        print("주차 감지 시스템 초기화 완료")
    
    def setup_parking_zones(self):
        """주차 구역 설정 (실제 환경에 맞게 조정 필요)"""
        # 예시 주차 구역 (전체 화면을 주차 구역으로 설정)
        # 실제 사용시에는 특정 영역만 주차 구역으로 설정
        self.parking_status.add_parking_zone(0, 0, 1920, 1080)  # 전체 화면
    
    def adjust_brightness(self, frame):
        """프레임의 밝기를 조절"""
        if self.brightness_adjustment != 0:
            frame = cv2.convertScaleAbs(frame, alpha=1, beta=self.brightness_adjustment)
        
        if self.contrast_adjustment != 1.0:
            frame = cv2.convertScaleAbs(frame, alpha=self.contrast_adjustment, beta=0)
        
        if self.gamma_adjustment != 1.0:
            gamma_table = np.array([((i / 255.0) ** (1.0 / self.gamma_adjustment)) * 255
                                  for i in np.arange(0, 256)]).astype("uint8")
            frame = cv2.LUT(frame, gamma_table)
        
        return frame
    
    def set_brightness(self, brightness):
        """밝기 설정"""
        self.brightness_adjustment = max(-100, min(100, brightness))
        print(f"밝기 설정: {self.brightness_adjustment}")
    
    def set_contrast(self, contrast):
        """대비 설정"""
        self.contrast_adjustment = max(0.1, min(3.0, contrast))
        print(f"대비 설정: {self.contrast_adjustment}")
    
    def set_gamma(self, gamma):
        """감마 설정"""
        self.gamma_adjustment = max(0.1, min(3.0, gamma))
        print(f"감마 설정: {self.gamma_adjustment}")
    
    def reset_brightness_settings(self):
        """밝기 설정을 기본값으로 초기화"""
        self.brightness_adjustment = 0.0
        self.contrast_adjustment = 1.0
        self.gamma_adjustment = 1.0
        print("밝기 설정이 기본값으로 초기화되었습니다.")
    
    def draw_enhanced_box(self, frame, xyxy, track_id, class_name, confidence, color):
        """향상된 박스 그리기"""
        x1, y1, x2, y2 = map(int, xyxy)
        
        # 박스 그리기
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        
        # 중심점 계산
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2
        
        # 주차 상태 확인
        parking_info = self.parking_status.get_parking_status(track_id)
        parking_text = ""
        if parking_info and parking_info['is_parked']:
            parking_text = " [PARKED]"
            color = (0, 255, 0)  # 주차된 차량은 초록색으로 표시
        
        # 라벨 텍스트
        label = f"ID:{track_id} {class_name} {confidence:.2f}{parking_text}"
        
        # 라벨 배경 그리기
        (label_width, label_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        frame_h, frame_w = frame.shape[:2]
        label_top = max(0, y1 - label_height - 10)
        label_bottom = min(max(label_height + 5, y1), frame_h - 1)
        rect_left = max(0, x1)
        rect_right = min(x1 + label_width, frame_w - 1)
        cv2.rectangle(frame, (rect_left, label_top),
                     (rect_right, label_bottom), color, -1)
        
        # 라벨 텍스트 그리기
        text_x = max(0, min(x1, frame_w - label_width))
        text_y = min(max(15, y1 - 5), frame_h - 5)
        cv2.putText(frame, label, (text_x, text_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # 주차 시간 표시
        if parking_info and parking_info['is_parked']:
            duration_text = f"주차시간: {parking_info['duration']:.1f}초"
            cv2.putText(frame, duration_text, (x1, y2 + 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        return center_x, center_y
    
    def draw_track_history(self, frame, track_id, current_pos):
        """추적 히스토리 및 진행 방향 그리기"""
        history = self.track_history[track_id]
        
        # 최근 경로 표시
        recent_history = history[-30:]
        for i in range(1, len(recent_history)):
            if recent_history[i - 1] is not None and recent_history[i] is not None:
                cv2.line(frame, recent_history[i - 1], recent_history[i], (0, 255, 0), 2)
        
        # 진행 방향 벡터 표시
        if len(history) > 0 and history[-1] is not None:
            prev_x, prev_y = history[-1]
            curr_x, curr_y = current_pos
            
            dx = curr_x - prev_x
            dy = curr_y - prev_y
            
            if dx * dx + dy * dy > 4:
                cv2.arrowedLine(frame, (prev_x, prev_y), (curr_x, curr_y),
                               (0, 255, 255), 2, tipLength=0.4)
                
                angle_deg = math.degrees(math.atan2(dy, dx))
                cv2.putText(frame, f"Dir: {angle_deg:.1f}°",
                           (curr_x + 5, curr_y - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        
        # 현재 위치를 히스토리에 추가
        history.append(current_pos)
        if len(history) > 100:
            del history[:-100]
    
    def get_color(self, class_id):
        """클래스별 색상 반환"""
        colors = [
            (255, 0, 0),    # 빨강
            (0, 255, 0),    # 초록
            (0, 0, 255),    # 파랑
            (255, 255, 0),  # 노랑
            (255, 0, 255),  # 마젠타
            (0, 255, 255),  # 시안
            (128, 0, 128),  # 보라
            (255, 165, 0),  # 주황
        ]
        return colors[class_id % len(colors)]
    
    def draw_parking_info(self, frame):
        """주차 정보 표시"""
        parked_count = self.parking_status.get_parked_vehicles_count()
        total_vehicles = len(self.current_active_track_ids)
        
        # 주차 정보 배경
        cv2.rectangle(frame, (10, 200), (300, 280), (0, 0, 0), -1)
        cv2.rectangle(frame, (10, 200), (300, 280), (255, 255, 255), 2)
        
        # 주차 정보 텍스트
        cv2.putText(frame, f"주차된 차량: {parked_count}대", (20, 225),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"총 차량: {total_vehicles}대", (20, 250),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # 주차 구역 표시
        for i, (x1, y1, x2, y2) in enumerate(self.parking_status.parking_zones):
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 2)
            cv2.putText(frame, f"주차구역 {i+1}", (x1, y1-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
    
    def create_kick_off_frame(self, width, height, fps, total_frames):
        """Kick-off 프레임 생성"""
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # 그라데이션 배경
        for y in range(height):
            intensity = int(20 * (y / height))
            frame[y, :] = [intensity, intensity, intensity]
        
        center_x, center_y = width // 2, height // 2
        
        # 메인 제목
        title = "주차 감지 시스템"
        title_size = cv2.getTextSize(title, cv2.FONT_HERSHEY_DUPLEX, 2.0, 3)[0]
        title_x = center_x - title_size[0] // 2
        title_y = center_y - 80
        
        cv2.rectangle(frame, (title_x - 20, title_y - title_size[1] - 20),
                     (title_x + title_size[0] + 20, title_y + 20), (50, 50, 50), -1)
        cv2.putText(frame, title, (title_x, title_y), cv2.FONT_HERSHEY_DUPLEX, 2.0, (255, 255, 255), 3)
        
        # 부제목
        subtitle = "Parking Detection System"
        subtitle_size = cv2.getTextSize(subtitle, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2)[0]
        subtitle_x = center_x - subtitle_size[0] // 2
        subtitle_y = center_y - 20
        
        cv2.putText(frame, subtitle, (subtitle_x, subtitle_y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
        
        # 시스템 정보
        info_y = center_y + 40
        info_texts = [
            f"해상도: {width}x{height}",
            f"FPS: {fps}",
            f"총 프레임: {total_frames:,}",
            f"모델: {self.model.ckpt_path if hasattr(self.model, 'ckpt_path') else 'best (6).pt'}"
        ]
        
        for i, text in enumerate(info_texts):
            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 1)[0]
            text_x = center_x - text_size[0] // 2
            text_y = info_y + i * 30
            
            cv2.putText(frame, text, (text_x, text_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 1)
        
        return frame
    
    def process_video_enhanced(self, source_path="WIN_20250807_10_08_53_Pro.mp4"):
        """향상된 비디오 처리 (주차 감지 포함)"""
        print("주차 감지 시스템 시작...")
        
        cap = cv2.VideoCapture(source_path)
        if not cap.isOpened():
            print(f"비디오 파일을 열 수 없습니다: {source_path}")
            return
        
        # 비디오 정보
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        if fps <= 0: fps = 30
        if width <= 0 or height <= 0: width, height = 640, 480
        
        print(f"비디오 정보 - 해상도: {width}x{height}, FPS: {fps}, 총 프레임: {total_frames}")
        
        # 출력 설정
        output_path = "./output/parking_detection_output.mp4"
        os.makedirs("./output", exist_ok=True)
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        # Kick-off 프레임
        kick_off_frame = self.create_kick_off_frame(width, height, fps, total_frames)
        out.write(kick_off_frame)
        
        frame_count = 0
        start_time = cv2.getTickCount()
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_count += 1
                current_time = time.time()
                
                # 밝기 조절 적용
                frame = self.adjust_brightness(frame)
                
                # 현재 프레임 활성 트랙 초기화
                self.current_active_track_ids.clear()
                
                # 진행률 표시
                if frame_count % 30 == 0:
                    progress = (frame_count / total_frames) * 100 if total_frames > 0 else 0.0
                    print(f"처리 진행률: {progress:.1f}% ({frame_count}/{total_frames})")
                
                # YOLO 추적 실행
                results = self.model.track(
                    frame,
                    conf=self.conf_threshold,
                    iou=self.iou_threshold,
                    tracker="bytetrack.yaml",
                    persist=True,
                    verbose=False,
                    imgsz=(640, 640),
                )
                
                if results and len(results) > 0:
                    result = results[0]
                    
                    # OBB 결과 처리
                    if hasattr(result, 'obb') and result.obb is not None:
                        self.process_obb_results(frame, result, current_time)
                    else:
                        # 일반 바운딩 박스 결과 처리
                        self.process_bbox_results(frame, result, current_time)
                
                # 성능 정보 표시
                elapsed_time = (cv2.getTickCount() - start_time) / cv2.getTickFrequency()
                current_fps = frame_count / elapsed_time if elapsed_time > 0 else 0
                
                # 정보 오버레이
                cv2.putText(frame, f"FPS: {current_fps:.1f}", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.putText(frame, f"Frame: {frame_count}/{total_frames}", (10, 70),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                active_tracks = len(self.current_active_track_ids)
                cv2.putText(frame, f"Active Tracks: {active_tracks}", (10, 110),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                # 밝기 설정 정보
                brightness_info = f"Brightness: {self.brightness_adjustment:.1f}"
                cv2.putText(frame, brightness_info, (10, 150),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                
                contrast_info = f"Contrast: {self.contrast_adjustment:.1f}"
                cv2.putText(frame, contrast_info, (10, 180),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                
                # 주차 정보 표시
                self.draw_parking_info(frame)
                
                # 프레임을 출력 비디오에 쓰기
                out.write(frame)
                
        except KeyboardInterrupt:
            print("사용자에 의해 중단되었습니다.")
        finally:
            cap.release()
            out.release()
            cv2.destroyAllWindows()
            
            # 처리 완료 정보
            total_time = (cv2.getTickCount() - start_time) / cv2.getTickFrequency()
            avg_fps = frame_count / total_time if total_time > 0 else 0
            
            print(f"\n처리 완료!")
            print(f"총 처리 시간: {total_time:.2f}초")
            print(f"평균 FPS: {avg_fps:.1f}")
            print(f"처리된 프레임: {frame_count}")
            print(f"결과 영상: {output_path}")
            print("주차 감지 기능이 적용된 영상이 생성되었습니다.")
    
    def process_obb_results(self, frame, result, current_time):
        """OBB 결과 처리"""
        xywhr = result.obb.xywhr
        xyxyxyxy = result.obb.xyxyxyxy
        classes = result.obb.cls.int()
        confidences = result.obb.conf
        
        track_ids = None
        if hasattr(result, 'boxes') and result.boxes is not None:
            if hasattr(result.boxes, 'id') and result.boxes.id is not None:
                track_ids = result.boxes.id.int()
        
        for i in range(len(xyxyxyxy)):
            box_coords = xyxyxyxy[i].cpu().numpy()
            confidence = confidences[i].item()
            class_id = classes[i].item()
            class_name = result.names[class_id]
            track_id = track_ids[i].item() if track_ids is not None else i
            color = self.get_color(class_id)
            
            # OBB 박스 그리기
            points = np.array(box_coords, dtype=np.int32).reshape(-1, 2)
            cv2.polylines(frame, [points], True, color, 2)
            
            # 중심점 계산
            center_x = int(np.mean(points[:, 0]))
            center_y = int(np.mean(points[:, 1]))
            
            # 주차 상태 업데이트
            self.parking_status.update_vehicle_status(track_id, (center_x, center_y), current_time)
            
            # 라벨 그리기
            parking_info = self.parking_status.get_parking_status(track_id)
            parking_text = ""
            if parking_info and parking_info['is_parked']:
                parking_text = " [PARKED]"
                color = (0, 255, 0)
            
            label = f"ID:{track_id} {class_name} {confidence:.2f}{parking_text}"
            cv2.putText(frame, label, (center_x - 50, center_y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            
            # 추적 히스토리 및 활성 트랙 기록
            self.draw_track_history(frame, track_id, (center_x, center_y))
            self.current_active_track_ids.add(int(track_id))
            
            # 각도 정보
            if len(xywhr) > i:
                angle_rad = xywhr[i][4].item()
                angle_deg = math.degrees(angle_rad)
                cv2.putText(frame, f"Angle: {angle_deg:.1f}°", 
                           (center_x, center_y + 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    
    def process_bbox_results(self, frame, result, current_time):
        """일반 바운딩 박스 결과 처리"""
        if hasattr(result, 'boxes') and result.boxes is not None:
            boxes = result.boxes
            xyxy = boxes.xyxy.cpu().numpy()
            confidences = boxes.conf.cpu().numpy()
            classes = boxes.cls.int().cpu().numpy()
            
            track_ids = None
            if hasattr(boxes, 'id') and boxes.id is not None:
                track_ids = boxes.id.int().cpu().numpy()
            
            for i in range(len(xyxy)):
                box = xyxy[i]
                confidence = confidences[i]
                class_id = classes[i]
                class_name = result.names[class_id]
                track_id = track_ids[i] if track_ids is not None else i
                color = self.get_color(class_id)
                
                # 중심점 계산
                center_x = (int(box[0]) + int(box[2])) // 2
                center_y = (int(box[1]) + int(box[3])) // 2
                
                # 주차 상태 업데이트
                self.parking_status.update_vehicle_status(track_id, (center_x, center_y), current_time)
                
                # 향상된 박스 그리기
                center_x, center_y = self.draw_enhanced_box(
                    frame, box, track_id, class_name, confidence, color
                )
                
                # 추적 히스토리 및 활성 트랙 기록
                self.draw_track_history(frame, track_id, (center_x, center_y))
                self.current_active_track_ids.add(int(track_id))

def process_video():
    """기본 비디오 처리"""
    processor = EnhancedVideoProcessor("best.pt")
    processor.process_video_enhanced()

if __name__ == "__main__":
    # 기본 처리
    process_video()