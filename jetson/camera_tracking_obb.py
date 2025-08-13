import cv2
import numpy as np
from ultralytics import YOLO
import time
import math
from collections import defaultdict

class CameraTrackingOBB:
    def __init__(self, model_path="best.pt", camera_id=0):
        """
        카메라 기반 OBB 추적 시스템 초기화
        
        Args:
            model_path (str): YOLO 모델 경로
            camera_id (int): 카메라 ID (기본값: 0)
        """
        self.model = YOLO(model_path)
        self.camera_id = camera_id
        self.cap = None
        self.track_history = defaultdict(list)
        self.track_count = 0
        
        # 추적 설정
        self.conf_threshold = 0.02
        self.iou_threshold = 0.7
        
        print(f"모델 로드 완료: {model_path}")
        print(f"카메라 ID: {camera_id}")
    
    def start_camera(self):
        """카메라 시작"""
        self.cap = cv2.VideoCapture(self.camera_id)
        if not self.cap.isOpened():
            print(f"카메라 {self.camera_id}를 열 수 없습니다.")
            return False
        
        # 카메라 기본 해상도 정보 출력
        width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        
        print(f"카메라 시작 완료 - 해상도: {width}x{height}, FPS: {fps}")
        return True
    
    def draw_obb_box(self, frame, xyxyxyxy, track_id, class_name, confidence, color):
        """
        OBB 박스 그리기
        
        Args:
            frame: 프레임
            xyxyxyxy: 4점 좌표 (x1,y1,x2,y2,x3,y3,x4,y4)
            track_id: 추적 ID
            class_name: 클래스 이름
            confidence: 신뢰도
            color: 색상
        """
        # 4점 좌표를 정수로 변환
        points = np.array(xyxyxyxy, dtype=np.int32).reshape(-1, 2)
        
        # OBB 박스 그리기
        cv2.polylines(frame, [points], True, color, 2)
        
        # 중심점 계산
        center_x = int(np.mean(points[:, 0]))
        center_y = int(np.mean(points[:, 1]))
        
        # 라벨 텍스트
        label = f"ID:{track_id} {class_name} {confidence:.2f}"
        
        # 라벨 배경 그리기
        (label_width, label_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(frame, (center_x - label_width//2, center_y - label_height - 10),
                     (center_x + label_width//2, center_y), color, -1)
        
        # 라벨 텍스트 그리기
        cv2.putText(frame, label, (center_x - label_width//2, center_y - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return center_x, center_y
    
    def draw_track_history(self, frame, track_id, current_pos):
        """추적 히스토리 그리기"""
        if track_id in self.track_history:
            # 최근 30개 포인트만 표시
            history = self.track_history[track_id][-30:]
            
            # 추적 경로 그리기
            for i in range(1, len(history)):
                if history[i-1] is not None and history[i] is not None:
                    cv2.line(frame, history[i-1], history[i], (0, 255, 0), 2)
            
            # 현재 위치를 히스토리에 추가
            self.track_history[track_id].append(current_pos)
    
    def process_frame(self, frame):
        """
        프레임 처리 및 OBB 추적
        
        Args:
            frame: 입력 프레임
            
        Returns:
            processed_frame: 처리된 프레임
        """
        # YOLO 추적 실행
        results = self.model.track(
            frame,
            conf=self.conf_threshold,
            iou=self.iou_threshold,
            tracker="bytetrack.yaml",
            persist=True,
            verbose=False
        )
        
        if results and len(results) > 0:
            result = results[0]
            
            # OBB 결과 처리
            if hasattr(result, 'obb') and result.obb is not None:
                # OBB 정보 추출
                xywhr = result.obb.xywhr  # center-x, center-y, width, height, angle
                xyxyxyxy = result.obb.xyxyxyxy  # 4점 좌표
                classes = result.obb.cls.int()  # 클래스 ID
                confidences = result.obb.conf  # 신뢰도
                
                # 추적 ID (ByteTrack 사용)
                track_ids = None
                if hasattr(result, 'boxes') and result.boxes is not None:
                    if hasattr(result.boxes, 'id') and result.boxes.id is not None:
                        track_ids = result.boxes.id.int()
                
                # 각 검출된 객체 처리
                for i in range(len(xyxyxyxy)):
                    # 좌표 추출
                    box_coords = xyxyxyxy[i].cpu().numpy()
                    confidence = confidences[i].item()
                    class_id = classes[i].item()
                    class_name = result.names[class_id]
                    
                    # 추적 ID 설정
                    track_id = track_ids[i].item() if track_ids is not None else i
                    
                    # 색상 설정 (클래스별)
                    color = self.get_color(class_id)
                    
                    # OBB 박스 그리기
                    center_x, center_y = self.draw_obb_box(
                        frame, box_coords, track_id, class_name, confidence, color
                    )
                    
                    # 추적 히스토리 그리기
                    self.draw_track_history(frame, track_id, (center_x, center_y))
                    
                    # 각도 정보 표시 (OBB 특성)
                    if len(xywhr) > i:
                        angle_rad = xywhr[i][4].item()
                        angle_deg = math.degrees(angle_rad)
                        angle_text = f"Angle: {angle_deg:.1f}°"
                        cv2.putText(frame, angle_text, (center_x, center_y + 20),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        return frame
    
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
    
    def run(self):
        """실시간 카메라 추적 실행"""
        if not self.start_camera():
            return
        
        print("실시간 추적 시작... (종료하려면 'q'를 누르세요)")
        
        try:
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    print("프레임을 읽을 수 없습니다.")
                    break
                
                # 프레임 처리
                processed_frame = self.process_frame(frame)
                
                # FPS 계산
                fps = self.cap.get(cv2.CAP_PROP_FPS)
                cv2.putText(processed_frame, f"FPS: {fps:.1f}", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                # 추적된 객체 수 표시
                active_tracks = len([h for h in self.track_history.values() if len(h) > 0])
                cv2.putText(processed_frame, f"Active Tracks: {active_tracks}", (10, 70),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                # 결과 표시
                cv2.imshow("Camera Tracking OBB", processed_frame)
                
                # 'q' 키로 종료
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                
        except KeyboardInterrupt:
            print("사용자에 의해 중단되었습니다.")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """리소스 정리"""
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        print("카메라 추적 종료")

def main():
    """메인 함수"""
    print("=== 카메라 기반 OBB 추적 시스템 ===")
    
    # 모델 경로 설정 (사용 가능한 모델 중 선택)
    model_paths = ["best.pt"]
    model_path = None
    
    for path in model_paths:
        try:
            # 모델 로드 테스트
            test_model = YOLO(path)
            model_path = path
            print(f"사용할 모델: {path}")
            break
        except Exception as e:
            print(f"모델 {path} 로드 실패: {e}")
    
    if model_path is None:
        print("사용 가능한 모델이 없습니다.")
        return
    
    # 추적 시스템 초기화 및 실행
    tracker = CameraTrackingOBB(model_path=model_path, camera_id=0)
    tracker.run()

if __name__ == "__main__":
    main()
