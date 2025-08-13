import cv2
from ultralytics import YOLO
import os
import numpy as np
import math
from collections import defaultdict

class EnhancedVideoProcessor:
    def __init__(self, model_path="best (6).pt"):
        """
        향상된 비디오 처리 시스템 초기화
        
        Args:
            model_path (str): YOLO 모델 경로
        """
        self.model = YOLO(model_path)
        self.track_history = defaultdict(list)
        self.track_count = 0
        self.current_active_track_ids = set()
        
        # 추적 설정
        self.conf_threshold = 0.05
        self.iou_threshold = 0.3
        
        print(f"모델 로드 완료: {model_path}")
    
    def draw_enhanced_box(self, frame, xyxy, track_id, class_name, confidence, color):
        """
        향상된 박스 그리기 (OBB 지원)
        
        Args:
            frame: 프레임
            xyxy: 바운딩 박스 좌표
            track_id: 추적 ID
            class_name: 클래스 이름
            confidence: 신뢰도
            color: 색상
        """
        x1, y1, x2, y2 = map(int, xyxy)
        
        # 박스 그리기
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        
        # 중심점 계산
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2
        
        # 라벨 텍스트
        label = f"ID:{track_id} {class_name} {confidence:.2f}"
        
        # 라벨 배경 그리기 (프레임 밖으로 나가지 않도록 클램프)
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
        
        return center_x, center_y
    
    def draw_track_history(self, frame, track_id, current_pos):
        """추적 히스토리 및 진행 방향(벡터) 그리기"""
        history = self.track_history[track_id]  # defaultdict(list) 이므로 자동 초기화

        # 최근 경로(최대 30개 포인트)를 라인으로 표시
        recent_history = history[-30:]
        for i in range(1, len(recent_history)):
            if recent_history[i - 1] is not None and recent_history[i] is not None:
                cv2.line(frame, recent_history[i - 1], recent_history[i], (0, 255, 0), 2)

        # 이전 위치가 있다면, 이전 -> 현재로 진행 방향 벡터(화살표) 표시
        if len(history) > 0 and history[-1] is not None:
            prev_x, prev_y = history[-1]
            curr_x, curr_y = current_pos

            dx = curr_x - prev_x
            dy = curr_y - prev_y

            # 너무 작은 이동은 노이즈로 간주하여 제외
            if dx * dx + dy * dy > 4:  # > 2px 이동
                # 화살표 그리기 (노란색)
                cv2.arrowedLine(
                    frame,
                    (prev_x, prev_y),
                    (curr_x, curr_y),
                    (0, 255, 255),
                    2,
                    tipLength=0.4,
                )

                # 진행 방향 각도(도 단위) 표시: x축(오른쪽)을 0°, 반시계 양수
                angle_deg = math.degrees(math.atan2(dy, dx))
                cv2.putText(
                    frame,
                    f"Dir: {angle_deg:.1f}°",
                    (curr_x + 5, curr_y - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 255),
                    1,
                )

        # 현재 위치를 히스토리에 추가
        history.append(current_pos)
        # 히스토리 무한 증가 방지 (최근 100개만 유지)
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
    
    def create_kick_off_frame(self, width, height, fps, total_frames):
        """
        Kick-off 프레임 생성
        
        Args:
            width (int): 프레임 너비
            height (int): 프레임 높이
            fps (int): 프레임 레이트
            total_frames (int): 총 프레임 수
            
        Returns:
            kick_off_frame: Kick-off 프레임
        """
        # 검은 배경 생성
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # 그라데이션 배경 (검은색에서 어두운 회색으로)
        for y in range(height):
            intensity = int(20 * (y / height))  # 0~20 범위의 그라데이션
            frame[y, :] = [intensity, intensity, intensity]
        
        # 중앙에 로고/제목 영역
        center_x, center_y = width // 2, height // 2
        
        # 메인 제목
        title = "YOLO Enhanced Tracking"
        title_size = cv2.getTextSize(title, cv2.FONT_HERSHEY_DUPLEX, 2.0, 3)[0]
        title_x = center_x - title_size[0] // 2
        title_y = center_y - 80
        
        # 제목 배경
        cv2.rectangle(frame, (title_x - 20, title_y - title_size[1] - 20),
                     (title_x + title_size[0] + 20, title_y + 20), (50, 50, 50), -1)
        cv2.putText(frame, title, (title_x, title_y), cv2.FONT_HERSHEY_DUPLEX, 2.0, (255, 255, 255), 3)
        
        # 부제목
        subtitle = "Processing Started"
        subtitle_size = cv2.getTextSize(subtitle, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2)[0]
        subtitle_x = center_x - subtitle_size[0] // 2
        subtitle_y = center_y - 20
        
        cv2.putText(frame, subtitle, (subtitle_x, subtitle_y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
        
        # 비디오 정보 표시
        info_y = center_y + 40
        info_texts = [
            f"Resolution: {width}x{height}",
            f"FPS: {fps}",
            f"Total Frames: {total_frames:,}",
            f"Model: {self.model.ckpt_path if hasattr(self.model, 'ckpt_path') else 'best (6).pt'}"
        ]
        
        for i, text in enumerate(info_texts):
            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 1)[0]
            text_x = center_x - text_size[0] // 2
            text_y = info_y + i * 30
            
            cv2.putText(frame, text, (text_x, text_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 1)
        
        # 진행 표시줄 (시뮬레이션)
        progress_y = center_y + 180
        progress_width = width - 200
        progress_x = 100
        
        # 진행 표시줄 배경
        cv2.rectangle(frame, (progress_x, progress_y), 
                     (progress_x + progress_width, progress_y + 20), (100, 100, 100), -1)
        
        # 진행 표시줄 (0%에서 시작)
        progress_fill = int(progress_width * 0.0)
        cv2.rectangle(frame, (progress_x, progress_y), 
                     (progress_x + progress_fill, progress_y + 20), (0, 255, 0), -1)
        
        # 진행률 텍스트
        progress_text = "0%"
        progress_text_size = cv2.getTextSize(progress_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)[0]
        progress_text_x = center_x - progress_text_size[0] // 2
        progress_text_y = progress_y + 40
        
        cv2.putText(frame, progress_text, (progress_text_x, progress_text_y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # 하단 안내 메시지
        bottom_text = "Enhanced tracking with ByteTrack and OBB support"
        bottom_text_size = cv2.getTextSize(bottom_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)[0]
        bottom_text_x = center_x - bottom_text_size[0] // 2
        bottom_text_y = height - 50
        
        cv2.putText(frame, bottom_text, (bottom_text_x, bottom_text_y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (150, 150, 150), 1)
        
        return frame
    
    def process_video_enhanced(self, source_path="WIN_20250807_10_08_53_Pro.mp4"):
        """
        향상된 비디오 처리
        
        Args:
            source_path (str): 입력 비디오 파일 경로
        """
        print("향상된 영상 처리 시작...")
        
        # 비디오 캡처 열기
        cap = cv2.VideoCapture(source_path)
        if not cap.isOpened():
            print(f"비디오 파일을 열 수 없습니다: {source_path}")
            return
        
        # 비디오 정보 가져오기
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # 안전한 기본값 대체
        if fps <= 0:
            fps = 30
        if width <= 0 or height <= 0:
            width, height = 640, 480
        
        print(f"비디오 정보 - 해상도: {width}x{height}, FPS: {fps}, 총 프레임: {total_frames}")
        
        # 출력 비디오 설정
        output_path = "./output/enhanced_output.mp4"
        os.makedirs("./output", exist_ok=True)
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        # Kick-off 프레임 생성
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
                    
                    # OBB 결과 처리 (OBB가 있는 경우)
                    if hasattr(result, 'obb') and result.obb is not None:
                        self.process_obb_results(frame, result)
                    else:
                        # 일반 바운딩 박스 결과 처리
                        self.process_bbox_results(frame, result)
                
                # 성능 정보 표시
                current_time = cv2.getTickCount()
                elapsed_time = (current_time - start_time) / cv2.getTickFrequency()
                current_fps = frame_count / elapsed_time if elapsed_time > 0 else 0
                
                # 정보 오버레이 그리기
                cv2.putText(frame, f"FPS: {current_fps:.1f}", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.putText(frame, f"Frame: {frame_count}/{total_frames}", (10, 70),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                # 활성 추적 객체 수 표시 (현재 프레임 기준)
                active_tracks = len(self.current_active_track_ids)
                cv2.putText(frame, f"Active Tracks: {active_tracks}", (10, 110),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                # 밝기 설정 정보 표시
                brightness_info = f"Brightness: {self.brightness_adjustment:.1f}"
                cv2.putText(frame, brightness_info, (10, 150),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                
                contrast_info = f"Contrast: {self.contrast_adjustment:.1f}"
                cv2.putText(frame, contrast_info, (10, 180),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                
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
            print("향상된 추적 기능이 적용된 영상이 생성되었습니다.")
    
    def process_obb_results(self, frame, result):
        """OBB 결과 처리"""
        xywhr = result.obb.xywhr
        xyxyxyxy = result.obb.xyxyxyxy
        classes = result.obb.cls.int()
        confidences = result.obb.conf
        
        # 추적 ID
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
            
            # 라벨 그리기
            label = f"ID:{track_id} {class_name} {confidence:.2f}"
            cv2.putText(frame, label, (center_x - 50, center_y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            
            # 추적 히스토리 및 활성 트랙 기록
            self.draw_track_history(frame, track_id, (center_x, center_y))
            self.current_active_track_ids.add(int(track_id))
            
            # 각도 정보 (OBB 특성)
            if len(xywhr) > i:
                angle_rad = xywhr[i][4].item()
                angle_deg = math.degrees(angle_rad)
                cv2.putText(frame, f"Angle: {angle_deg:.1f}°", 
                           (center_x, center_y + 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    
    def process_bbox_results(self, frame, result):
        """일반 바운딩 박스 결과 처리"""
        if hasattr(result, 'boxes') and result.boxes is not None:
            boxes = result.boxes
            xyxy = boxes.xyxy.cpu().numpy()
            confidences = boxes.conf.cpu().numpy()
            classes = boxes.cls.int().cpu().numpy()
            
            # 추적 ID
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
                
                # 향상된 박스 그리기
                center_x, center_y = self.draw_enhanced_box(
                    frame, box, track_id, class_name, confidence, color
                )
                
                # 추적 히스토리 및 활성 트랙 기록
                self.draw_track_history(frame, track_id, (center_x, center_y))
                self.current_active_track_ids.add(int(track_id))

def process_video():
    """기존 호환성을 위한 함수"""
    processor = EnhancedVideoProcessor("best (6).pt")
    processor.process_video_enhanced()

def process_video_with_brightness_control():
    """밝기 조절 기능이 포함된 비디오 처리 예제"""
    processor = EnhancedVideoProcessor("best (6).pt")
    
    # 밝기 설정 예제
    print("=== 밝기 조절 설정 예제 ===")
    processor.set_brightness(20)      # 밝기 +20 증가
    processor.set_contrast(1.2)       # 대비 20% 증가
    processor.set_gamma(1.1)          # 감마 10% 증가
    
    print("\n비디오 처리 시작...")
    processor.process_video_enhanced()

def process_video_with_dark_environment():
    """어두운 환경을 위한 밝기 설정"""
    processor = EnhancedVideoProcessor("best (6).pt")
    
    # 어두운 환경을 위한 설정
    processor.set_brightness(50)      # 밝기 대폭 증가
    processor.set_contrast(1.5)       # 대비 증가
    processor.set_gamma(0.8)          # 감마 감소 (어두운 부분 밝게)
    
    print("어두운 환경 설정으로 비디오 처리 시작...")
    processor.process_video_enhanced()

def process_video_with_bright_environment():
    """밝은 환경을 위한 밝기 설정"""
    processor = EnhancedVideoProcessor("best (6).pt")
    
    # 밝은 환경을 위한 설정
    processor.set_brightness(-60)     # 밝기 감소
    processor.set_contrast(1.5)       # 대비 증가
    
    print("밝은 환경 설정으로 비디오 처리 시작...")
    processor.process_video_enhanced()

if __name__ == "__main__":
    # 기본 처리
    # process_video()
    
    # 밝기 조절 기능이 포함된 처리
    # process_video_with_brightness_control()
    
    # 환경별 설정 예제 (주석 해제하여 사용)
    # process_video_with_dark_environment()
    process_video_with_bright_environment() 