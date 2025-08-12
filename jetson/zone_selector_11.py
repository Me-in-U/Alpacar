#!/usr/bin/env python3
"""
11개 주차 구역 순차 설정 도구
A1~A5, B1~B3, C1~C3 순서로 구역을 설정하는 도구
"""

import cv2
import numpy as np
import json
import os
from datetime import datetime

class OrderedZoneSelector:
    def __init__(self, image_path):
        """
        순차 구역 설정 도구 초기화
        
        Args:
            image_path: 이미지 파일 경로
        """
        self.image_path = image_path
        self.original_frame = None
        self.display_frame = None
        
        # 구역 정보 (순서대로)
        self.zone_order = ['A1', 'A2', 'A3', 'A4', 'A5', 
                          'B1', 'B2', 'B3', 
                          'C1', 'C2', 'C3']
        self.zones = {}  # 완성된 구역들 {name: points}
        self.current_zone = []  # 현재 그리고 있는 구역의 점들
        self.current_index = 0  # 현재 그리고 있는 구역 인덱스
        
        # 설정
        self.point_radius = 5
        self.line_thickness = 2
        
        # 구역별 색상
        self.zone_colors = {
            'A1': (0, 0, 255),    # 빨강
            'A2': (0, 0, 255),
            'A3': (0, 0, 255),
            'A4': (0, 0, 255),
            'A5': (0, 0, 255),
            'B1': (0, 255, 0),    # 초록
            'B2': (0, 255, 0),
            'B3': (0, 255, 0),
            'C1': (255, 0, 0),    # 파랑
            'C2': (255, 0, 0),
            'C3': (255, 0, 0),
        }
        
    def load_image(self):
        """이미지 로드"""
        if not os.path.exists(self.image_path):
            print(f"❌ 이미지 파일이 없습니다: {self.image_path}")
            return False
            
        self.original_frame = cv2.imread(self.image_path)
        if self.original_frame is None:
            print(f"❌ 이미지를 로드할 수 없습니다: {self.image_path}")
            return False
            
        print(f"✅ 이미지 로드 완료: {self.image_path}")
        print(f"📏 이미지 크기: {self.original_frame.shape[1]}x{self.original_frame.shape[0]}")
        
        # 디스플레이용 프레임 초기화
        self.display_frame = self.original_frame.copy()
        return True
    
    def get_current_zone_name(self):
        """현재 그리고 있는 구역 이름 반환"""
        if self.current_index < len(self.zone_order):
            return self.zone_order[self.current_index]
        return "완료"
    
    def mouse_callback(self, event, x, y, flags, param):
        """마우스 콜백 함수"""
        if self.current_index >= len(self.zone_order):
            return  # 모든 구역 완성됨
            
        current_zone_name = self.get_current_zone_name()
        
        if event == cv2.EVENT_LBUTTONDOWN:
            # 점 추가
            self.current_zone.append((x, y))
            print(f"📍 {current_zone_name} - 점 {len(self.current_zone)}: ({x}, {y})")
            
            # 4개 점이 모이면 구역 완성
            if len(self.current_zone) == 4:
                self.complete_current_zone()
            
            self.update_display()
            
        elif event == cv2.EVENT_RBUTTONDOWN:
            if len(self.current_zone) > 0:
                # 마지막 점 제거
                removed = self.current_zone.pop()
                print(f"🔄 {current_zone_name} - 점 제거: {removed}")
                self.update_display()
    
    def complete_current_zone(self):
        """현재 구역 완성 및 다음 구역으로 이동"""
        if len(self.current_zone) == 4:
            current_zone_name = self.get_current_zone_name()
            
            # 구역 저장
            self.zones[current_zone_name] = self.current_zone.copy()
            print(f"✅ {current_zone_name} 구역 완성!")
            
            # 다음 구역으로 이동
            self.current_index += 1
            self.current_zone = []
            
            if self.current_index < len(self.zone_order):
                next_zone_name = self.get_current_zone_name()
                print(f"➡️ 다음 구역: {next_zone_name}")
            else:
                print("🎉 모든 구역 설정 완료!")
    
    def update_display(self):
        """디스플레이 업데이트"""
        # 원본 이미지로 초기화
        self.display_frame = self.original_frame.copy()
        
        # 완성된 구역들 그리기
        for zone_name, points in self.zones.items():
            color = self.zone_colors[zone_name]
            pts = np.array(points, np.int32)
            pts = pts.reshape((-1, 1, 2))
            
            # 구역 채우기 (반투명)
            overlay = self.display_frame.copy()
            cv2.fillPoly(overlay, [pts], color)
            cv2.addWeighted(overlay, 0.3, self.display_frame, 0.7, 0, self.display_frame)
            
            # 구역 경계선
            cv2.polylines(self.display_frame, [pts], True, color, self.line_thickness)
            
            # 구역 이름 표시
            center_x = int(np.mean([p[0] for p in points]))
            center_y = int(np.mean([p[1] for p in points]))
            cv2.putText(self.display_frame, zone_name, 
                       (center_x - 15, center_y), cv2.FONT_HERSHEY_SIMPLEX, 
                       0.8, (255, 255, 255), 2)
        
        # 현재 그리고 있는 구역의 점들
        if self.current_index < len(self.zone_order):
            current_zone_name = self.get_current_zone_name()
            color = self.zone_colors[current_zone_name]
            
            for i, point in enumerate(self.current_zone):
                cv2.circle(self.display_frame, point, self.point_radius, (0, 255, 255), -1)
                cv2.putText(self.display_frame, str(i+1), 
                           (point[0] + 10, point[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 
                           0.5, (0, 255, 255), 1)
            
            # 현재 구역의 선들 (2개 이상 점이 있을 때)
            if len(self.current_zone) >= 2:
                for i in range(len(self.current_zone) - 1):
                    cv2.line(self.display_frame, self.current_zone[i], 
                            self.current_zone[i + 1], (0, 255, 255), self.line_thickness)
        
        # 안내 텍스트
        self.draw_instructions()
    
    def draw_instructions(self):
        """사용법 안내 표시"""
        if self.current_index < len(self.zone_order):
            current_zone_name = self.get_current_zone_name()
            progress = f"{self.current_index + 1}/{len(self.zone_order)}"
        else:
            current_zone_name = "완료"
            progress = f"{len(self.zone_order)}/{len(self.zone_order)}"
        
        instructions = [
            "=== 순차 주차 구역 설정 ===",
            f"현재 구역: {current_zone_name} ({progress})",
            f"완성된 구역: {len(self.zones)}개",
            "",
            "좌클릭: 구역 꼭지점 선택 (4개)",
            "우클릭: 마지막 점 제거",
            "S: 구역 저장",
            "R: 현재 구역 다시 시작",
            "Q: 종료",
            "",
            f"현재: {len(self.current_zone)}/4 점 선택됨"
        ]
        
        # 반투명 배경
        overlay = self.display_frame.copy()
        cv2.rectangle(overlay, (10, 10), (350, 250), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.8, self.display_frame, 0.2, 0, self.display_frame)
        
        # 텍스트 표시
        for i, text in enumerate(instructions):
            if text == "":
                continue
            y_pos = 30 + i * 20
            if text.startswith("현재 구역:"):
                color = (0, 255, 255)  # 노란색으로 강조
            else:
                color = (255, 255, 255)
            cv2.putText(self.display_frame, text, (20, y_pos), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        # 구역 순서 표시
        order_text = "순서: " + " → ".join(self.zone_order)
        cv2.putText(self.display_frame, order_text, (20, self.display_frame.shape[0] - 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    
    def restart_current_zone(self):
        """현재 구역 다시 시작"""
        if self.current_index < len(self.zone_order):
            current_zone_name = self.get_current_zone_name()
            self.current_zone = []
            print(f"🔄 {current_zone_name} 구역을 다시 시작합니다.")
            self.update_display()
    
    def save_zones(self, filename=None):
        """구역 정보 저장"""
        if not self.zones:
            print("❌ 저장할 구역이 없습니다.")
            return False
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"parking_zones_11_{timestamp}.json"
        
        # 이미지 크기 정보
        height, width = self.original_frame.shape[:2]
        
        # 절대 좌표와 정규화된 좌표 모두 저장
        zones_data = {
            "image_info": {
                "width": width,
                "height": height,
                "source": self.image_path
            },
            "zones": []
        }
        
        # 순서대로 저장
        for zone_name in self.zone_order:
            if zone_name in self.zones:
                points = self.zones[zone_name]
                zone_data = {
                    "name": zone_name,
                    "points_absolute": points,
                    "points_normalized": [
                        [round(x / width, 4), round(y / height, 4)] for x, y in points
                    ],
                    "bbox_absolute": {
                        "x1": min(p[0] for p in points),
                        "y1": min(p[1] for p in points),
                        "x2": max(p[0] for p in points),
                        "y2": max(p[1] for p in points)
                    }
                }
                
                # 정규화된 bbox
                zone_data["bbox_normalized"] = {
                    "x1": round(zone_data["bbox_absolute"]["x1"] / width, 4),
                    "y1": round(zone_data["bbox_absolute"]["y1"] / height, 4),
                    "x2": round(zone_data["bbox_absolute"]["x2"] / width, 4),
                    "y2": round(zone_data["bbox_absolute"]["y2"] / height, 4)
                }
                
                zones_data["zones"].append(zone_data)
        
        # 파일 저장
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(zones_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ 구역 정보가 저장되었습니다: {filename}")
            print(f"📊 총 {len(self.zones)}개 구역 저장됨")
            
            # 파이썬 코드 형태로도 출력
            self.print_python_format()
            
            return True
            
        except Exception as e:
            print(f"❌ 저장 실패: {e}")
            return False
    
    def print_python_format(self):
        """파이썬 코드 형태로 좌표 출력"""
        print("\n" + "="*60)
        print("📋 파이썬 코드용 좌표 (정규화됨):")
        print("="*60)
        
        height, width = self.original_frame.shape[:2]
        
        print("PARKING_ZONES_NORM = [")
        
        # 순서대로 출력
        for zone_name in self.zone_order:
            if zone_name in self.zones:
                points = self.zones[zone_name]
                
                # bbox 형태로 변환 (x1, y1, x2, y2)
                x_coords = [p[0] for p in points]
                y_coords = [p[1] for p in points]
                
                x1, x2 = min(x_coords) / width, max(x_coords) / width
                y1, y2 = min(y_coords) / height, max(y_coords) / height
                
                print(f"    [{x1:.4f}, {y1:.4f}, {x2:.4f}, {y2:.4f}],  # {zone_name}")
        
        print("]")
        print("\n구역 순서:")
        for i, zone_name in enumerate(self.zone_order):
            if zone_name in self.zones:
                print(f"  {i}: {zone_name}")
        print("="*60)
    
    def run(self):
        """메인 실행 함수"""
        print("🚀 11개 구역 순차 설정 도구 시작...")
        
        # 이미지 로드
        if not self.load_image():
            return
        
        # 초기 디스플레이 업데이트
        self.update_display()
        
        # 윈도우 생성 및 마우스 콜백 설정
        window_name = "11 Zone Sequential Selector"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.setMouseCallback(window_name, self.mouse_callback)
        
        print(f"\n🎯 구역 설정을 시작하세요!")
        print(f"📋 순서: {' → '.join(self.zone_order)}")
        print(f"💡 각 구역마다 4개의 꼭지점을 시계방향으로 클릭하세요.")
        print(f"🔥 첫 번째 구역: {self.get_current_zone_name()}")
        
        while True:
            cv2.imshow(window_name, self.display_frame)
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q') or key == 27:  # Q 또는 ESC
                break
            elif key == ord('s'):  # 저장
                self.save_zones()
            elif key == ord('r'):  # 현재 구역 다시 시작
                self.restart_current_zone()
        
        cv2.destroyAllWindows()
        print("👋 구역 설정 도구를 종료합니다.")
        
        # 최종 결과 출력
        if self.zones:
            print(f"\n📊 최종 결과: {len(self.zones)}개 구역 설정 완료")
            for zone_name in self.zone_order:
                if zone_name in self.zones:
                    print(f"  ✅ {zone_name}")
                else:
                    print(f"  ❌ {zone_name} (미완성)")


def main():
    """메인 함수"""
    print("=== 11개 주차 구역 순차 설정 도구 ===")
    print("A1~A5, B1~B3, C1~C3 순서로 구역을 설정합니다.\n")
    
    image_path = "angle_first_frame.jpg"
    
    if not os.path.exists(image_path):
        print(f"❌ 이미지 파일이 없습니다: {image_path}")
        print("먼저 extract_frame.py를 실행하여 이미지를 생성하세요.")
        return
    
    # 구역 설정 도구 실행
    selector = OrderedZoneSelector(image_path)
    selector.run()


if __name__ == "__main__":
    main()
