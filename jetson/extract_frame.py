#!/usr/bin/env python3
"""
비디오 첫 프레임 추출기
GUI가 지원되지 않는 환경에서 비디오의 첫 프레임을 이미지로 저장
"""

import cv2
import sys

def extract_first_frame(video_path, output_path="first_frame.jpg"):
    """비디오의 첫 프레임을 이미지로 저장"""
    try:
        # 비디오 열기
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"❌ 비디오를 열 수 없습니다: {video_path}")
            return False
        
        # 첫 프레임 읽기
        ret, frame = cap.read()
        if not ret:
            print(f"❌ 프레임을 읽을 수 없습니다: {video_path}")
            return False
        
        # 이미지 저장
        success = cv2.imwrite(output_path, frame)
        if success:
            print(f"✅ 첫 프레임 저장 완료: {output_path}")
            print(f"📏 이미지 크기: {frame.shape[1]}x{frame.shape[0]}")
            return True
        else:
            print(f"❌ 이미지 저장 실패: {output_path}")
            return False
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False
    finally:
        if 'cap' in locals():
            cap.release()

def main():
    video_path = "angle.mp4"
    output_path = "angle_first_frame.jpg"
    
    print("🎬 비디오 첫 프레임 추출기")
    print(f"📹 입력: {video_path}")
    print(f"🖼️ 출력: {output_path}")
    
    if extract_first_frame(video_path, output_path):
        print("\n✅ 추출 완료!")
        print(f"이제 {output_path} 파일을 다운로드하여 로컬에서 구역을 설정하거나,")
        print(f"좌표를 직접 확인할 수 있습니다.")
        
        # 이미지에 구역 가이드 표시
        show_coordinate_guide(output_path)
    else:
        print("❌ 추출 실패")

def show_coordinate_guide(image_path):
    """이미지에 좌표 가이드 표시"""
    try:
        img = cv2.imread(image_path)
        height, width = img.shape[:2]
        
        print(f"\n📐 이미지 정보:")
        print(f"   크기: {width} x {height}")
        print(f"   비율: {width/height:.3f}")
        
        # 격자 그리기
        grid_img = img.copy()
        
        # 10등분 격자
        for i in range(1, 10):
            x = int(width * i / 10)
            y = int(height * i / 10)
            
            # 세로선
            cv2.line(grid_img, (x, 0), (x, height), (0, 255, 255), 1)
            # 가로선  
            cv2.line(grid_img, (0, y), (width, y), (0, 255, 255), 1)
            
            # 좌표 표시
            if i % 2 == 0:  # 짝수만 표시
                cv2.putText(grid_img, f"{i/10:.1f}", (x-15, 20), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                cv2.putText(grid_img, f"{i/10:.1f}", (5, y+5), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        
        # 격자 이미지 저장
        grid_output = image_path.replace('.jpg', '_grid.jpg')
        cv2.imwrite(grid_output, grid_img)
        print(f"📊 격자 이미지 저장: {grid_output}")
        
        # 현재 PARKING_ZONES_NORM 좌표를 이미지에 표시
        draw_current_zones(img, width, height)
        
    except Exception as e:
        print(f"❌ 가이드 생성 오류: {e}")

def draw_current_zones(img, width, height):
    """현재 설정된 구역들을 이미지에 표시"""
    # 현재 사용중인 좌표 (수정된 것)
    PARKING_ZONES_NORM = [
        [0.0500, 0.0500, 0.2000, 0.3500],  # B1 (위쪽)
        [0.2100, 0.0500, 0.3600, 0.3500],  # B2
        [0.3700, 0.0500, 0.5200, 0.3500],  # B3
        [0.5300, 0.0500, 0.6800, 0.3500],  # B4
        [0.6900, 0.0500, 0.8400, 0.3500],  # B5
        [0.1000, 0.4000, 0.2500, 0.7000],  # C1 (중간)
        [0.2600, 0.4000, 0.4100, 0.7000],  # C2
        [0.4200, 0.4000, 0.5700, 0.7000],  # C3
        [0.5800, 0.4000, 0.7300, 0.7000],  # C4
        [0.1500, 0.7500, 0.3000, 0.9500],  # A1 (아래쪽)
        [0.3100, 0.7500, 0.4600, 0.9500],  # A2
        [0.4700, 0.7500, 0.6200, 0.9500],  # A3
        [0.6300, 0.7500, 0.7800, 0.9500],  # A4
        [0.7900, 0.7500, 0.9400, 0.9500],  # A5
    ]
    
    zone_names = ['B1', 'B2', 'B3', 'B4', 'B5', 'C1', 'C2', 'C3', 'C4', 'A1', 'A2', 'A3', 'A4', 'A5']
    colors = [(0, 255, 0), (255, 0, 0), (0, 0, 255)]  # B-녹색, C-파랑, A-빨강
    
    zones_img = img.copy()
    
    for i, (zone, name) in enumerate(zip(PARKING_ZONES_NORM, zone_names)):
        x1, y1, x2, y2 = zone
        
        # 정규화된 좌표를 절대 좌표로 변환
        x1_abs = int(x1 * width)
        y1_abs = int(y1 * height)
        x2_abs = int(x2 * width)
        y2_abs = int(y2 * height)
        
        # 색상 선택 (A-빨강, B-녹색, C-파랑)
        if name.startswith('A'):
            color = (0, 0, 255)  # 빨강
        elif name.startswith('B'):
            color = (0, 255, 0)  # 녹색
        else:  # C
            color = (255, 0, 0)  # 파랑
        
        # 사각형 그리기
        cv2.rectangle(zones_img, (x1_abs, y1_abs), (x2_abs, y2_abs), color, 2)
        
        # 구역 이름 표시
        center_x = (x1_abs + x2_abs) // 2
        center_y = (y1_abs + y2_abs) // 2
        cv2.putText(zones_img, name, (center_x-15, center_y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        print(f"📍 {name}: ({x1:.3f}, {y1:.3f}, {x2:.3f}, {y2:.3f}) -> ({x1_abs}, {y1_abs}, {x2_abs}, {y2_abs})")
    
    # 구역 표시 이미지 저장
    zones_output = "angle_with_zones.jpg"
    cv2.imwrite(zones_output, zones_img)
    print(f"🎯 구역 표시 이미지 저장: {zones_output}")

if __name__ == "__main__":
    main()
