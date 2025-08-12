#!/usr/bin/env python3
"""
텍스트 기반 구역 설정 도구
마우스 대신 키보드로 좌표를 입력하여 구역을 설정
"""

import cv2
import numpy as np
import json
import os
from datetime import datetime

class TextZoneSelector:
    def __init__(self, image_path):
        self.image_path = image_path
        self.original_frame = None
        
        # 구역 정보 (순서대로)
        self.zone_order = ['A1', 'A2', 'A3', 'A4', 'A5', 
                          'B1', 'B2', 'B3', 
                          'C1', 'C2', 'C3']
        self.zones = {}
        
        # 구역별 색상
        self.zone_colors = {
            'A1': (0, 0, 255), 'A2': (0, 0, 255), 'A3': (0, 0, 255), 'A4': (0, 0, 255), 'A5': (0, 0, 255),
            'B1': (0, 255, 0), 'B2': (0, 255, 0), 'B3': (0, 255, 0),
            'C1': (255, 0, 0), 'C2': (255, 0, 0), 'C3': (255, 0, 0),
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
            
        height, width = self.original_frame.shape[:2]
        print(f"✅ 이미지 로드 완료: {self.image_path}")
        print(f"📏 이미지 크기: {width} x {height}")
        return True
    
    def input_zone_coordinates(self, zone_name):
        """구역 좌표 입력받기"""
        print(f"\n📍 {zone_name} 구역 좌표를 입력하세요:")
        print("각 꼭지점을 시계방향으로 입력하세요 (x,y 형식)")
        print("예: 100,200")
        
        points = []
        for i in range(4):
            while True:
                try:
                    coord_input = input(f"  점 {i+1}: ").strip()
                    if ',' not in coord_input:
                        print("❌ x,y 형식으로 입력하세요 (예: 100,200)")
                        continue
                    
                    x_str, y_str = coord_input.split(',')
                    x, y = int(x_str.strip()), int(y_str.strip())
                    
                    # 범위 체크
                    height, width = self.original_frame.shape[:2]
                    if 0 <= x < width and 0 <= y < height:
                        points.append((x, y))
                        print(f"    ✅ 점 {i+1}: ({x}, {y})")
                        break
                    else:
                        print(f"❌ 좌표 범위 초과. 0-{width-1}, 0-{height-1} 범위 내로 입력하세요")
                        
                except ValueError:
                    print("❌ 숫자만 입력하세요")
                except Exception as e:
                    print(f"❌ 입력 오류: {e}")
        
        return points
    
    def preview_zone(self, zone_name, points):
        """구역 미리보기"""
        preview_img = self.original_frame.copy()
        
        # 기존 구역들 그리기
        for name, zone_points in self.zones.items():
            color = self.zone_colors[name]
            pts = np.array(zone_points, np.int32).reshape((-1, 1, 2))
            cv2.polylines(preview_img, [pts], True, color, 2)
            
            # 구역 이름
            center_x = int(np.mean([p[0] for p in zone_points]))
            center_y = int(np.mean([p[1] for p in zone_points]))
            cv2.putText(preview_img, name, (center_x-15, center_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # 새 구역 그리기
        color = self.zone_colors[zone_name]
        pts = np.array(points, np.int32).reshape((-1, 1, 2))
        cv2.polylines(preview_img, [pts], True, color, 3)  # 더 두껍게
        
        # 점 번호 표시
        for i, (x, y) in enumerate(points):
            cv2.circle(preview_img, (x, y), 5, (0, 255, 255), -1)
            cv2.putText(preview_img, str(i+1), (x+10, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
        
        # 구역 이름
        center_x = int(np.mean([p[0] for p in points]))
        center_y = int(np.mean([p[1] for p in points]))
        cv2.putText(preview_img, zone_name, (center_x-15, center_y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        # 미리보기 이미지 저장
        preview_filename = f"preview_{zone_name}.jpg"
        cv2.imwrite(preview_filename, preview_img)
        print(f"📷 미리보기 저장: {preview_filename}")
        
        return preview_filename
    
    def confirm_zone(self, zone_name, points):
        """구역 확인"""
        print(f"\n{zone_name} 구역 좌표:")
        for i, (x, y) in enumerate(points):
            print(f"  점 {i+1}: ({x}, {y})")
        
        while True:
            confirm = input("이 구역이 맞습니까? (y/n/r=다시입력): ").strip().lower()
            if confirm in ['y', 'yes']:
                return True
            elif confirm in ['n', 'no']:
                return False
            elif confirm in ['r', 'retry']:
                return None
            else:
                print("y(예), n(아니오), r(다시입력) 중 하나를 입력하세요")
    
    def run(self):
        """메인 실행"""
        print("🚀 텍스트 기반 구역 설정 도구")
        print("=" * 50)
        
        if not self.load_image():
            return
        
        height, width = self.original_frame.shape[:2]
        print(f"\n📐 참고 정보:")
        print(f"   이미지 크기: {width} x {height}")
        print(f"   왼쪽 위: (0, 0)")
        print(f"   오른쪽 아래: ({width-1}, {height-1})")
        
        # 각 구역별로 입력
        for zone_name in self.zone_order:
            print(f"\n{'='*20} {zone_name} 구역 {'='*20}")
            
            while True:
                # 좌표 입력
                points = self.input_zone_coordinates(zone_name)
                
                # 미리보기 생성
                self.preview_zone(zone_name, points)
                
                # 확인
                result = self.confirm_zone(zone_name, points)
                if result is True:
                    self.zones[zone_name] = points
                    print(f"✅ {zone_name} 구역 저장 완료!")
                    break
                elif result is None:
                    print("🔄 다시 입력합니다...")
                    continue
                else:
                    print("❌ 구역을 저장하지 않고 넘어갑니다.")
                    break
        
        # 최종 결과
        self.save_final_result()
    
    def save_final_result(self):
        """최종 결과 저장"""
        if not self.zones:
            print("❌ 저장할 구역이 없습니다.")
            return
        
        # 최종 이미지 생성
        final_img = self.original_frame.copy()
        
        for zone_name, points in self.zones.items():
            color = self.zone_colors[zone_name]
            pts = np.array(points, np.int32).reshape((-1, 1, 2))
            
            # 반투명 채우기
            overlay = final_img.copy()
            cv2.fillPoly(overlay, [pts], color)
            cv2.addWeighted(overlay, 0.3, final_img, 0.7, 0, final_img)
            
            # 경계선
            cv2.polylines(final_img, [pts], True, color, 2)
            
            # 구역 이름
            center_x = int(np.mean([p[0] for p in points]))
            center_y = int(np.mean([p[1] for p in points]))
            cv2.putText(final_img, zone_name, (center_x-15, center_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        # 최종 이미지 저장
        final_filename = "final_zones_result.jpg"
        cv2.imwrite(final_filename, final_img)
        print(f"🎯 최종 결과 저장: {final_filename}")
        
        # JSON 저장
        self.save_json()
        
        # Python 코드 출력
        self.print_python_format()
    
    def save_json(self):
        """JSON 형태로 저장"""
        height, width = self.original_frame.shape[:2]
        
        zones_data = {
            "image_info": {
                "width": width,
                "height": height,
                "source": self.image_path
            },
            "zones": []
        }
        
        for zone_name in self.zone_order:
            if zone_name in self.zones:
                points = self.zones[zone_name]
                zone_data = {
                    "name": zone_name,
                    "points_absolute": points,
                    "points_normalized": [
                        [round(x / width, 4), round(y / height, 4)] for x, y in points
                    ],
                    "bbox_normalized": {
                        "x1": round(min(p[0] for p in points) / width, 4),
                        "y1": round(min(p[1] for p in points) / height, 4),
                        "x2": round(max(p[0] for p in points) / width, 4),
                        "y2": round(max(p[1] for p in points) / height, 4)
                    }
                }
                zones_data["zones"].append(zone_data)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_filename = f"parking_zones_text_{timestamp}.json"
        
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(zones_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 JSON 저장: {json_filename}")
    
    def print_python_format(self):
        """파이썬 코드 형태로 출력"""
        print("\n" + "="*60)
        print("📋 파이썬 코드용 좌표 (정규화됨):")
        print("="*60)
        
        height, width = self.original_frame.shape[:2]
        
        print("PARKING_ZONES_NORM = [")
        for zone_name in self.zone_order:
            if zone_name in self.zones:
                points = self.zones[zone_name]
                x1, x2 = min(p[0] for p in points) / width, max(p[0] for p in points) / width
                y1, y2 = min(p[1] for p in points) / height, max(p[1] for p in points) / height
                print(f"    [{x1:.4f}, {y1:.4f}, {x2:.4f}, {y2:.4f}],  # {zone_name}")
        print("]")
        print("="*60)


def main():
    print("=== 텍스트 기반 주차 구역 설정 도구 ===")
    print("마우스 없이 키보드로 좌표를 입력하여 구역을 설정합니다.\n")
    
    image_path = "angle_first_frame.jpg"
    
    if not os.path.exists(image_path):
        print(f"❌ 이미지 파일이 없습니다: {image_path}")
        return
    
    selector = TextZoneSelector(image_path)
    selector.run()


if __name__ == "__main__":
    main()
