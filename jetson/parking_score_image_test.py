#!/usr/bin/env python3
"""
젯슨 주차 점수 계산 이미지 테스트
- 정적 이미지에서 차량 검출
- 차량 길이 매핑  
- 주차 점수 계산
"""

import cv2
import numpy as np
from ultralytics import YOLO
import math
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
    
    def get_vehicle_info(self, vehicle_index):
        """차량 인덱스로 차량 정보 조회 (시뮬레이션)"""
        plates = ["12가3456", "34나5678", "56다7890", "78라1234", "90마5678", "11바9012"]
        license_plate = plates[vehicle_index % len(plates)]
        
        if license_plate in self.vehicle_db:
            return license_plate, self.vehicle_db[license_plate]
        
        # 번호판이 없으면 기본값 반환 (중형차)
        return license_plate, self.vehicle_db["default_medium"]

class ParkingScoreImageTest:
    """주차 점수 계산 이미지 테스트"""
    
    def __init__(self, model_path="best.pt"):
        """초기화"""
        self.model = YOLO(model_path)
        self.score_calculator = ParkingScoreCalculator()
        self.vehicle_db = VehicleLengthDatabase()
        
        # 감지 임계값
        self.conf_threshold = 0.1  # 낮춰서 더 많은 객체 검출
        
        # 주차 구역 정의 (정규화된 좌표)
        self.parking_zones = self.setup_parking_zones()
        
        print("🚗 주차 점수 계산 이미지 테스트 초기화 완료")
        print(f"📊 주차 구역 수: {len(self.parking_zones)}")
    
    def setup_parking_zones(self):
        """주차 구역 설정"""
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
    
    def calculate_vehicle_angle(self, xyxy):
        """차량 박스에서 각도 추정"""
        x1, y1, x2, y2 = xyxy
        
        # 박스의 가로세로 비율로 각도 추정
        width = x2 - x1
        height = y2 - y1
        
        # 간단한 각도 추정 (실제로는 더 정교한 방법 필요)
        if width > height * 1.5:
            return 0  # 수평
        elif height > width * 1.5:
            return 90  # 수직
        else:
            return 5  # 약간 기울어진 것으로 가정
    
    def process_image(self, image_path):
        """이미지 처리 및 주차 점수 계산"""
        print(f"\n🔍 이미지 처리 시작: {image_path}")
        
        frame = cv2.imread(image_path)
        if frame is None:
            print(f"❌ 이미지를 읽을 수 없습니다: {image_path}")
            return None
        
        frame_height, frame_width = frame.shape[:2]
        print(f"📐 이미지 크기: {frame_width}x{frame_height}")
        
        # YOLO 검출 실행
        results = self.model(frame, conf=self.conf_threshold)
        
        if results[0].boxes is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()
            confidences = results[0].boxes.conf.cpu().numpy()
            classes = results[0].boxes.cls.cpu().numpy().astype(int)
            
            print(f"🚗 검출된 객체 수: {len(boxes)}")
            
            vehicle_results = []
            
            for i, (box, conf, cls) in enumerate(zip(boxes, confidences, classes)):
                # 차량만 처리 (클래스 0이 차량이라고 가정)
                if cls != 0:
                    continue
                
                x1, y1, x2, y2 = box
                center_x = int((x1 + x2) / 2)
                center_y = int((y1 + y2) / 2)
                
                print(f"\n🚙 차량 {i+1}: 중심점 ({center_x}, {center_y}), 신뢰도: {conf:.3f}")
                
                # 번호판 및 차량 정보 시뮬레이션
                license_plate, vehicle_info = self.vehicle_db.get_vehicle_info(i)
                
                # 차량이 주차 구역에 있는지 확인
                zone_name, parking_zone = self.find_parking_zone_for_vehicle(
                    (center_x, center_y), frame_width, frame_height
                )
                
                if zone_name and parking_zone is not None:
                    print(f"   📍 주차 구역: {zone_name}")
                    print(f"   🚘 번호판: {license_plate}")
                    print(f"   🏭 차량: {vehicle_info['brand']} {vehicle_info['model']} ({vehicle_info['length_mm']}mm)")
                    
                    # 차량 각도 계산
                    vehicle_angle = self.calculate_vehicle_angle(box)
                    print(f"   📐 추정 각도: {vehicle_angle}도")
                    
                    # 차량 박스 생성
                    vehicle_box = self.get_vehicle_box_from_detection(box, vehicle_angle)
                    
                    # 주차 점수 계산
                    score_info = self.score_calculator.calculate_parking_score(
                        vehicle_box=vehicle_box,
                        parking_zone=parking_zone,
                        vehicle_length_mm=vehicle_info["length_mm"],
                        vehicle_angle=vehicle_angle
                    )
                    
                    print(f"   📊 === 주차 점수 결과 ===")
                    print(f"   🏆 총점: {score_info['total_score']}점")
                    print(f"   📍 중심 정렬: {score_info['center_score']}점")
                    print(f"   📐 각도 정렬: {score_info['angle_score']}점")
                    print(f"   📏 길이 적합성: {score_info['length_score']}점")
                    
                    details = score_info['details']
                    print(f"   📏 중심 오프셋: {details['center_offset_px']:.1f}px ({details['center_offset_mm']:.1f}mm)")
                    print(f"   📐 각도 편차: {details['angle_offset']:.1f}도")
                    print(f"   📊 길이 활용률: {details['length_utilization']:.1f}%")
                    
                    # 등급 판정
                    total_score = score_info['total_score']
                    if total_score >= 80:
                        grade = "EXCELLENT (우수)"
                        grade_color = (0, 255, 0)  # 초록
                    elif total_score >= 70:
                        grade = "GOOD (양호)" 
                        grade_color = (0, 255, 255)  # 노랑
                    elif total_score >= 60:
                        grade = "FAIR (보통)"
                        grade_color = (0, 165, 255)  # 주황
                    else:
                        grade = "POOR (미흡)"
                        grade_color = (0, 0, 255)  # 빨강
                    
                    print(f"   🏅 등급: {grade}")
                    
                    # 시각화를 위한 결과 저장
                    vehicle_results.append({
                        'box': box,
                        'center': (center_x, center_y),
                        'license_plate': license_plate,
                        'vehicle_info': vehicle_info,
                        'zone_name': zone_name,
                        'parking_zone': parking_zone,
                        'score_info': score_info,
                        'grade': grade,
                        'color': grade_color
                    })
                    
                else:
                    print(f"   ⚠️  주차 구역 밖에 위치")
                    # 구역 밖 차량도 시각화에 포함
                    vehicle_results.append({
                        'box': box,
                        'center': (center_x, center_y),
                        'license_plate': license_plate,
                        'vehicle_info': vehicle_info,
                        'zone_name': "구역밖",
                        'parking_zone': None,
                        'score_info': None,
                        'grade': "구역밖",
                        'color': (100, 100, 100)  # 회색
                    })
            
            # 결과 이미지 생성
            result_frame = self.draw_results(frame.copy(), vehicle_results, frame_width, frame_height)
            
            # 결과 이미지 저장
            result_path = image_path.replace('.', '_parking_score.')
            cv2.imwrite(result_path, result_frame)
            print(f"\n💾 결과 이미지 저장: {result_path}")
            
            return result_frame, vehicle_results
        
        else:
            print("❌ 검출된 차량이 없습니다")
            return frame, []
    
    def draw_results(self, frame, vehicle_results, frame_width, frame_height):
        """결과를 프레임에 그리기"""
        # 모든 주차 구역 표시
        for zone_name, norm_coords in self.parking_zones.items():
            x1, y1, x2, y2 = self.normalize_to_pixel_coords(norm_coords, frame_width, frame_height)
            zone_points = np.array([[x1, y1], [x2, y1], [x2, y2], [x1, y2]])
            
            cv2.polylines(frame, [zone_points], True, (150, 150, 150), 2)
            cv2.putText(frame, zone_name, (x1 + 5, y1 + 25), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
        
        # 차량별 결과 그리기
        for i, result in enumerate(vehicle_results):
            box = result['box']
            color = result['color']
            x1, y1, x2, y2 = box
            
            # 차량 박스 그리기
            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 3)
            
            # 정보 텍스트
            if result['score_info']:
                info_lines = [
                    f"차량 {i+1}: {result['zone_name']}",
                    f"{result['license_plate']}",
                    f"{result['vehicle_info']['brand']} {result['vehicle_info']['model']}",
                    f"점수: {result['score_info']['total_score']}점",
                    f"등급: {result['grade']}"
                ]
            else:
                info_lines = [
                    f"차량 {i+1}: {result['zone_name']}",
                    f"{result['license_plate']}",
                    f"{result['vehicle_info']['brand']} {result['vehicle_info']['model']}"
                ]
            
            # 텍스트 배경 및 내용
            text_y = int(y1) - 10
            for j, line in enumerate(info_lines):
                text_size = cv2.getTextSize(line, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                cv2.rectangle(frame, (int(x1), text_y - 25 - j*25), 
                             (int(x1) + text_size[0] + 10, text_y - j*25), color, -1)
                cv2.putText(frame, line, (int(x1) + 5, text_y - 5 - j*25), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return frame

def main():
    """메인 함수"""
    print("🚗 젯슨 주차 점수 계산 이미지 테스트")
    
    # 테스트 시스템 초기화
    tester = ParkingScoreImageTest(model_path="best.pt")
    
    # 테스트할 이미지들
    test_images = [
        "car.jpg",
        "car_analysis_result.jpg",
        "morning_parking_test.jpg"  # 이전에 생성된 테스트 이미지
    ]
    
    for image_path in test_images:
        try:
            result_frame, vehicle_results = tester.process_image(image_path)
            
            if result_frame is not None:
                # 결과 표시 대신 저장만 함 (OpenCV GUI 문제 해결)
                print(f"✅ {image_path} 처리 완료 - 결과 이미지 저장됨")
            
        except Exception as e:
            print(f"❌ {image_path} 처리 중 오류: {e}")
    
    print("🏁 모든 이미지 테스트 완료")

if __name__ == "__main__":
    main()
