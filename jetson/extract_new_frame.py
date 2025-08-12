#!/usr/bin/env python3
"""
new.mp4에서 첫 번째 프레임을 추출하는 스크립트
"""

import cv2
import os

def extract_first_frame():
    video_path = 'new.mp4'
    output_path = 'new_first_frame.jpg'
    
    print(f"🎬 비디오 파일 확인: {video_path}")
    
    if not os.path.exists(video_path):
        print(f"❌ 비디오 파일이 없습니다: {video_path}")
        return False
    
    try:
        # 비디오 캡처 객체 생성
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            print("❌ 비디오 파일을 열 수 없습니다")
            return False
        
        print("✅ 비디오 파일 열기 성공")
        
        # 첫 번째 프레임 읽기
        ret, frame = cap.read()
        
        if not ret:
            print("❌ 프레임을 읽을 수 없습니다")
            cap.release()
            return False
        
        print(f"✅ 프레임 읽기 성공 - 크기: {frame.shape[1]} x {frame.shape[0]}")
        
        # 이미지 저장
        success = cv2.imwrite(output_path, frame)
        
        if success:
            print(f"✅ 첫 번째 프레임 저장 완료: {output_path}")
        else:
            print("❌ 이미지 저장 실패")
        
        cap.release()
        return success
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False

if __name__ == "__main__":
    extract_first_frame()
