import cv2
from ultralytics import YOLO
import os

def process_video():
    # 모델 로드
    model = YOLO("best.pt")
    
    # 영상 처리
    print("영상 처리 시작...")
    
    # ByteTrack 추적 기능과 함께 YOLO의 내장 비디오 처리 기능 사용
    results = model.track(
        source="sample.mp4", 
        save=True, 
        project=".", 
        name="output", 
        conf=0.3,
        tracker="bytetrack.yaml",  # ByteTrack 추적기 사용
        persist=True,  # 추적 ID 유지
        show_labels=True,  # 라벨 표시
        show_conf=True,  # 신뢰도 표시
        line_width=2,  # 선 두께 (line_thickness 대신 line_width 사용)
        verbose=True  # 상세한 출력
    )
    
    print("처리 완료!")
    print("결과 영상: ./output/sample.mp4")
    print("ByteTrack 추적이 적용된 영상이 생성되었습니다.")

if __name__ == "__main__":
    process_video() 