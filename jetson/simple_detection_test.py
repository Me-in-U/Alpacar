#!/usr/bin/env python3
"""
간단한 차량 검출 테스트
"""

import cv2
import numpy as np
from ultralytics import YOLO

def test_vehicle_detection():
    """차량 검출 테스트"""
    print("🚗 차량 검출 테스트 시작")
    
    # YOLO 모델 로드
    model = YOLO("best.pt")
    
    # 테스트할 이미지들
    test_images = ["car.jpg", "car_analysis_result.jpg"]
    
    for image_path in test_images:
        print(f"\n🔍 처리 중: {image_path}")
        
        try:
            # 이미지 로드
            frame = cv2.imread(image_path)
            if frame is None:
                print(f"❌ 이미지를 읽을 수 없습니다: {image_path}")
                continue
            
            print(f"📐 이미지 크기: {frame.shape[1]}x{frame.shape[0]}")
            
            # YOLO 검출 (confidence threshold를 매우 낮게)
            results = model(frame, conf=0.01, verbose=True)
            
            if results[0].boxes is not None:
                boxes = results[0].boxes.xyxy.cpu().numpy()
                confidences = results[0].boxes.conf.cpu().numpy()
                classes = results[0].boxes.cls.cpu().numpy().astype(int)
                
                print(f"📊 총 검출된 객체 수: {len(boxes)}")
                
                # 클래스별 검출 결과
                class_counts = {}
                for cls in classes:
                    class_counts[cls] = class_counts.get(cls, 0) + 1
                
                print(f"📋 클래스별 검출 수: {class_counts}")
                
                # 각 검출 결과 상세 정보
                for i, (box, conf, cls) in enumerate(zip(boxes, confidences, classes)):
                    x1, y1, x2, y2 = box
                    print(f"   객체 {i+1}: 클래스={cls}, 신뢰도={conf:.3f}, 박스=({x1:.0f},{y1:.0f},{x2:.0f},{y2:.0f})")
                
                # 결과 이미지에 박스 그리기
                result_frame = frame.copy()
                for i, (box, conf, cls) in enumerate(zip(boxes, confidences, classes)):
                    x1, y1, x2, y2 = box
                    
                    # 클래스에 따른 색상
                    if cls == 0:  # 차량 (보통 클래스 0)
                        color = (0, 255, 0)  # 초록
                        label = f"Vehicle {conf:.2f}"
                    else:
                        color = (255, 0, 0)  # 파랑
                        label = f"Class{cls} {conf:.2f}"
                    
                    cv2.rectangle(result_frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
                    cv2.putText(result_frame, label, (int(x1), int(y1) - 10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                
                # 결과 저장
                result_path = image_path.replace('.', '_detection.')
                cv2.imwrite(result_path, result_frame)
                print(f"💾 결과 저장: {result_path}")
                
            else:
                print("❌ 검출된 객체가 없습니다")
                
        except Exception as e:
            print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    test_vehicle_detection()
