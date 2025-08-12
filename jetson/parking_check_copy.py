import cv2
from ultralytics import YOLO
import os
import numpy as np
import math
from collections import defaultdict

PARKING_ZONES_NORM = [
    {
        "id": "b1",
        "rect": [0.414251, 0.008621, 0.493357, 0.240421]
    },
    {
        "id": "b2",
        "rect": [0.494565, 0.017241, 0.583333, 0.254789]
    },
    {
        "id": "b3",
        "rect": [0.584541, 0.017241, 0.657609, 0.265326]
    },
    {
        "id": "c1",
        "rect": [0.693237, 0.030651, 0.775362, 0.239464]
    },
    {
        "id": "c2",
        "rect": [0.775362, 0.038314, 0.856280, 0.246169]
    },
    {
        "id": "c3",
        "rect": [0.847826, 0.035441, 0.930556, 0.229885]
    },
    {
        "id": "a1",
        "rect": [0.397343, 0.726054, 0.487319, 0.989464]
    },
    {
        "id": "a2",
        "rect": [0.493357, 0.729885, 0.580918, 0.983716]
    },
    {
        "id": "a3",
        "rect": [0.578502, 0.727011, 0.663647, 0.987548]
    },
    {
        "id": "a4",
        "rect": [0.695048, 0.735632, 0.776570, 0.983716]
    },
    {
        "id": "a5",
        "rect": [0.777174, 0.729885, 0.859300, 0.983716]
    }
]

class EnhancedVideoProcessor:
    def __init__(self, model_path="best.pt"):
        self.model = YOLO(model_path)
        self.track_history = defaultdict(list)
        self.track_count = 0
        
        # 추적 설정
        self.conf_threshold = 0.1  # 신뢰도 임계값을 낮춤
        self.iou_threshold = 0.4
        

        self.rsize = (1920, 1088)
        self.parking_zones = self.init_parking_zones()

        print(f"모델 로드 완료: {model_path}")

    def zone_rect_to_poly(self, rect_norm, width, height):
        x1n, y1n, x2n, y2n = rect_norm
        x1, y1 = int(x1n * width), int(y1n * height)
        x2, y2 = int(x2n * width), int(y2n * height)
        return np.array([[x1, y1], [x2, y1], [x2, y2], [x1, y2]])

    def init_parking_zones(self):
        parking_zones = {}
        for zone in PARKING_ZONES_NORM:
            parking_zones[zone["id"]] = {
                "id": zone["id"],
                "poly": self.zone_rect_to_poly(zone["rect"], self.rsize[0], self.rsize[1])
            }

        return parking_zones
    
    def draw_vehicle_box(self, frame, points, track_id, class_name, confidence, color):
        # OBB 박스 그리기 (두꺼운 선)
        points_array = np.array(points, dtype=np.int32).reshape(-1, 2)
        cv2.polylines(frame, [points_array], True, color, 3)
        
        # 중심점 계산
        center_x = int(np.mean(points_array[:, 0]))
        center_y = int(np.mean(points_array[:, 1]))
        
        # 라벨 배경 그리기
        label = f"ID:{track_id} {class_name} {confidence:.2f}"
        (label_width, label_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
        
        # 라벨 위치 계산 (프레임 밖으로 나가지 않도록)
        frame_h, frame_w = frame.shape[:2]
        label_x = max(0, min(center_x - label_width // 2, frame_w - label_width))
        label_y = max(label_height + 5, center_y - 10)
        
        # 라벨 배경 사각형
        cv2.rectangle(frame, 
                     (label_x - 5, label_y - label_height - 5),
                     (label_x + label_width + 5, label_y + 5), 
                     color, -1)
        
        # 라벨 텍스트 (흰색)
        cv2.putText(frame, label, (label_x, label_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # 중심점에 작은 원 그리기
        cv2.circle(frame, (center_x, center_y), 3, color, -1)
        
        return center_x, center_y

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
    
    def process_video_enhanced(self, source_path="WIN_20250807_10_08_53_Pro.mp4"):
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

        print(f"비디오 정보 - 해상도: {width}x{height}, FPS: {fps}, 총 프레임: {total_frames}")
        
        # 출력 비디오 설정
        output_path = "./output/enhanced_output.mp4"
        os.makedirs("./output", exist_ok=True)
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, self.rsize)
        
        frame_count = 0
        n_frames = 30
        frame_patience = 30  # 차량이 나간 후 5프레임 동안 기다린 후 제거
        start_time = cv2.getTickCount()
        
        # dict 공간:{추적 ID:시간} 반환 변수
        zone_id_to_track_time = {zone_id: {} for zone_id in self.parking_zones}
        # 차량이 나간 후 기다리는 시간을 추적하는 딕셔너리
        zone_id_to_track_patience = {zone_id: {} for zone_id in self.parking_zones}

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_count += 1
                
                # 진행률 표시
                if frame_count % 30 == 0:
                    progress = (frame_count / total_frames) * 100 if total_frames > 0 else 0.0
                    print(f"처리 진행률: {progress:.1f}% ({frame_count}/{total_frames})")
                
                frame = cv2.resize(frame, self.rsize)
                # YOLO 추적 실행 (개선된 설정)
                results = self.model.track(
                    frame,
                    conf=self.conf_threshold,
                    iou=self.iou_threshold,
                    tracker="bytetrack.yaml",
                    persist=True,
                    verbose=False,
                    imgsz=self.rsize,
                    # 추적 안정성을 위한 추가 파라미터
                    # agnostic_nms=True,  # 클래스별 NMS
                )

                if results and len(results) > 0:
                    result = results[0]
                    
                    # 디버깅: 결과 정보 출력
                    if frame_count % 30 == 0:  # 30프레임마다 한 번씩만 출력
                        print(f"Frame {frame_count}: 결과 타입 확인")
                        if hasattr(result, 'obb') and result.obb is not None:
                            print(f"  - OBB 결과: {len(result.obb.xyxyxyxy)}개 객체")
                    
                    # OBB 결과 처리 (OBB가 있는 경우)
                    if hasattr(result, 'obb') and result.obb is not None:
                        zone_to_track_id = self.process_obb_results(frame, result)

                    # 현재 프레임에서 주차공간에 있는 차량들만 추적
                    current_frame_tracks = set()
                    for zone_id, track_ids in zone_to_track_id.items():
                        for track_id in track_ids:
                            current_frame_tracks.add((zone_id, track_id))
                            if track_id not in zone_id_to_track_time[zone_id]:
                                zone_id_to_track_time[zone_id][track_id] = 1
                            else:
                                zone_id_to_track_time[zone_id][track_id] += 1
                    
                    # 이전 프레임에서 있었지만 현재 프레임에서 없는 차량들 처리 (patience 적용)
                    for zone_id in zone_id_to_track_time:
                        tracks_to_remove = []
                        for track_id in zone_id_to_track_time[zone_id]:
                            if (zone_id, track_id) not in current_frame_tracks:
                                # patience 딕셔너리에 추가하거나 증가
                                if track_id not in zone_id_to_track_patience[zone_id]:
                                    zone_id_to_track_patience[zone_id][track_id] = 1
                                    if frame_count % 30 == 0:  # 디버깅 정보
                                        print(f"  - 차량 ID {track_id}가 주차공간 {zone_id}에서 나감 (patience 시작)")
                                else:
                                    zone_id_to_track_patience[zone_id][track_id] += 1
                                
                                # patience 시간이 지나면 제거
                                if zone_id_to_track_patience[zone_id][track_id] >= frame_patience:
                                    tracks_to_remove.append(track_id)
                                    if frame_count % 30 == 0:  # 디버깅 정보
                                        print(f"  - 차량 ID {track_id}가 주차공간 {zone_id}에서 완전히 제거됨 (patience 만료)")
                        
                        # patience가 만료된 차량들 제거
                        for track_id in tracks_to_remove:
                            del zone_id_to_track_time[zone_id][track_id]
                            del zone_id_to_track_patience[zone_id][track_id]
                    
                    # 현재 프레임에 있는 차량들은 patience에서 제거 (다시 들어온 경우)
                    for zone_id, track_ids in zone_to_track_id.items():
                        for track_id in track_ids:
                            if track_id in zone_id_to_track_patience[zone_id]:
                                del zone_id_to_track_patience[zone_id][track_id]
                                if frame_count % 30 == 0:  # 디버깅 정보
                                    print(f"  - 차량 ID {track_id}가 주차공간 {zone_id}에 다시 들어옴 (patience 취소)")

                # 주차공간 색상 표시
                for zone_id in self.parking_zones:
                    track_times = zone_id_to_track_time[zone_id]
                    
                    if not track_times:  # 차량이 없으면 파란색
                        color = (255, 0, 0)  # 파란색
                    else:
                        # 가장 오래 머문 차량의 시간 확인
                        max_time = max(track_times.values()) if track_times else 0
                        
                        if max_time >= n_frames:  # n_frames 이상 머물면 초록색
                            color = (0, 255, 0)  # 초록색
                        else:  # n_frames 미만이면 빨간색
                            color = (0, 0, 255)  # 빨간색
                    
                    cv2.polylines(frame, [self.parking_zones[zone_id]["poly"]], True, color, 2)
                    
                    # 주차공간 ID 표시
                    zone_center = np.mean(self.parking_zones[zone_id]["poly"], axis=0).astype(int)
                    cv2.putText(frame, zone_id, (zone_center[0] - 10, zone_center[1]),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                    

                # 상태 정보 표시
                cv2.putText(frame, f"Frame: {frame_count}", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(frame, f"Threshold: {n_frames} frames", (10, 60),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(frame, f"Patience: {frame_patience} frames", (10, 90),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                # 색상 범례 표시
                legend_y = 130
                cv2.putText(frame, "Blue: Empty", (10, legend_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
                cv2.putText(frame, "Red: Occupied < 10 frames", (10, legend_y + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                cv2.putText(frame, "Green: Occupied >= 10 frames", (10, legend_y + 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                # 프레임을 rsize 크기로 리사이즈 후 출력 비디오에 기록
                resized_frame = cv2.resize(frame, self.rsize)
                out.write(resized_frame)
                
        except KeyboardInterrupt:
            print("사용자에 의해 중단되었습니다.")
        finally:
            cap.release()
            out.release()
            # cv2.destroyAllWindows()  # OpenCV GUI 오류 방지를 위해 주석 처리
            
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
        try:
            xywhr = result.obb.xywhr
            xyxyxyxy = result.obb.xyxyxyxy
            classes = result.obb.cls.int()
            confidences = result.obb.conf
            
            # 추적 ID 안전하게 추출
            track_ids = None
            if hasattr(result, 'boxes') and result.boxes is not None and hasattr(result.boxes, 'id'):
                track_ids = result.boxes.id.int()
            
            zone_to_track_id = {}
            
            # 객체 개수 확인
            num_objects = len(xyxyxyxy)
            if num_objects == 0:
                return zone_to_track_id
            
            for i in range(num_objects):
                try:
                    box_coords = xyxyxyxy[i].cpu().numpy()
                    confidence = confidences[i].item()
                    class_id = classes[i].item()
                    class_name = result.names[class_id]
                    
                    # track_id 안전하게 추출
                    track_id = None
                    if track_ids is not None and i < len(track_ids):
                        track_id = track_ids[i].item()
                    else:
                        # track_id가 없으면 인덱스 사용
                        track_id = i
                    
                    color = self.get_color(class_id)
                    
                    # 향상된 차량 박스 그리기
                    center_x, center_y = self.draw_vehicle_box(frame, box_coords, track_id, class_name, confidence, color)
                    
                    # 각도 정보 (OBB 특성) - 안전하게 처리
                    if i < len(xywhr):
                        angle_rad = xywhr[i][4].item()
                        angle_deg = math.degrees(angle_rad)
                        cv2.putText(frame, f"Angle: {angle_deg:.1f}°", 
                                   (center_x, center_y + 20),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                    
                    # 주차공간 확인
                    for zone_id in self.parking_zones:
                        zone_cnt = self.parking_zones[zone_id]["poly"].reshape(-1, 1, 2)
                        if cv2.pointPolygonTest(zone_cnt, (center_x, center_y), False) >= 0:
                            if zone_id not in zone_to_track_id:
                                zone_to_track_id[zone_id] = []
                            # 중복 방지
                            if track_id not in zone_to_track_id[zone_id]:
                                zone_to_track_id[zone_id].append(track_id)
                
                except Exception as e:
                    print(f"객체 {i} 처리 중 오류: {e}")
                    continue
            
            return zone_to_track_id
            
        except Exception as e:
            print(f"process_obb_results 오류: {e}")
            return {}
    
def process_video():
    """기존 호환성을 위한 함수"""
    processor = EnhancedVideoProcessor("best.pt")
    processor.process_video_enhanced("angle.mp4")

if __name__ == "__main__":
    # 기본 처리
    process_video()