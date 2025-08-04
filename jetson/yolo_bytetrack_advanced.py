import cv2
from ultralytics import YOLO
import os
import time

def process_video_with_bytetrack():
    # 모델 로드
    model = YOLO("best.pt")
    
    print("ByteTrack 추적 기능과 함께 영상 처리 시작...")
    
    # 고급 ByteTrack 설정 (유효한 매개변수만 사용)
    results = model.track(
        source="sample.mp4", 
        save=True, 
        project=".", 
        name="output_bytetrack", 
        conf=0.5,
        iou=0.7,  # IoU 임계값
        tracker="bytetrack.yaml",  # ByteTrack 추적기
        persist=True,  # 추적 ID 유지
        show_labels=True,  # 라벨 표시
        show_conf=True,  # 신뢰도 표시
        line_width=3,  # 선 두께
        verbose=True  # 상세한 출력
    )
    
    print("ByteTrack 추적 처리 완료!")
    print("결과 영상: ./output_bytetrack/sample.mp4")
    
    # 추적 통계 출력
    if results:
        print(f"처리된 프레임 수: {len(results)}")
        for i, result in enumerate(results):
            if hasattr(result, 'boxes') and result.boxes is not None:
                if hasattr(result.boxes, 'id') and result.boxes.id is not None:
                    track_ids = result.boxes.id.cpu().numpy()
                    print(f"프레임 {i+1}: {len(track_ids)}개 객체 추적됨 (ID: {track_ids})")

def process_video_with_custom_tracking():
    """사용자 정의 추적 설정으로 영상 처리"""
    model = YOLO("best.pt")
    
    print("사용자 정의 ByteTrack 설정으로 영상 처리...")
    
    # 사용자 정의 추적 설정 (유효한 매개변수만 사용)
    custom_results = model.track(
        source="sample.mp4", 
        save=True, 
        project=".", 
        name="output_custom", 
        conf=0.3,  # 더 낮은 신뢰도로 더 많은 객체 검출
        iou=0.5,   # 더 낮은 IoU 임계값
        tracker="bytetrack.yaml",
        persist=True,
        show_labels=True,
        show_conf=True,
        line_width=2,
        verbose=False
    )
    
    print("사용자 정의 추적 처리 완료!")
    print("결과 영상: ./output_custom/sample.mp4")

if __name__ == "__main__":
    print("=== ByteTrack 추적 기능이 포함된 YOLO 영상 처리 ===")
    
    # 기본 ByteTrack 처리
    process_video_with_bytetrack()
    
    print("\n" + "="*50 + "\n")
    
    # 사용자 정의 설정으로 처리
    process_video_with_custom_tracking()
    
    print("\n모든 처리 완료!")
    print("생성된 파일들:")
    print("- ./output_bytetrack/sample.mp4 (기본 ByteTrack)")
    print("- ./output_custom/sample.mp4 (사용자 정의 설정)") 