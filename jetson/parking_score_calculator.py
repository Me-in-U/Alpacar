import cv2
import numpy as np
import math
from typing import Tuple, Optional, Dict, Any

# 차량 길이 매핑 테이블 (모형차 실제 치수 기준)
VEHICLE_LENGTH_MAPPING = {
    # 소형차 - 모형차 소형
    "소형": 105,   # 모형차 소형 길이
    "모닝": 105,
    "morning": 105,
    "compact": 105,
    "small": 105,
    
    # 중형차 - 모형차 중형
    "중형": 118,   # 모형차 중형 길이
    "K5": 118,    # 모형차 중형
    "K8": 118,    # 모형차 중형  
    "midsize": 118,
    "sedan": 118,
    
    # 대형 SUV/승합차 - 모형차 대형
    "대형": 125,   # 모형차 대형 길이
    "카니발": 125,
    "carnival": 125,
    "승합차": 125,
    "large": 125,
    "van": 125,
    "suv": 125,
    
    # 기본값 (중형차 기준)
    "default": 118
}

def get_vehicle_length_by_type(vehicle_type: str) -> int:
    """차량 타입별 길이 반환"""
    return VEHICLE_LENGTH_MAPPING.get(vehicle_type.lower(), VEHICLE_LENGTH_MAPPING["default"])

def get_vehicle_length_by_plate(license_plate: str) -> int:
    """번호판으로 차량 길이 추정 (임시 로직)"""
    
    # 번호판 패턴 분석 (예시)
    if not license_plate or license_plate == "Unknown":
        return VEHICLE_LENGTH_MAPPING["default"]
    
    # 간단한 규칙 기반 분류 (실제로는 더 정교한 로직 필요)
    plate_lower = license_plate.lower()
    
    # 예시: 특정 패턴으로 차량 크기 추정
    if any(x in plate_lower for x in ["suv", "sports"]):
        return VEHICLE_LENGTH_MAPPING["SUV"]
    elif any(x in plate_lower for x in ["compact", "mini"]):
        return VEHICLE_LENGTH_MAPPING["소형"]
    elif any(x in plate_lower for x in ["luxury", "premium"]):
        return VEHICLE_LENGTH_MAPPING["대형"]
    else:
        return VEHICLE_LENGTH_MAPPING["중형"]

# 차종별 임시 데이터베이스 (모형차 기준)
TEMP_VEHICLE_DATABASE = {
    "123가4567": {"type": "소형", "brand": "기아", "model": "모닝", "length": 105},     # 모형차 소형
    "456나7890": {"type": "중형", "brand": "기아", "model": "K5", "length": 118},      # 모형차 중형
    "789다1234": {"type": "중형", "brand": "기아", "model": "K8", "length": 118},      # 모형차 중형
    "321라5678": {"type": "소형", "brand": "현대", "model": "아반떼", "length": 105},    # 모형차 소형
    "654마9012": {"type": "승합차", "brand": "기아", "model": "카니발", "length": 125},  # 모형차 대형
}

def get_vehicle_info_from_temp_db(license_plate: str) -> dict:
    """임시 데이터베이스에서 차량 정보 조회"""
    return TEMP_VEHICLE_DATABASE.get(license_plate, {
        "type": "중형",
        "brand": "Unknown",
        "model": "Unknown", 
        "length": 118  # 모형차 중형 기본값
    })

# 새로 추가: ParkingScoreCalculator 클래스
class ParkingScoreCalculator:
    """차량 길이 기반 주차 점수 계산 클래스"""
    
    def __init__(self):
        # 주차선 길이 (mm) - 모형차 주차장 크기
        self.parking_space_length = 150  # 15cm (모형차 주차장)
        self.parking_space_width = 80    # 8cm (모형차 주차장)
        
        # 점수 가중치
        self.angle_weight = 1.0       # 각도 정렬 비중 (100%)
        
        # 픽셀-실제 거리 변환 비율 (모형차용 - 추정값)
        self.pixel_to_mm_ratio = 0.3  # 1픽셀 = 0.3mm (모형차 스케일)
    
    def calculate_parking_score(
        self, 
        vehicle_box: np.ndarray,  # 차량 박스 좌표
        parking_zone: np.ndarray, # 주차 구역 좌표
        vehicle_length_mm: int,   # 차량 실제 길이(mm)
        vehicle_angle: float      # 차량 회전 각도(degree)
    ) -> Dict[str, Any]:
        """
        주차 점수 계산
        Args:
            vehicle_box: 차량 박스 좌표 [(x1,y1), (x2,y2), (x3,y3), (x4,y4)]
            parking_zone: 주차 구역 좌표 [(x1,y1), (x2,y2), (x3,y3), (x4,y4)]
            vehicle_length_mm: 차량 실제 길이(mm)
            vehicle_angle: 차량 회전 각도(degree)
        Returns:
            dict: 점수 정보
        """
        
        # 1. 각도 정렬 점수 계산 (유일한 평가 기준)
        angle_score = self._calculate_angle_alignment(vehicle_angle, parking_zone)
        
        # 2. 총합 점수 = 각도 점수만 사용
        total_score = angle_score
        
        # 3. 실제 각도 차이 계산 (디스플레이용)
        zone_width_vector = parking_zone[1] - parking_zone[0]
        zone_depth_vector = parking_zone[3] - parking_zone[0]
        zone_depth_angle = math.degrees(math.atan2(zone_depth_vector[1], zone_depth_vector[0]))
        actual_angle_diff = abs(vehicle_angle - zone_depth_angle)
        while actual_angle_diff > 180:
            actual_angle_diff -= 360
        actual_angle_diff = abs(actual_angle_diff)
        if actual_angle_diff > 90:
            actual_angle_diff = 180 - actual_angle_diff
        
        return {
            'total_score': min(100, max(0, int(total_score))),
            'angle_score': int(angle_score),
            'details': {
                'angle_offset': actual_angle_diff,  # 실제 각도 차이
            }
        }
    
    def _calculate_center_alignment(self, vehicle_box: np.ndarray, parking_zone: np.ndarray) -> float:
        """중심점 정렬 점수 계산 (0-100)"""
        vehicle_center = np.mean(vehicle_box, axis=0)
        zone_center = np.mean(parking_zone, axis=0)
        
        # 중심점 간 거리
        center_distance = np.linalg.norm(vehicle_center - zone_center)
        
        # 주차 구역 크기 기준 정규화
        zone_diagonal = np.linalg.norm(parking_zone[2] - parking_zone[0])
        normalized_distance = center_distance / (zone_diagonal * 0.5) if zone_diagonal > 0 else 0
        
        # 점수 계산 (거리가 가까울수록 높은 점수)
        center_score = max(0, 100 - (normalized_distance * 100))
        return center_score
    
    def _calculate_angle_alignment(self, vehicle_angle: float, parking_zone: np.ndarray) -> float:
        """각도 정렬 점수 계산 (0-100) - 수직 주차 기준 (90도 고정)"""
        # 모든 주차 구역이 수직 주차이므로 90도로 고정
        zone_depth_angle = 90.0  # 수직 주차 기준각
        
        # 차량 각도와 수직 주차 각도(90도) 비교
        raw_diff = abs(vehicle_angle - zone_depth_angle)
        angle_diff = raw_diff
        
        # 180도 범위에서 가장 작은 각도 차이 구하기
        while angle_diff > 180:
            angle_diff -= 360
        angle_diff = abs(angle_diff)
        if angle_diff > 90:
            angle_diff = 180 - angle_diff
        
        # 특수 경우: 90도 근처 차이는 수직 주차로 간주 (YOLO 인식 오류 보정)
        # 87~93도 차이는 실제로는 수직 주차일 가능성이 높음 (범위 축소)
        if 87 <= angle_diff <= 93:
            print(f"DEBUG: YOLO 인식 오류 감지 (각도차이:{angle_diff:.1f}도) - 수직주차로 보정")
            angle_diff = 0  # 완벽한 수직 주차로 보정
        # 특수 경우: 90도 근처 차이는 수직 주차로 간주 (YOLO 인식 오류 보정)
        # 87~93도 차이는 실제로는 수직 주차일 가능성이 높음
        if 87 <= angle_diff <= 93:
            print(f"DEBUG: YOLO 인식 오류 감지 (각도차이:{angle_diff:.1f}도) - 수직주차로 보정")
            angle_diff = 0  # 완벽한 수직 주차로 보정
        # 73~77도 차이는 부분적 보정 (실제 10~15도 정도의 기울기로 처리)
        elif 73 <= angle_diff <= 77:
            print(f"DEBUG: YOLO 180도 회전 오류 감지 (각도차이:{angle_diff:.1f}도) - 적정 보정")
            angle_diff = (angle_diff - 60)  # 60도를 빼서 13~17도 실제 각도로 처리
        
        # DEBUG: 각도 계산 과정 출력
        print(f"DEBUG: vehicle_angle={vehicle_angle:.1f}, zone_depth_angle={zone_depth_angle:.1f}, raw_diff={raw_diff:.1f}, final_angle_diff={angle_diff:.1f}")
        
        # 개선된 세분화 점수 계산 - 더 부드러운 곡선
        if angle_diff <= 2:
            angle_score = 100 - (angle_diff * 2)  # 0-2도: 100-96점
        elif angle_diff <= 5:
            angle_score = 96 - ((angle_diff - 2) * 3)  # 2-5도: 96-87점
        elif angle_diff <= 10:
            angle_score = 87 - ((angle_diff - 5) * 2.5)  # 5-10도: 87-74점
        elif angle_diff <= 15:
            angle_score = 74 - ((angle_diff - 10) * 2)  # 10-15도: 74-64점
        elif angle_diff <= 20:
            angle_score = 64 - ((angle_diff - 15) * 2)  # 15-20도: 64-54점
        elif angle_diff <= 25:
            angle_score = 54 - ((angle_diff - 20) * 2)  # 20-25도: 54-44점
        elif angle_diff <= 30:
            angle_score = 44 - ((angle_diff - 25) * 2)  # 25-30도: 44-34점
        elif angle_diff <= 40:
            angle_score = 34 - ((angle_diff - 30) * 1.5)  # 30-40도: 34-19점
        elif angle_diff <= 50:
            angle_score = 19 - ((angle_diff - 40) * 1)  # 40-50도: 19-9점
        elif angle_diff <= 60:
            angle_score = 9 - ((angle_diff - 50) * 0.5)  # 50-60도: 9-4점
        else:
            angle_score = max(0, 4 - ((angle_diff - 60) * 0.2))  # 60도 이상: 4점 이하
        
        print(f"DEBUG: final_score={angle_score:.1f}")
        
        return angle_score
    
    def _calculate_length_fitness(self, vehicle_box: np.ndarray, parking_zone: np.ndarray, vehicle_length_mm: int) -> float:
        """길이 적합성 점수 계산 (0-100)"""
        # 차량 박스의 실제 길이 계산 (픽셀)
        vehicle_length_px = max(
            np.linalg.norm(vehicle_box[1] - vehicle_box[0]),
            np.linalg.norm(vehicle_box[3] - vehicle_box[2])
        )
        
        # 주차 구역 길이 계산 (픽셀)
        zone_length_px = max(
            np.linalg.norm(parking_zone[1] - parking_zone[0]),
            np.linalg.norm(parking_zone[3] - parking_zone[2])
        )
        
        if vehicle_length_px == 0 or zone_length_px == 0:
            return 50  # 기본 점수
        
        # 픽셀-실제 길이 비율 계산
        px_to_mm_ratio = vehicle_length_mm / vehicle_length_px
        zone_length_mm = zone_length_px * px_to_mm_ratio
        
        # 길이 활용률 계산
        length_utilization = vehicle_length_mm / zone_length_mm if zone_length_mm > 0 else 0
        
        # 최적 활용률 0.7-0.9 범위에서 최고점
        if 0.7 <= length_utilization <= 0.9:
            length_score = 100
        elif length_utilization < 0.7:
            # 너무 작은 차량
            length_score = max(50, length_utilization * 100 / 0.7)
        else:
            # 너무 큰 차량
            excess = length_utilization - 0.9
            length_score = max(0, 100 - (excess * 200))
        
        return length_score
    
    def _get_center_offset(self, vehicle_box: np.ndarray, parking_zone: np.ndarray) -> float:
        """중심점 오프셋 거리 반환 (픽셀)"""
        vehicle_center = np.mean(vehicle_box, axis=0)
        zone_center = np.mean(parking_zone, axis=0)
        return np.linalg.norm(vehicle_center - zone_center)
    
    def _get_length_utilization(self, vehicle_box: np.ndarray, parking_zone: np.ndarray, vehicle_length_mm: int) -> float:
        """길이 활용률 반환 (0.0-1.0)"""
        vehicle_length_px = max(
            np.linalg.norm(vehicle_box[1] - vehicle_box[0]),
            np.linalg.norm(vehicle_box[3] - vehicle_box[2])
        )
        zone_length_px = max(
            np.linalg.norm(parking_zone[1] - parking_zone[0]),
            np.linalg.norm(parking_zone[3] - parking_zone[2])
        )
        
        if vehicle_length_px == 0 or zone_length_px == 0:
            return 0.5  # 기본값
        
        px_to_mm_ratio = vehicle_length_mm / vehicle_length_px
        zone_length_mm = zone_length_px * px_to_mm_ratio
        
        return vehicle_length_mm / zone_length_mm if zone_length_mm > 0 else 0

# 테스트용 함수
def print_temp_database():
    """임시 데이터베이스 내용 출력"""
    print("=== 임시 차량 데이터베이스 ===")
    for plate, info in TEMP_VEHICLE_DATABASE.items():
        print(f"{plate}: {info['brand']} {info['model']} ({info['type']}, {info['length']}mm)")

if __name__ == "__main__":
    print_temp_database()