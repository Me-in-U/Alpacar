#!/usr/bin/env python3
"""
차량별 이상적 모형 생성 및 비교 시스템
각 차량의 길이에 맞는 완벽한 주차 템플릿을 생성하고 실제 차량과 비교
"""

import cv2
import numpy as np
import math
from typing import Tuple, Dict, Any

class VehicleTemplateMatcher:
    """차량별 이상적 모형 생성 및 비교 클래스"""
    
    def __init__(self):
        # 모형차 기본 정보
        self.vehicle_specs = {
            "모닝": {"length_mm": 105, "width_mm": 50, "type": "소형차"},
            "K5": {"length_mm": 118, "width_mm": 50, "type": "중형차"},
            "K8": {"length_mm": 118, "width_mm": 50, "type": "중형차"},
            "카니발": {"length_mm": 125, "width_mm": 50, "type": "승합차"},
        }
        
        # 픽셀-실제 거리 변환 비율 (추정값)
        self.pixel_to_mm_ratio = 0.3  # 1픽셀 = 0.3mm
    
    def generate_ideal_vehicle_template(
        self, 
        vehicle_model: str, 
        parking_zone: np.ndarray, 
        target_angle: float = 90.0
    ) -> np.ndarray:
        """
        차량 모델에 맞는 이상적인 주차 템플릿 생성
        
        Args:
            vehicle_model: 차량 모델명 (모닝, K5, K8, 카니발)
            parking_zone: 주차 구역 좌표 [(x1,y1), (x2,y2), (x3,y3), (x4,y4)]
            target_angle: 목표 각도 (기본: 90도 수직주차)
            
        Returns:
            ideal_template: 이상적인 차량 박스 좌표
        """
        
        # 1. 차량 사양 가져오기
        if vehicle_model not in self.vehicle_specs:
            vehicle_model = "K5"  # 기본값
        
        vehicle_length_mm = self.vehicle_specs[vehicle_model]["length_mm"]
        vehicle_width_mm = self.vehicle_specs[vehicle_model]["width_mm"]
        
        # 2. 픽셀 단위 차량 크기 계산
        vehicle_length_px = vehicle_length_mm / self.pixel_to_mm_ratio
        vehicle_width_px = vehicle_width_mm / self.pixel_to_mm_ratio
        
        # 3. 주차 구역 중심점 계산
        zone_center_x = np.mean(parking_zone[:, 0])
        zone_center_y = np.mean(parking_zone[:, 1])
        
        # 4. 목표 각도로 이상적인 차량 박스 생성
        angle_rad = math.radians(target_angle)
        
        # 차량의 네 모서리 계산 (중심점 기준)
        half_length = vehicle_length_px / 2
        half_width = vehicle_width_px / 2
        
        # 회전 변환 적용
        cos_angle = math.cos(angle_rad)
        sin_angle = math.sin(angle_rad)
        
        # 차량 박스의 네 점 (시계방향)
        corners = [
            (-half_length, -half_width),  # 좌상
            (half_length, -half_width),   # 우상
            (half_length, half_width),    # 우하
            (-half_length, half_width)    # 좌하
        ]
        
        # 회전 및 이동 변환 적용
        ideal_template = []
        for dx, dy in corners:
            # 회전 변환
            rotated_x = dx * cos_angle - dy * sin_angle
            rotated_y = dx * sin_angle + dy * cos_angle
            
            # 주차 구역 중심으로 이동
            final_x = zone_center_x + rotated_x
            final_y = zone_center_y + rotated_y
            
            ideal_template.append([final_x, final_y])
        
        return np.array(ideal_template)
    
    def calculate_template_similarity(
        self, 
        actual_vehicle: np.ndarray, 
        ideal_template: np.ndarray
    ) -> Dict[str, float]:
        """
        실제 차량과 이상적 템플릿 간의 유사도 계산
        
        Args:
            actual_vehicle: 실제 검출된 차량 박스
            ideal_template: 이상적인 차량 템플릿
            
        Returns:
            similarity_scores: 각종 유사도 점수
        """
        
        # 1. 위치 유사도 (중심점 거리)
        actual_center = np.mean(actual_vehicle, axis=0)
        ideal_center = np.mean(ideal_template, axis=0)
        center_distance = np.linalg.norm(actual_center - ideal_center)
        
        # 주차 구역 크기 대비 정규화
        zone_diagonal = np.linalg.norm(ideal_template[2] - ideal_template[0])
        normalized_center_distance = center_distance / (zone_diagonal * 0.5) if zone_diagonal > 0 else 0
        position_score = max(0, 100 - (normalized_center_distance * 100))
        
        # 2. 크기 유사도
        actual_area = cv2.contourArea(actual_vehicle.astype(np.int32))
        ideal_area = cv2.contourArea(ideal_template.astype(np.int32))
        
        if ideal_area > 0:
            size_ratio = min(actual_area, ideal_area) / max(actual_area, ideal_area)
            size_score = size_ratio * 100
        else:
            size_score = 0
        
        # 3. 각도 유사도
        angle_score = self._calculate_angle_similarity(actual_vehicle, ideal_template)
        
        # 4. 형태 유사도 (Intersection over Union)
        iou_score = self._calculate_iou_similarity(actual_vehicle, ideal_template)
        
        # 5. 종합 점수 (가중 평균)
        total_score = (
            angle_score * 0.4 +      # 각도 40%
            position_score * 0.25 +  # 위치 25%
            size_score * 0.2 +       # 크기 20%
            iou_score * 0.15         # 형태 15%
        )
        
        return {
            'total_score': min(100, max(0, total_score)),
            'position_score': position_score,
            'size_score': size_score,
            'angle_score': angle_score,
            'iou_score': iou_score,
            'center_distance_px': center_distance,
            'size_ratio': size_ratio if 'size_ratio' in locals() else 0
        }
    
    def _calculate_angle_similarity(self, actual_vehicle: np.ndarray, ideal_template: np.ndarray) -> float:
        """각도 유사도 계산"""
        
        # 실제 차량의 각도 계산
        actual_vec = actual_vehicle[1] - actual_vehicle[0]
        actual_angle = math.degrees(math.atan2(actual_vec[1], actual_vec[0]))
        
        # 이상적 템플릿의 각도 계산
        ideal_vec = ideal_template[1] - ideal_template[0]
        ideal_angle = math.degrees(math.atan2(ideal_vec[1], ideal_vec[0]))
        
        # 각도 차이 계산
        angle_diff = abs(actual_angle - ideal_angle)
        while angle_diff > 180:
            angle_diff -= 360
        angle_diff = abs(angle_diff)
        if angle_diff > 90:
            angle_diff = 180 - angle_diff
        
        # 각도 점수 계산 (차이가 작을수록 높은 점수)
        if angle_diff <= 2:
            return 100 - (angle_diff * 2)
        elif angle_diff <= 5:
            return 96 - ((angle_diff - 2) * 4)
        elif angle_diff <= 10:
            return 88 - ((angle_diff - 5) * 6)
        elif angle_diff <= 20:
            return 58 - ((angle_diff - 10) * 3)
        else:
            return max(0, 28 - ((angle_diff - 20) * 1.4))
    
    def _calculate_iou_similarity(self, actual_vehicle: np.ndarray, ideal_template: np.ndarray) -> float:
        """IoU (Intersection over Union) 유사도 계산"""
        try:
            # 다각형을 이미지로 변환하여 IoU 계산
            # 임시 이미지 생성 (충분한 크기)
            img_size = 2000
            actual_img = np.zeros((img_size, img_size), dtype=np.uint8)
            ideal_img = np.zeros((img_size, img_size), dtype=np.uint8)
            
            # 좌표를 이미지 범위에 맞게 조정
            offset = 500
            actual_shifted = actual_vehicle.astype(np.int32) + offset
            ideal_shifted = ideal_template.astype(np.int32) + offset
            
            # 다각형 채우기
            cv2.fillPoly(actual_img, [actual_shifted], 255)
            cv2.fillPoly(ideal_img, [ideal_shifted], 255)
            
            # IoU 계산
            intersection = cv2.bitwise_and(actual_img, ideal_img)
            union = cv2.bitwise_or(actual_img, ideal_img)
            
            intersection_area = np.sum(intersection > 0)
            union_area = np.sum(union > 0)
            
            if union_area > 0:
                iou = intersection_area / union_area
                return iou * 100
            else:
                return 0
                
        except Exception as e:
            print(f"IoU 계산 오류: {e}")
            return 0
    
    def get_comprehensive_parking_score(
        self, 
        actual_vehicle: np.ndarray,
        parking_zone: np.ndarray,
        vehicle_model: str,
        target_angle: float = 90.0
    ) -> Dict[str, Any]:
        """
        종합적인 주차 점수 계산 (템플릿 매칭 기반)
        
        Args:
            actual_vehicle: 실제 검출된 차량 박스
            parking_zone: 주차 구역 좌표
            vehicle_model: 차량 모델명
            target_angle: 목표 각도
            
        Returns:
            comprehensive_score: 종합 점수 정보
        """
        
        # 1. 이상적인 템플릿 생성
        ideal_template = self.generate_ideal_vehicle_template(
            vehicle_model, parking_zone, target_angle
        )
        
        # 2. 유사도 계산
        similarity_scores = self.calculate_template_similarity(
            actual_vehicle, ideal_template
        )
        
        # 3. 결과 구성
        result = {
            'total_score': int(similarity_scores['total_score']),
            'position_score': int(similarity_scores['position_score']),
            'size_score': int(similarity_scores['size_score']),
            'angle_score': int(similarity_scores['angle_score']),
            'iou_score': int(similarity_scores['iou_score']),
            'vehicle_model': vehicle_model,
            'vehicle_specs': self.vehicle_specs[vehicle_model],
            'ideal_template': ideal_template.tolist(),
            'details': {
                'center_distance_px': similarity_scores['center_distance_px'],
                'size_ratio': similarity_scores['size_ratio'],
                'target_angle': target_angle
            }
        }
        
        return result

# 테스트 함수
def test_template_matching():
    """템플릿 매칭 테스트"""
    matcher = VehicleTemplateMatcher()
    
    # 테스트용 주차 구역 (사각형)
    parking_zone = np.array([
        [100, 100],  # 좌상
        [200, 100],  # 우상
        [200, 200],  # 우하
        [100, 200]   # 좌하
    ])
    
    # 테스트용 실제 차량 (약간 틀어진 상태)
    actual_vehicle = np.array([
        [105, 110],  # 좌상 (약간 틀어짐)
        [195, 105],  # 우상
        [205, 195],  # 우하
        [110, 200]   # 좌하
    ])
    
    # 각 차량 모델별 테스트
    for vehicle_model in ["모닝", "K5", "K8", "카니발"]:
        print(f"\n=== {vehicle_model} 테스트 ===")
        
        # 종합 점수 계산
        result = matcher.get_comprehensive_parking_score(
            actual_vehicle, parking_zone, vehicle_model
        )
        
        print(f"총점: {result['total_score']}점")
        print(f"  위치: {result['position_score']}점")
        print(f"  크기: {result['size_score']}점") 
        print(f"  각도: {result['angle_score']}점")
        print(f"  형태: {result['iou_score']}점")
        print(f"차량 길이: {result['vehicle_specs']['length_mm']}mm")

if __name__ == "__main__":
    test_template_matching()
