#!/usr/bin/env python3
"""
템플릿 매칭 기반 주차 점수 계산 시스템
- 각 차량 길이별 이상적인 주차 모형(템플릿) 생성
- 실제 검출된 차량과 이상적 모형 비교
- 각도, 위치, 크기 종합 평가
"""

import cv2
from ultralytics import YOLO
import os
import numpy as np
import math
from collections import defaultdict

# 주차 구역 정의 (정규화된 좌표) - parking_zones (2).json에서 변환
PARKING_ZONES_NORM = [
    # A구역 (상단)
    {"id": "a1", "rect": [0.540669, 0.008364, 0.634211, 0.268172]},  # A1: (903,8) to (1060,288)
    {"id": "a2", "rect": [0.450479, 0.002793, 0.536660, 0.261452]},  # A2: (753,3) to (897,281)
    {"id": "a3", "rect": [0.354904, 0.009311, 0.444976, 0.258659]},  # A3: (593,10) to (744,278)
    {"id": "a4", "rect": [0.232057, 0.013016, 0.319378, 0.262266]},  # A4: (388,14) to (534,281)
    {"id": "a5", "rect": [0.141746, 0.010242, 0.229186, 0.262639]},  # A5: (237,11) to (383,276)
    
    # B구역 (하단)
    {"id": "b1", "rect": [0.537859, 0.746088, 0.623444, 0.989572]},  # B1: (899,801) to (1043,1063)
    {"id": "b2", "rect": [0.447607, 0.740037, 0.529904, 0.989572]},  # B2: (748,795) to (886,1063)
    {"id": "b3", "rect": [0.361244, 0.740037, 0.444976, 0.985475]},  # B3: (604,795) to (744,1060)
    
    # C구역 (하단)
    {"id": "c1", "rect": [0.241028, 0.768544, 0.327751, 0.986102]},  # C1: (403,825) to (548,1060)
    {"id": "c2", "rect": [0.157416, 0.770688, 0.241028, 0.987383]},  # C2: (263,826) to (403,1060)
    {"id": "c3", "rect": [0.071770, 0.772832, 0.155502, 0.991480]}   # C3: (120,830) to (260,1065)
]

class VehicleTemplateDatabase:
    """차량별 템플릿 데이터베이스"""
    
    def __init__(self):
        # 차량 타입별 실제 치수 (mm)
        self.vehicle_specs = {
            "Morning": {"length_mm": 105, "width_mm": 50, "type": "소형차"},
            "K5": {"length_mm": 118, "width_mm": 50, "type": "중형차"},
            "K8": {"length_mm": 118, "width_mm": 50, "type": "중형차"},
            "Carnival": {"length_mm": 125, "width_mm": 50, "type": "승합차"},
        }
        
        # 구역별 차량 할당
        self.zone_vehicle_mapping = {
            'a': "Carnival",   # A구역: Carnival
            'b': ["K5", "K8"],  # B구역: K5, K8 순환
            'c': "Morning"      # C구역: Morning
        }
        
        # Track ID별 차량 할당 캐시
        self.track_assignments = {}
    
    def get_vehicle_for_zone(self, track_id, zone_id):
        """구역과 Track ID를 기반으로 차량 모델 할당"""
        if track_id in self.track_assignments:
            return self.track_assignments[track_id]
        
        zone_prefix = zone_id[0].lower()
        
        if zone_prefix == 'a':
            vehicle_model = "Carnival"
        elif zone_prefix == 'b':
            # B구역은 K5, K8 순환
            vehicles = self.zone_vehicle_mapping['b']
            vehicle_model = vehicles[track_id % len(vehicles)]
        elif zone_prefix == 'c':
            vehicle_model = "Morning"
        else:
            vehicle_model = "K5"  # 기본값
        
        self.track_assignments[track_id] = vehicle_model
        return vehicle_model
    
    def get_vehicle_specs(self, vehicle_model):
        """차량 사양 정보 반환"""
        return self.vehicle_specs.get(vehicle_model, self.vehicle_specs["K5"])

class IdealParkingTemplate:
    """이상적인 주차 템플릿 생성기"""
    
    def __init__(self, frame_width=1920, frame_height=1088):
        self.frame_width = frame_width
        self.frame_height = frame_height
        
        # 픽셀-실제거리 변환 비율 (실험적으로 조정 필요)
        self.mm_per_pixel = 0.5  # 1픽셀 = 0.5mm (조정 가능)
    
    def create_ideal_template(self, zone_poly, vehicle_length_mm, vehicle_width_mm):
        """
        주차 구역에 대한 이상적인 차량 템플릿 생성
        
        Args:
            zone_poly: 주차 구역 다각형 좌표
            vehicle_length_mm: 차량 길이 (mm)
            vehicle_width_mm: 차량 폭 (mm)
            
        Returns:
            dict: 이상적인 템플릿 정보
        """
        # 구역의 중심점과 방향 계산
        zone_center = np.mean(zone_poly, axis=0)
        zone_bbox = cv2.boundingRect(zone_poly)
        zone_width = zone_bbox[2]
        zone_height = zone_bbox[3]
        
        # 구역의 실제 방향 벡터 계산 (더 정확한 방법)
        # 첫 번째와 두 번째 점을 연결한 벡터 (가로 방향)
        horizontal_vec = zone_poly[1] - zone_poly[0]
        horizontal_angle = math.degrees(math.atan2(horizontal_vec[1], horizontal_vec[0]))
        
        # 첫 번째와 네 번째 점을 연결한 벡터 (세로 방향)
        vertical_vec = zone_poly[3] - zone_poly[0]
        vertical_angle = math.degrees(math.atan2(vertical_vec[1], vertical_vec[0]))
        
        # 가로와 세로 중 어느 것이 더 긴지 확인
        horizontal_length = np.linalg.norm(horizontal_vec)
        vertical_length = np.linalg.norm(vertical_vec)
        
        if horizontal_length > vertical_length:
            # 가로가 더 긴 경우 - 차량이 가로 방향으로 주차
            ideal_angle = horizontal_angle
            template_length = min(vehicle_length_mm / self.mm_per_pixel, horizontal_length * 0.9)
            template_width = min(vehicle_width_mm / self.mm_per_pixel, vertical_length * 0.9)
        else:
            # 세로가 더 긴 경우 - 차량이 세로 방향으로 주차
            ideal_angle = vertical_angle
            template_length = min(vehicle_length_mm / self.mm_per_pixel, vertical_length * 0.9)
            template_width = min(vehicle_width_mm / self.mm_per_pixel, horizontal_length * 0.9)
        
        # 각도 정규화 (0-180도 범위)
        ideal_angle = abs(ideal_angle) % 180
        if ideal_angle > 90:
            ideal_angle = 180 - ideal_angle
        
        # 이상적인 템플릿 박스 생성 (각도 적용)
        half_length = template_length / 2
        half_width = template_width / 2
        
        # 회전 변환 적용
        angle_rad = math.radians(ideal_angle)
        cos_angle = math.cos(angle_rad)
        sin_angle = math.sin(angle_rad)
        
        # 템플릿 박스의 네 점 (중심점 기준)
        corners = [
            (-half_length, -half_width),  # 좌상
            (half_length, -half_width),   # 우상
            (half_length, half_width),    # 우하
            (-half_length, half_width)    # 좌하
        ]
        
        template_box = []
        for dx, dy in corners:
            # 회전 변환 적용
            rotated_x = dx * cos_angle - dy * sin_angle
            rotated_y = dx * sin_angle + dy * cos_angle
            
            # 중심점으로 이동
            final_x = zone_center[0] + rotated_x
            final_y = zone_center[1] + rotated_y
            
            template_box.append([final_x, final_y])
        
        template_box = np.array(template_box)
        
        return {
            'center': zone_center,
            'angle': ideal_angle,
            'box': template_box,
            'length_pixels': template_length,
            'width_pixels': template_width,
            'zone_poly': zone_poly,
            'zone_direction': 'horizontal' if horizontal_length > vertical_length else 'vertical'
        }

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
                print(f"🚨 차선 침범 감점! 각도: {angle_diff:.1f}도, 감점: -{penalty:.1f}점")
        
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
            print(f"⚠️ 차선 침범 검사 오류: {e}")
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

class TemplateMatchingParkingSystem:
    """템플릿 매칭 기반 주차 점수 시스템"""
    
    def __init__(self, model_path="best.pt"):
        self.model = YOLO(model_path)
        self.vehicle_db = VehicleTemplateDatabase()
        self.scorer = TemplateMatchingScorer()
        
        # 비디오 설정
        self.rsize = (1672, 1074)  # new.mp4의 해상도에 맞게 조정
        self.conf_threshold = 0.1
        self.iou_threshold = 0.4
        
        # 주차 구역 초기화
        self.parking_zones = self.init_parking_zones()
        
        # 점수 저장소
        self.vehicle_scores = {}
        self.ideal_templates = {}  # 구역별 이상적 템플릿 캐시
        
        print(f"🎯 템플릿 매칭 주차 시스템 초기화 완료")
    
    def zone_rect_to_poly(self, rect_norm, width, height):
        """정규화된 좌표를 픽셀 좌표로 변환"""
        x1n, y1n, x2n, y2n = rect_norm
        x1, y1 = int(x1n * width), int(y1n * height)
        x2, y2 = int(x2n * width), int(y2n * height)
        return np.array([[x1, y1], [x2, y1], [x2, y2], [x1, y2]])
    
    def init_parking_zones(self):
        """주차 구역 초기화"""
        parking_zones = {}
        for zone in PARKING_ZONES_NORM:
            parking_zones[zone["id"]] = {
                "id": zone["id"],
                "poly": self.zone_rect_to_poly(zone["rect"], self.rsize[0], self.rsize[1])
            }
        return parking_zones
    
    def get_ideal_template(self, zone_id, vehicle_model):
        """구역과 차량 모델에 대한 이상적 템플릿 생성/조회"""
        template_key = f"{zone_id}_{vehicle_model}"
        
        if template_key not in self.ideal_templates:
            zone_poly = self.parking_zones[zone_id]["poly"]
            vehicle_specs = self.vehicle_db.get_vehicle_specs(vehicle_model)
            
            template = self.scorer.template_generator.create_ideal_template(
                zone_poly, 
                vehicle_specs["length_mm"], 
                vehicle_specs["width_mm"]
            )
            
            self.ideal_templates[template_key] = template
            print(f"📐 {zone_id} 구역 {vehicle_model} 이상적 템플릿 생성")
        
        return self.ideal_templates[template_key]
    
    def calculate_vehicle_angle(self, obb_coords, xywhr_data):
        """차량 각도 계산"""
        if xywhr_data is not None and len(xywhr_data) >= 5:
            angle_rad = xywhr_data[4]
            angle_deg = math.degrees(angle_rad)
            angle_deg = abs(angle_deg) % 180
            if angle_deg > 90:
                angle_deg = 180 - angle_deg
        else:
            # OBB 박스의 장축 방향으로 각도 계산
            vec1 = obb_coords[1] - obb_coords[0]
            vec2 = obb_coords[3] - obb_coords[0]
            
            if np.linalg.norm(vec1) > np.linalg.norm(vec2):
                angle_rad = math.atan2(vec1[1], vec1[0])
            else:
                angle_rad = math.atan2(vec2[1], vec2[0])
            
            angle_deg = abs(math.degrees(angle_rad))
            if angle_deg > 90:
                angle_deg = 180 - angle_deg
        
        return angle_deg
    
    def find_parking_zone(self, center):
        """중심점이 속한 주차 구역 찾기"""
        cx, cy = center
        for zone_id, zone_data in self.parking_zones.items():
            zone_poly = zone_data["poly"].reshape(-1, 1, 2)
            if cv2.pointPolygonTest(zone_poly, (cx, cy), False) >= 0:
                return zone_id
        return None
    
    def get_color_by_score(self, score):
        """점수에 따른 색상 반환"""
        if score >= 80:
            return (0, 255, 0)    # 초록색
        elif score >= 70:
            return (0, 255, 255)  # 노란색
        elif score >= 60:
            return (0, 165, 255)  # 주황색
        else:
            return (0, 0, 255)    # 빨간색
    
    def draw_vehicle_and_template(self, frame, obb_coords, ideal_template, track_id, 
                                vehicle_model, score_info, zone_id):
        """차량과 이상적 템플릿을 함께 그리기"""
        # 실제 차량 그리기
        color = self.get_color_by_score(score_info['total_score'])
        points_array = np.array(obb_coords, dtype=np.int32).reshape(-1, 2)
        cv2.polylines(frame, [points_array], True, color, 3)
        
        # 이상적 템플릿 그리기 (점선)
        template_points = np.array(ideal_template['box'], dtype=np.int32).reshape(-1, 2)
        
        # 점선 효과를 위한 간격 그리기
        for i in range(len(template_points)):
            start_point = template_points[i]
            end_point = template_points[(i + 1) % len(template_points)]
            
            # 점선 그리기
            line_length = np.linalg.norm(end_point - start_point)
            num_segments = int(line_length / 10)  # 10픽셀 간격
            
            for j in range(0, num_segments, 2):  # 짝수 번째만 그리기
                if j + 1 < num_segments:
                    seg_start = start_point + (end_point - start_point) * j / num_segments
                    seg_end = start_point + (end_point - start_point) * (j + 1) / num_segments
                    cv2.line(frame, tuple(seg_start.astype(int)), 
                            tuple(seg_end.astype(int)), (255, 255, 255), 2)
        
        # 중심점 표시
        actual_center = np.mean(obb_coords, axis=0).astype(int)
        ideal_center = ideal_template['center'].astype(int)
        
        cv2.circle(frame, tuple(actual_center), 6, color, -1)  # 실제 중심
        cv2.circle(frame, tuple(ideal_center), 6, (255, 255, 255), 2)  # 이상적 중심
        
        # 중심점 연결선
        cv2.line(frame, tuple(actual_center), tuple(ideal_center), (255, 0, 255), 2)
        
        # 숙련도 레벨 (이미 영어)
        skill_eng = score_info['details']['skill_level']
        
        # 정보 텍스트 (영어로 변환)
        info_lines = [
            f"ID:{track_id} {vehicle_model}",
            f"Score: {score_info['total_score']:.1f}",
            f"Angle:{score_info['angle_score']:.0f} ({skill_eng})"
        ]
        
        # 텍스트 위치
        text_x = actual_center[0] - 50
        text_y = actual_center[1] - 80
        
        # 경계 체크
        if text_y < 80:
            text_y = actual_center[1] + 80
        if text_x < 10:
            text_x = 10
        if text_x > frame.shape[1] - 200:
            text_x = frame.shape[1] - 200
        
        # 텍스트 그리기 (배경 + 텍스트)
        for i, line in enumerate(info_lines):
            y_pos = text_y + i * 20
            cv2.rectangle(frame, (text_x - 5, y_pos - 15), 
                         (text_x + 200, y_pos + 5), (0, 0, 0), -1)
            cv2.putText(frame, line, (text_x, y_pos), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    def draw_parking_zones(self, frame):
        """주차 구역 그리기"""
        for zone_id, zone_data in self.parking_zones.items():
            cv2.polylines(frame, [zone_data["poly"]], True, (255, 255, 0), 2)
            
            zone_center = np.mean(zone_data["poly"], axis=0).astype(int)
            cv2.putText(frame, zone_id.upper(), tuple(zone_center - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
    
    def process_video(self, source_path="new.mp4"):
        """비디오 처리 메인 함수"""
        print("🎬 템플릿 매칭 주차 분석 시작...")
        
        cap = cv2.VideoCapture(source_path)
        if not cap.isOpened():
            print(f"❌ 비디오 파일을 열 수 없습니다: {source_path}")
            return
        
        # 비디오 정보
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # 출력 설정
        output_path = "./output/template_matching_output.mp4"
        os.makedirs("./output", exist_ok=True)
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, self.rsize)
        
        frame_count = 0
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_count += 1
                
                # 진행률 표시
                if frame_count % 30 == 0:
                    progress = (frame_count / total_frames) * 100
                    print(f"🔄 처리 진행률: {progress:.1f}% ({frame_count}/{total_frames})")
                
                frame = cv2.resize(frame, self.rsize)
                
                # YOLO 추적
                results = self.model.track(
                    frame,
                    conf=self.conf_threshold,
                    iou=self.iou_threshold,
                    tracker="bytetrack.yaml",
                    persist=True,
                    verbose=False,
                    imgsz=self.rsize
                )
                
                # 주차 구역 그리기
                self.draw_parking_zones(frame)
                
                if results and len(results) > 0:
                    self.process_vehicles(frame, results[0], frame_count)
                
                # 프레임 정보
                cv2.putText(frame, f"Frame: {frame_count}/{total_frames}", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                
                out.write(frame)
        
        except KeyboardInterrupt:
            print("⏹️ 사용자에 의해 중단되었습니다.")
        finally:
            cap.release()
            out.release()
            
            print(f"\n✅ 처리 완료! 출력: {output_path}")
            self.print_final_results()
    
    def process_vehicles(self, frame, result, frame_count):
        """차량 처리 및 템플릿 매칭"""
        try:
            if not (hasattr(result, 'obb') and result.obb is not None):
                return
            
            xyxyxyxy = result.obb.xyxyxyxy
            xywhr = result.obb.xywhr
            
            # 추적 ID 추출
            track_ids = None
            if hasattr(result, 'boxes') and result.boxes is not None and hasattr(result.boxes, 'id'):
                track_ids = result.boxes.id.int()
            
            for i in range(len(xyxyxyxy)):
                try:
                    obb_coords = xyxyxyxy[i].cpu().numpy()
                    xywhr_data = xywhr[i].cpu().numpy() if i < len(xywhr) else None
                    
                    # Track ID
                    track_id = track_ids[i].item() if track_ids is not None and i < len(track_ids) else i
                    
                    # 차량 중심점 및 각도
                    center = np.mean(obb_coords, axis=0)
                    angle = self.calculate_vehicle_angle(obb_coords, xywhr_data)
                    
                    # 주차 구역 확인
                    zone_id = self.find_parking_zone(center)
                    
                    if zone_id:
                        # 차량 모델 할당
                        vehicle_model = self.vehicle_db.get_vehicle_for_zone(track_id, zone_id)
                        vehicle_specs = self.vehicle_db.get_vehicle_specs(vehicle_model)
                        
                        # 이상적 템플릿 생성
                        ideal_template = self.get_ideal_template(zone_id, vehicle_model)
                        
                        # 템플릿 매칭 점수 계산 (차량 사양 포함)
                        score_info = self.scorer.calculate_template_matching_score(
                            obb_coords, ideal_template, angle, vehicle_specs
                        )
                        
                        # 점수 저장
                        self.vehicle_scores[track_id] = {
                            'zone_id': zone_id,
                            'vehicle_model': vehicle_model,
                            'score_info': score_info,
                            'ideal_template': ideal_template,
                            'last_update': frame_count
                        }
                        
                        # 시각화
                        self.draw_vehicle_and_template(frame, obb_coords, ideal_template, 
                                                     track_id, vehicle_model, score_info, zone_id)
                        
                        # 30프레임마다 로그 출력
                        if frame_count % 30 == 0:
                            self.print_vehicle_status(track_id, vehicle_model, score_info, zone_id)
                
                except Exception as e:
                    print(f"⚠️ 차량 {i} 처리 오류: {e}")
                    continue
        
        except Exception as e:
            print(f"❌ 차량 처리 전체 오류: {e}")
    
    def print_vehicle_status(self, track_id, vehicle_model, score_info, zone_id):
        """차량 상태 출력 (새로운 3단계 각도 시스템)"""
        details = score_info['details']
        skill_level = details['skill_level']  # 이미 영어
        lane_violation = details.get('lane_violation', False)
        
        print(f"\n🚗 ID {track_id} [{zone_id}] {vehicle_model}")
        print(f"   📊 Total Score: {score_info['total_score']:.1f}")
        print(f"   📐 Angle: {score_info['angle_score']:.1f} (diff: {details['angle_diff']:.1f}°)")
        print(f"      Skill: {skill_level} | Original: {details['actual_angle']:.1f}° → Corrected: {details['corrected_angle']:.1f}°")
        
        if lane_violation and details['angle_diff'] >= 6:
            print(f"   🚨 Lane violation penalty applied! (angle ≥6° + zone violation)")
        elif details['angle_diff'] >= 6:
            print(f"   ⚠️  Angle ≥6° but no lane violation")
        else:
            print(f"   ✅ Excellent angle alignment")
    
    def print_final_results(self):
        """최종 결과 출력"""
        if not self.vehicle_scores:
            print("\n❌ No vehicles analyzed.")
            return
        
        print(f"\n🏆 Template Matching Final Results")
        print("=" * 60)
        
        # 구역별 정리
        zone_results = defaultdict(list)
        for track_id, data in self.vehicle_scores.items():
            zone_results[data['zone_id']].append((track_id, data))
        
        for zone_id in sorted(zone_results.keys()):
            vehicles = zone_results[zone_id]
            print(f"\n📍 Zone {zone_id.upper()} ({len(vehicles)} vehicles)")
            print("-" * 40)
            
            for track_id, data in vehicles:
                score = data['score_info']['total_score']
                model = data['vehicle_model']
                
                if score >= 80:
                    grade = "🏆 Perfect"
                elif score >= 70:
                    grade = "👍 Good"
                elif score >= 60:
                    grade = "😐 Average"
                else:
                    grade = "👎 Poor"
                
                print(f"   🚙 ID {track_id}: {model} - {score:.1f} {grade}")
        
        # 전체 통계
        all_scores = [data['score_info']['total_score'] for data in self.vehicle_scores.values()]
        print(f"\n📊 Overall Statistics")
        print(f"   Total vehicles: {len(all_scores)}")
        print(f"   Average score: {np.mean(all_scores):.1f}")
        print(f"   Highest score: {max(all_scores):.1f}")
        print(f"   Lowest score: {min(all_scores):.1f}")

def main():
    """메인 함수"""
    print("🎯 Template Matching Parking Analysis System")
    
    # 시스템 초기화
    system = TemplateMatchingParkingSystem(model_path="best.pt")
    
    # 비디오 처리
    system.process_video("new.mp4")

if __name__ == "__main__":
    main()
