#!/usr/bin/env python3
"""
주차 점수 계산 시스템
- 차량 검출 및 추적
- 차량 타입별 길이 매핑
- 중심점 기반 주차 점수 계산
- 각도 편차에 따른 감점 시스템
"""

import cv2
from ultralytics import YOLO
import os
import numpy as np
import math
from collections import defaultdict
from parking_score_calculator import ParkingScoreCalculator

# 주차 구역 정의 (정규화된 좌표)
# 웹 마우스 도구로 직접 설정한 정확한 좌표
PARKING_ZONES_NORM = [
    # B구역 (위쪽)
    {"id": "b1", "rect": [0.414251, 0.008621, 0.493357, 0.240421]},
    {"id": "b2", "rect": [0.494565, 0.017241, 0.583333, 0.254789]},
    {"id": "b3", "rect": [0.584541, 0.017241, 0.657609, 0.265326]},
    
    # C구역 (중간)
    {"id": "c1", "rect": [0.693237, 0.030651, 0.775362, 0.239464]},
    {"id": "c2", "rect": [0.775362, 0.038314, 0.856280, 0.246169]},
    {"id": "c3", "rect": [0.847826, 0.035441, 0.930556, 0.229885]},
    
    # A구역 (아래쪽)
    {"id": "a1", "rect": [0.397343, 0.726054, 0.487319, 0.989464]},
    {"id": "a2", "rect": [0.493357, 0.729885, 0.580918, 0.983716]},
    {"id": "a3", "rect": [0.578502, 0.727011, 0.663647, 0.987548]},
    {"id": "a4", "rect": [0.695048, 0.735632, 0.776570, 0.983716]},
    {"id": "a5", "rect": [0.777174, 0.729885, 0.859300, 0.983716]}
]

class VehicleDatabase:
    """차량 타입별 길이 데이터베이스"""
    
    def __init__(self):
        # car.mp4에 있는 모형차들의 실제 치수 (mm)
        self.vehicle_types = {
            "모닝": {"length_mm": 105, "width_mm": 50, "type": "소형차"},      # 모형차 소형
            "K5": {"length_mm": 118, "width_mm": 50, "type": "중형차"},       # 모형차 중형  
            "K8": {"length_mm": 118, "width_mm": 50, "type": "중형차"},       # 모형차 중형
            "카니발": {"length_mm": 125, "width_mm": 50, "type": "승합차"},     # 모형차 대형(SUV)
        }
        
        # 차량 타입별 기본 매핑 (백업용) - 모형차 치수
        self.type_mapping = {
            "소형차": {"length_mm": 105, "width_mm": 50},    # 소형 모형차
            "중형차": {"length_mm": 118, "width_mm": 50},    # 중형 모형차
            "승합차": {"length_mm": 125, "width_mm": 50},    # 대형 모형차
        }
        
        # Track ID별 차량 타입 할당 (시뮬레이션)
        self.track_to_vehicle_type = {}
    
    def assign_vehicle_type(self, track_id, zone_id):
        """구역 기반으로 차량 모델 할당 (car.mp4의 실제 주차 상황)"""
        if track_id in self.track_to_vehicle_type:
            return self.track_to_vehicle_type[track_id]
        
        # 구역별 실제 주차 차량 할당
        if zone_id and zone_id.lower().startswith('a'):
            # A구역: 카니발 (승합차)
            vehicle_model = "카니발"
        elif zone_id and zone_id.lower().startswith('b'):
            # B구역: K시리즈 (중형차) - K5, K8 순환
            k_models = ["K5", "K8"]
            vehicle_model = k_models[track_id % len(k_models)]
        elif zone_id and zone_id.lower().startswith('c'):
            # C구역: 모닝 (소형차)
            vehicle_model = "모닝"
        else:
            # 기본값: 중형차
            vehicle_model = "K5"
        
        self.track_to_vehicle_type[track_id] = vehicle_model
        print(f"🚗 Vehicle ID {track_id} in {zone_id} -> {vehicle_model} assigned")
        return vehicle_model
    
    def get_vehicle_info(self, track_id, zone_id):
        """차량 정보 반환 (실제 모델 기반)"""
        vehicle_model = self.assign_vehicle_type(track_id, zone_id)
        
        if vehicle_model in self.vehicle_types:
            vehicle_data = self.vehicle_types[vehicle_model]
            return {
                "model": vehicle_model,
                "type": vehicle_data["type"],
                "length_mm": vehicle_data["length_mm"],
                "width_mm": vehicle_data["width_mm"]
            }
        else:
            # 백업: 기본 중형차 정보 (모형차)
            return {
                "model": "Unknown",
                "type": "중형차",
                "length_mm": 118,  # 모형차 중형 길이
                "width_mm": 50     # 모형차 폭
            }

class ParkingScoreSystem:
    """주차 점수 계산 시스템"""
    
    def __init__(self, model_path="best.pt"):
        self.model = YOLO(model_path)
        self.score_calculator = ParkingScoreCalculator()
        self.vehicle_db = VehicleDatabase()
        self.track_history = defaultdict(list)
        
        # 추적 설정
        self.conf_threshold = 0.1  # 원래 값으로 복원
        self.iou_threshold = 0.4
        self.rsize = (1920, 1088)
        
        # 주차 구역 초기화
        self.parking_zones = self.init_parking_zones()
        
        # 점수 저장소
        self.vehicle_scores = {}  # {track_id: {zone_id, score_info, vehicle_info, ...}}
        
        print(f"🚗 주차 점수 계산 시스템 초기화 완료")
        print(f"📊 주차 구역 수: {len(self.parking_zones)}")

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
    
    def get_vehicle_box_from_obb(self, obb_coords, angle_deg=0):
        """OBB 좌표를 vehicle_box 형태로 변환"""
        # OBB 좌표가 이미 4개 점으로 되어 있음
        return np.array(obb_coords)
    
    def calculate_vehicle_center_and_angle(self, obb_coords, xywhr_data):
        """차량의 중심점과 각도 계산"""
        # 중심점 계산
        center_x = int(np.mean(obb_coords[:, 0]))
        center_y = int(np.mean(obb_coords[:, 1]))
        
        # 각도 계산 (라디안을 도로 변환)
        if xywhr_data is not None and len(xywhr_data) >= 5:
            angle_rad = xywhr_data[4]
            angle_deg = math.degrees(angle_rad)
            # 각도를 0-180도 범위로 정규화
            angle_deg = abs(angle_deg) % 180
            if angle_deg > 90:
                angle_deg = 180 - angle_deg
        else:
            # OBB 박스의 장축 방향으로 각도 계산
            # 첫 번째와 두 번째 점 사이의 벡터 계산
            vec1 = obb_coords[1] - obb_coords[0]
            vec2 = obb_coords[3] - obb_coords[0]
            
            # 더 긴 변을 기준으로 각도 계산
            if np.linalg.norm(vec1) > np.linalg.norm(vec2):
                angle_rad = math.atan2(vec1[1], vec1[0])
            else:
                angle_rad = math.atan2(vec2[1], vec2[0])
            
            angle_deg = abs(math.degrees(angle_rad))
            if angle_deg > 90:
                angle_deg = 180 - angle_deg
        
        return (center_x, center_y), angle_deg
    
    def get_color_by_score(self, score):
        """점수에 따른 색상 반환"""
        if score >= 80:
            return (0, 255, 0)    # 초록색 (우수)
        elif score >= 70:
            return (0, 255, 255)  # 노란색 (양호)
        elif score >= 60:
            return (0, 165, 255)  # 주황색 (보통)
        else:
            return (0, 0, 255)    # 빨간색 (미흡)
    
    def draw_vehicle_with_score(self, frame, obb_coords, track_id, vehicle_info, score_info, zone_id, center, angle):
        """차량과 점수 정보를 프레임에 그리기 (개선된 가독성)"""
        if score_info:
            total_score = score_info['total_score']
            color = self.get_color_by_score(total_score)
            score_text = f"{total_score}pts"  # 한글 제거
        else:
            color = (128, 128, 128)  # 회색
            score_text = "Calc..."  # 한글 제거
        
        # OBB 박스 그리기 (더 두껍게)
        points_array = np.array(obb_coords, dtype=np.int32).reshape(-1, 2)
        cv2.polylines(frame, [points_array], True, color, 4)
        
        # 중심점 표시 (더 크게)
        cv2.circle(frame, center, 8, (0, 0, 255), -1)  # 빨간 점
        cv2.circle(frame, center, 10, (255, 255, 255), 2)  # 흰색 테두리
        
        # 정보 텍스트 준비 (영어로 변경)
        model_en = {
            "모닝": "Morning",
            "K5": "K5", 
            "K8": "K8",
            "카니발": "Carnival"
        }.get(vehicle_info['model'], vehicle_info['model'])
        
        info_lines = [
            f"ID:{track_id}",
            f"{model_en}",
            f"{score_text}"
        ]
        
        # 텍스트 위치 계산 (차량 위쪽에 표시)
        text_x = center[0] - 40
        text_y = center[1] - 60
        
        # 프레임 경계 체크
        if text_y < 50:
            text_y = center[1] + 60  # 아래쪽으로 이동
        if text_x < 10:
            text_x = 10
        if text_x > frame.shape[1] - 150:
            text_x = frame.shape[1] - 150
        
        # 텍스트 배경 및 내용 그리기 (더 큰 폰트)
        font_scale = 0.8
        thickness = 2
        
        for i, line in enumerate(info_lines):
            y_pos = text_y + i * 30
            text_size = cv2.getTextSize(line, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)[0]
            
            # 배경 사각형 (더 크게)
            cv2.rectangle(frame, (text_x - 5, y_pos - 25), 
                         (text_x + text_size[0] + 10, y_pos + 5), color, -1)
            
            # 텍스트 테두리 (가독성 향상)
            cv2.putText(frame, line, (text_x, y_pos), 
                       cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 0), thickness + 2)
            
            # 텍스트 (흰색)
            cv2.putText(frame, line, (text_x, y_pos), 
                       cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), thickness)
    
    def draw_parking_zones(self, frame):
        """주차 구역 그리기 (개선된 가독성)"""
        for zone_id, zone_data in self.parking_zones.items():
            # 구역 경계선 (더 두껍게)
            cv2.polylines(frame, [zone_data["poly"]], True, (255, 255, 0), 3)
            
            # 구역 이름 (더 큰 폰트, 배경 추가)
            zone_center = np.mean(zone_data["poly"], axis=0).astype(int)
            
            # 텍스트 크기 계산
            font_scale = 1.2
            thickness = 3
            text_size = cv2.getTextSize(zone_id.upper(), cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)[0]
            
            # 배경 사각형
            bg_x1 = zone_center[0] - text_size[0] // 2 - 5
            bg_y1 = zone_center[1] - text_size[1] // 2 - 10
            bg_x2 = zone_center[0] + text_size[0] // 2 + 5
            bg_y2 = zone_center[1] + text_size[1] // 2 + 5
            
            cv2.rectangle(frame, (bg_x1, bg_y1), (bg_x2, bg_y2), (0, 0, 0), -1)
            
            # 구역 이름 텍스트
            text_x = zone_center[0] - text_size[0] // 2
            text_y = zone_center[1] + text_size[1] // 2
            
            cv2.putText(frame, zone_id.upper(), (text_x, text_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 0), thickness)
    
    def process_video_with_scoring(self, source_path="car.mp4"):
        """주차 점수 계산이 포함된 비디오 처리"""
        print("🎯 주차 점수 계산 시스템 시작...")
        
        # 비디오 캡처 열기
        cap = cv2.VideoCapture(source_path)
        if not cap.isOpened():
            print(f"❌ 비디오 파일을 열 수 없습니다: {source_path}")
            return
        
        # 비디오 정보
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        print(f"📹 비디오 정보 - 해상도: {width}x{height}, FPS: {fps}, 총 프레임: {total_frames}")
        
        # 출력 비디오 설정
        output_path = "./output/parking_score_output.mp4"
        os.makedirs("./output", exist_ok=True)
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, self.rsize)
        
        frame_count = 0
        start_time = cv2.getTickCount()
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_count += 1
                
                # 진행률 표시
                if frame_count % 30 == 0:
                    progress = (frame_count / total_frames) * 100 if total_frames > 0 else 0.0
                    print(f"🔄 처리 진행률: {progress:.1f}% ({frame_count}/{total_frames})")
                
                frame = cv2.resize(frame, self.rsize)
                
                # YOLO 추적 실행
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
                    result = results[0]
                    
                    # OBB 결과 처리
                    if hasattr(result, 'obb') and result.obb is not None:
                        self.process_vehicles_with_scoring(frame, result, frame_count)
                
                # 프레임 정보 표시 (개선된 가독성)
                frame_text = f"Frame: {frame_count}/{total_frames}"
                text_size = cv2.getTextSize(frame_text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
                
                # 배경 사각형
                cv2.rectangle(frame, (5, 5), (15 + text_size[0], 35), (0, 0, 0), -1)
                cv2.putText(frame, frame_text, (10, 25),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                
                # 점수 통계 표시
                self.draw_score_statistics(frame)
                
                # 결과 저장
                out.write(frame)
        
        except KeyboardInterrupt:
            print("⏹️ 사용자에 의해 중단되었습니다.")
        finally:
            cap.release()
            out.release()
            
            # 처리 완료 정보
            total_time = (cv2.getTickCount() - start_time) / cv2.getTickFrequency()
            avg_fps = frame_count / total_time if total_time > 0 else 0
            
            print(f"\n✅ 처리 완료!")
            print(f"⏱️ 총 처리 시간: {total_time:.2f}초")
            print(f"📊 평균 FPS: {avg_fps:.1f}")
            print(f"🎬 처리된 프레임: {frame_count}")
            print(f"💾 결과 영상: {output_path}")
            
            # 최종 점수 요약
            self.print_final_scores()
    
    def process_vehicles_with_scoring(self, frame, result, frame_count):
        """차량별 점수 계산 처리"""
        try:
            xyxyxyxy = result.obb.xyxyxyxy
            xywhr = result.obb.xywhr
            classes = result.obb.cls.int()
            confidences = result.obb.conf
            
            # 추적 ID 추출
            track_ids = None
            if hasattr(result, 'boxes') and result.boxes is not None and hasattr(result.boxes, 'id'):
                track_ids = result.boxes.id.int()
            
            num_objects = len(xyxyxyxy)
            if num_objects == 0:
                return
            
            for i in range(num_objects):
                try:
                    obb_coords = xyxyxyxy[i].cpu().numpy()
                    confidence = confidences[i].item()
                    class_id = classes[i].item()
                    
                    # Track ID 추출
                    if track_ids is not None and i < len(track_ids):
                        track_id = track_ids[i].item()
                    else:
                        track_id = i
                    
                    # 중심점과 각도 계산
                    xywhr_data = xywhr[i].cpu().numpy() if i < len(xywhr) else None
                    center, angle = self.calculate_vehicle_center_and_angle(obb_coords, xywhr_data)
                    
                    # 주차 구역 확인
                    zone_id = self.find_parking_zone(center)
                    
                    if zone_id:
                        # 차량 정보 조회
                        vehicle_info = self.vehicle_db.get_vehicle_info(track_id, zone_id)
                        
                        # 주차 점수 계산
                        parking_zone = self.parking_zones[zone_id]["poly"]
                        vehicle_box = self.get_vehicle_box_from_obb(obb_coords, angle)
                        
                        score_info = self.score_calculator.calculate_parking_score(
                            vehicle_box=vehicle_box,
                            parking_zone=parking_zone,
                            vehicle_length_mm=vehicle_info["length_mm"],
                            vehicle_angle=angle
                        )
                        
                        # 점수 정보 저장
                        self.vehicle_scores[track_id] = {
                            'zone_id': zone_id,
                            'vehicle_info': vehicle_info,
                            'score_info': score_info,
                            'center': center,
                            'angle': angle,
                            'last_update': frame_count
                        }
                        
                        # 차량과 점수 정보 그리기
                        self.draw_vehicle_with_score(frame, obb_coords, track_id, vehicle_info, 
                                                   score_info, zone_id, center, angle)
                        
                        # 30프레임마다 점수 출력
                        if frame_count % 30 == 0:
                            self.print_vehicle_score(track_id, vehicle_info, score_info, zone_id)
                
                except Exception as e:
                    print(f"⚠️ 객체 {i} 처리 중 오류: {e}")
                    continue
        
        except Exception as e:
            print(f"❌ 차량 점수 계산 오류: {e}")
    
    def find_parking_zone(self, center):
        """중심점이 속한 주차 구역 찾기"""
        cx, cy = center
        for zone_id, zone_data in self.parking_zones.items():
            zone_poly = zone_data["poly"].reshape(-1, 1, 2)
            if cv2.pointPolygonTest(zone_poly, (cx, cy), False) >= 0:
                return zone_id
        return None
    
    def draw_score_statistics(self, frame):
        """점수 통계 정보 표시 (개선된 가독성)"""
        if not self.vehicle_scores:
            return
        
        # 통계 계산
        scores = [data['score_info']['total_score'] for data in self.vehicle_scores.values()]
        avg_score = sum(scores) / len(scores)
        max_score = max(scores)
        min_score = min(scores)
        
        # 등급별 개수
        excellent = sum(1 for s in scores if s >= 80)
        good = sum(1 for s in scores if 70 <= s < 80)
        fair = sum(1 for s in scores if 60 <= s < 70)
        poor = sum(1 for s in scores if s < 60)
        
        # 통계 정보 표시 (영어로 변경)
        stats_lines = [
            f"Cars: {len(self.vehicle_scores)}",
            f"Avg: {avg_score:.1f}pts",
            f"Max: {max_score} / Min: {min_score}",
            f"Excellent: {excellent} | Good: {good} | Fair: {fair} | Poor: {poor}"
        ]
        
        # 배경 및 텍스트 그리기 (더 큰 폰트)
        start_y = self.rsize[1] - 120
        font_scale = 0.7
        thickness = 2
        
        for i, line in enumerate(stats_lines):
            y_pos = start_y + i * 30
            text_size = cv2.getTextSize(line, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)[0]
            
            # 배경 사각형 (더 크게)
            cv2.rectangle(frame, (5, y_pos - 25), (15 + text_size[0], y_pos + 5), (0, 0, 0), -1)
            cv2.putText(frame, line, (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), thickness)
    
    def print_vehicle_score(self, track_id, vehicle_info, score_info, zone_id):
        """개별 차량 점수 출력"""
        print(f"\n🚙 차량 ID {track_id} [{zone_id}구역]")
        print(f"   🚗 모델: {vehicle_info['model']} ({vehicle_info['type']}, {vehicle_info['length_mm']}mm)")
        print(f"   📊 총점: {score_info['total_score']}점")
        print(f"    각도: {score_info['angle_score']}점")
        
        details = score_info['details']
        print(f"    각도 편차: {details['angle_offset']:.1f}도")
    
    def print_final_scores(self):
        """최종 점수 요약 출력"""
        if not self.vehicle_scores:
            print("\n❌ 분석된 차량이 없습니다.")
            return
        
        print(f"\n🏁 최종 주차 점수 분석 결과")
        print("=" * 60)
        
        # 구역별 정리
        zone_vehicles = defaultdict(list)
        for track_id, data in self.vehicle_scores.items():
            zone_vehicles[data['zone_id']].append((track_id, data))
        
        for zone_id in sorted(zone_vehicles.keys()):
            vehicles = zone_vehicles[zone_id]
            print(f"\n📍 {zone_id.upper()}구역 ({len(vehicles)}대)")
            print("-" * 40)
            
            for track_id, data in vehicles:
                vehicle_info = data['vehicle_info']
                score_info = data['score_info']
                
                # 등급 판정
                total_score = score_info['total_score']
                if total_score >= 80:
                    grade = "🏆 우수"
                elif total_score >= 70:
                    grade = "👍 양호"
                elif total_score >= 60:
                    grade = "😐 보통"
                else:
                    grade = "👎 미흡"
                
                print(f"  🚙 ID {track_id}: {vehicle_info['model']} ({vehicle_info['type']}) - {total_score}점 {grade}")
        
        # 전체 통계
        all_scores = [data['score_info']['total_score'] for data in self.vehicle_scores.values()]
        avg_score = sum(all_scores) / len(all_scores)
        
        print(f"\n📊 전체 통계")
        print(f"   총 차량 수: {len(self.vehicle_scores)}대")
        print(f"   평균 점수: {avg_score:.1f}점")
        print(f"   최고 점수: {max(all_scores)}점")
        print(f"   최저 점수: {min(all_scores)}점")

def main():
    """메인 함수"""
    print("🚗 주차 점수 계산 시스템 시작")
    
    # 시스템 초기화
    scoring_system = ParkingScoreSystem(model_path="best.pt")
    
    # 비디오 처리 시작
    scoring_system.process_video_with_scoring("angle.mp4")

if __name__ == "__main__":
    main()
