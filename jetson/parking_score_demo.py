#!/usr/bin/env python3
"""
젯슨 주차 점수 계산 데모
- YOLO로 차량 검출
- 번호판 인식 (시뮬레이션)
- 차량 길이 매핑
- 주차 점수 계산
"""

import cv2
import numpy as np
from ultralytics import YOLO
import time
import math
from collections import defaultdict
from parking_score_calculator import ParkingScoreCalculator

class VehicleLengthDatabase:
    """차량 길이 데이터베이스 (백엔드 연결 전 임시)"""
    
    def __init__(self):
        self.vehicle_db = {
            # 번호판 -> 차량 정보 매핑
            "12가3456": {"brand": "기아", "model": "모닝", "length_mm": 3595},
            "34나5678": {"brand": "현대", "model": "아반떼", "length_mm": 4680},
            "56다7890": {"brand": "기아", "model": "K5", "length_mm": 4980},
            "78라1234": {"brand": "현대", "model": "그랜저", "length_mm": 5180},
            "90마5678": {"brand": "BMW", "model": "520i", "length_mm": 4963},
            "11바9012": {"brand": "현대", "model": "투싼", "length_mm": 4630},
            
            # 기본값들 (차량 타입별)
            "default_small": {"brand": "기본", "model": "소형차", "length_mm": 4200},
            "default_medium": {"brand": "기본", "model": "중형차", "length_mm": 4650},
            "default_large": {"brand": "기본", "model": "대형차", "length_mm": 4900},
        }
    
    def get_vehicle_info(self, license_plate):
        """번호판으로 차량 정보 조회"""
        if license_plate in self.vehicle_db:
            return self.vehicle_db[license_plate]
        
        # 번호판이 없으면 기본값 반환 (중형차)
        return self.vehicle_db["default_medium"]

class ParkingScoreDemo:
    """주차 점수 계산 데모 시스템"""
    
    def __init__(self, model_path="best.pt"):
        """초기화"""
        self.model = YOLO(model_path)
        self.score_calculator = ParkingScoreCalculator()
        self.vehicle_db = VehicleLengthDatabase()
        
        # 추적 관련
        self.track_history = defaultdict(list)
        self.vehicle_scores = {}  # track_id -> 최신 점수 정보
        
        # 감지 임계값
        self.conf_threshold = 0.3
        self.iou_threshold = 0.7
        
        # 주차 구역 정의 (정규화된 좌표)
        self.parking_zones = self.setup_parking_zones()
        
        print("🚗 주차 점수 계산 데모 시스템 초기화 완료")
        print(f"📊 주차 구역 수: {len(self.parking_zones)}")
    
    def setup_parking_zones(self):
        """주차 구역 설정 (실제 CCTV 영상에 맞게 조정)"""
        # 정규화된 좌표로 주차 구역 정의
        zones = {
            "A1": [0.1, 0.3, 0.25, 0.7],    # [x1, y1, x2, y2] (정규화)
            "A2": [0.3, 0.3, 0.45, 0.7],
            "B1": [0.55, 0.3, 0.7, 0.7],
            "B2": [0.75, 0.3, 0.9, 0.7],
            "C1": [0.1, 0.05, 0.25, 0.25],
            "C2": [0.706019, 0.006859, 0.783951, 0.242798],  # 실제 C2 구역
        }
        return zones
    
    def normalize_to_pixel_coords(self, norm_coords, frame_width, frame_height):
        """정규화된 좌표를 픽셀 좌표로 변환"""
        x1, y1, x2, y2 = norm_coords
        return [
            int(x1 * frame_width),
            int(y1 * frame_height),
            int(x2 * frame_width),
            int(y2 * frame_height)
        ]
    
    def get_vehicle_box_from_detection(self, xyxy, angle=0):
        """YOLO 검출 결과를 vehicle_box로 변환"""
        x1, y1, x2, y2 = xyxy
        
        # 중심점과 크기 계산
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        width = x2 - x1
        height = y2 - y1
        
        # 4개 모서리 점 계산 (각도 고려)
        angle_rad = math.radians(angle)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        
        # 반 크기
        half_w = width / 2
        half_h = height / 2
        
        # 회전된 모서리들
        corners = [
            [-half_w, -half_h],  # 좌상단
            [half_w, -half_h],   # 우상단
            [half_w, half_h],    # 우하단
            [-half_w, half_h]    # 좌하단
        ]
        
        # 회전 적용 후 실제 좌표로 변환
        vehicle_box = []
        for corner in corners:
            x = corner[0] * cos_a - corner[1] * sin_a + center_x
            y = corner[0] * sin_a + corner[1] * cos_a + center_y
            vehicle_box.append([x, y])
        
        return np.array(vehicle_box)
    
    def find_parking_zone_for_vehicle(self, vehicle_center, frame_width, frame_height):
        """차량 중심점이 속한 주차 구역 찾기"""
        cx, cy = vehicle_center
        
        for zone_name, norm_coords in self.parking_zones.items():
            x1, y1, x2, y2 = self.normalize_to_pixel_coords(norm_coords, frame_width, frame_height)
            
            if x1 <= cx <= x2 and y1 <= cy <= y2:
                return zone_name, np.array([[x1, y1], [x2, y1], [x2, y2], [x1, y2]])
        
        return None, None
    
    def simulate_license_plate_recognition(self, track_id):
        """번호판 인식 시뮬레이션 (실제로는 OCR 결과 사용)"""
        # 간단한 시뮬레이션: track_id에 따라 다른 번호판 할당
        plates = ["12가3456", "34나5678", "56다7890", "78라1234", "90마5678", "11바9012"]
        return plates[track_id % len(plates)]
    
    def calculate_vehicle_angle(self, xyxy):
        """차량 박스에서 각도 추정 (간단한 방법)"""
        x1, y1, x2, y2 = xyxy
        
        # 박스의 가로세로 비율로 각도 추정 (실제로는 더 정교한 방법 필요)
        width = x2 - x1
        height = y2 - y1
        
        # 가로가 더 길면 수평, 세로가 더 길면 수직으로 가정
        if width > height * 1.5:
            return 0  # 수평
        elif height > width * 1.5:
            return 90  # 수직
        else:
            return 15  # 약간 기울어진 것으로 가정
    
    def process_frame(self, frame):
        """프레임 처리 및 주차 점수 계산"""
        frame_height, frame_width = frame.shape[:2]
        
        # YOLO 검출 실행
        results = self.model.track(
            frame,
            conf=self.conf_threshold,
            iou=self.iou_threshold,
            persist=True,
            tracker="bytetrack.yaml"
        )
        
        if results[0].boxes is not None and results[0].boxes.id is not None:
            # 검출된 객체들 처리
            boxes = results[0].boxes.xyxy.cpu().numpy()
            track_ids = results[0].boxes.id.cpu().numpy().astype(int)
            confidences = results[0].boxes.conf.cpu().numpy()
            classes = results[0].boxes.cls.cpu().numpy().astype(int)
            
            for i, (box, track_id, conf, cls) in enumerate(zip(boxes, track_ids, confidences, classes)):
                # 차량만 처리 (클래스 0이 차량이라고 가정)
                if cls != 0:
                    continue
                
                x1, y1, x2, y2 = box
                center_x = int((x1 + x2) / 2)
                center_y = int((y1 + y2) / 2)
                
                # 번호판 인식 시뮬레이션
                license_plate = self.simulate_license_plate_recognition(track_id)
                
                # 차량 정보 조회
                vehicle_info = self.vehicle_db.get_vehicle_info(license_plate)
                
                # 차량이 주차 구역에 있는지 확인
                zone_name, parking_zone = self.find_parking_zone_for_vehicle(
                    (center_x, center_y), frame_width, frame_height
                )
                
                if zone_name and parking_zone is not None:
                    # 차량 각도 계산
                    vehicle_angle = self.calculate_vehicle_angle(box)
                    
                    # 차량 박스 생성
                    vehicle_box = self.get_vehicle_box_from_detection(box, vehicle_angle)
                    
                    # 주차 점수 계산
                    score_info = self.score_calculator.calculate_parking_score(
                        vehicle_box=vehicle_box,
                        parking_zone=parking_zone,
                        vehicle_length_mm=vehicle_info["length_mm"],
                        vehicle_angle=vehicle_angle
                    )
                    
                    # 결과 저장
                    self.vehicle_scores[track_id] = {
                        'license_plate': license_plate,
                        'vehicle_info': vehicle_info,
                        'zone_name': zone_name,
                        'score_info': score_info,
                        'timestamp': time.time()
                    }
                    
                    # 시각화
                    self.draw_vehicle_with_score(frame, box, track_id, score_info, 
                                                vehicle_info, zone_name, license_plate)
                    
                    # 주차 구역 표시
                    self.draw_parking_zone(frame, parking_zone, zone_name)
                else:
                    # 주차 구역 밖의 차량
                    color = (100, 100, 100)  # 회색
                    cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
                    cv2.putText(frame, f"ID:{track_id} (구역밖)", 
                               (int(x1), int(y1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # 모든 주차 구역 표시
        self.draw_all_parking_zones(frame, frame_width, frame_height)
        
        return frame
    
    def draw_vehicle_with_score(self, frame, box, track_id, score_info, vehicle_info, zone_name, license_plate):
        """차량과 점수 정보를 프레임에 그리기"""
        x1, y1, x2, y2 = box
        total_score = score_info['total_score']
        
        # 점수에 따른 색상 결정
        if total_score >= 80:
            color = (0, 255, 0)    # 초록색 (우수)
        elif total_score >= 70:
            color = (0, 255, 255)  # 노란색 (양호)
        elif total_score >= 60:
            color = (0, 165, 255)  # 주황색 (보통)
        else:
            color = (0, 0, 255)    # 빨간색 (미흡)
        
        # 차량 박스 그리기
        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 3)
        
        # 정보 텍스트 준비
        info_lines = [
            f"ID:{track_id} 구역:{zone_name}",
            f"{license_plate}",
            f"{vehicle_info['brand']} {vehicle_info['model']}",
            f"총점: {total_score}점",
            f"중심:{score_info['center_score']} 각도:{score_info['angle_score']} 길이:{score_info['length_score']}"
        ]
        
        # 텍스트 배경 그리기
        text_y = int(y1) - 10
        for i, line in enumerate(info_lines):
            text_size = cv2.getTextSize(line, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
            cv2.rectangle(frame, (int(x1), text_y - 15 - i*20), 
                         (int(x1) + text_size[0] + 5, text_y - i*20), color, -1)
            cv2.putText(frame, line, (int(x1) + 2, text_y - 5 - i*20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    def draw_parking_zone(self, frame, parking_zone, zone_name):
        """개별 주차 구역 그리기"""
        points = parking_zone.astype(int)
        cv2.polylines(frame, [points], True, (255, 255, 0), 2)  # 청록색
        
        # 구역 이름 표시
        center_x = int(np.mean(points[:, 0]))
        center_y = int(np.mean(points[:, 1]))
        cv2.putText(frame, zone_name, (center_x - 20, center_y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
    
    def draw_all_parking_zones(self, frame, frame_width, frame_height):
        """모든 주차 구역 표시"""
        for zone_name, norm_coords in self.parking_zones.items():
            x1, y1, x2, y2 = self.normalize_to_pixel_coords(norm_coords, frame_width, frame_height)
            zone_points = np.array([[x1, y1], [x2, y1], [x2, y2], [x1, y2]])
            
            # 구역만 그리기 (차량이 없을 때)
            cv2.polylines(frame, [zone_points], True, (150, 150, 150), 1)  # 회색 점선
    
    def print_current_scores(self):
        """현재 주차 점수들을 콘솔에 출력"""
        if not self.vehicle_scores:
            return
        
        print("\n" + "="*80)
        print("🚗 현재 주차 점수 현황")
        print("="*80)
        
        for track_id, data in self.vehicle_scores.items():
            score_info = data['score_info']
            vehicle_info = data['vehicle_info']
            
            print(f"🚙 차량 ID: {track_id}")
            print(f"   번호판: {data['license_plate']}")
            print(f"   차량: {vehicle_info['brand']} {vehicle_info['model']} ({vehicle_info['length_mm']}mm)")
            print(f"   구역: {data['zone_name']}")
            print(f"   📊 점수: {score_info['total_score']}점 (중심:{score_info['center_score']}, 각도:{score_info['angle_score']}, 길이:{score_info['length_score']})")
            
            details = score_info['details']
            print(f"   📍 중심 오프셋: {details['center_offset_px']:.1f}px ({details['center_offset_mm']:.1f}mm)")
            print(f"   📐 각도 편차: {details['angle_offset']:.1f}도")
            print(f"   📏 길이 활용률: {details['length_utilization']:.1f}%")
            print("")

def main():
    """메인 함수"""
    print("🚗 젯슨 주차 점수 계산 데모 시작")
    
    # 데모 시스템 초기화
    demo = ParkingScoreDemo(model_path="best.pt")
    
    # 비디오 파일 또는 카메라 선택
    source = input("비디오 파일 경로 입력 (엔터 시 웹캠 사용): ").strip()
    if not source:
        source = 0  # 웹캠
    
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"❌ 영상 소스를 열 수 없습니다: {source}")
        return
    
    print("✅ 영상 처리 시작 (q키로 종료)")
    
    frame_count = 0
    start_time = time.time()
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("영상 끝 또는 읽기 실패")
            break
        
        # 프레임 처리
        processed_frame = demo.process_frame(frame)
        
        # FPS 계산 및 표시
        frame_count += 1
        elapsed_time = time.time() - start_time
        fps = frame_count / elapsed_time if elapsed_time > 0 else 0
        
        cv2.putText(processed_frame, f"FPS: {fps:.1f}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # 결과 표시
        cv2.imshow("주차 점수 계산 데모", processed_frame)
        
        # 키 입력 처리
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):  # 's'키로 현재 점수 출력
            demo.print_current_scores()
        elif key == ord(' '):  # 스페이스바로 일시정지
            cv2.waitKey(0)
    
    # 최종 점수 출력
    print("\n🏁 최종 주차 점수 결과:")
    demo.print_current_scores()
    
    cap.release()
    cv2.destroyAllWindows()
    print("✅ 프로그램 종료")

if __name__ == "__main__":
    main()
