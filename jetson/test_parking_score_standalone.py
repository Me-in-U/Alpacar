from parking_check_copy import EnhancedVideoProcessor

def main():
    # 주차 감지 프로세서 초기화
    try:
        processor = EnhancedVideoProcessor("best.pt")
    except Exception as e:
        print(f"모델 로드 실패: {e}")
        print("best.pt 파일이 없으면 임시로 다른 파일명을 사용하거나 YOLO 기본 모델 사용")
        return
    
    print("=== car.mp4 영상 주차 점수 분석 ===")
    print("임시 차량 데이터베이스:")
    from parking_score_calculator import TEMP_VEHICLE_DATABASE
    for plate, info in TEMP_VEHICLE_DATABASE.items():
        print(f"  {plate}: {info['brand']} {info['model']} ({info['length']}mm)")
    
    print("\ncar.mp4 비디오 처리 시작...")
    
    # car.mp4 영상 분석
    try:
        processor.process_video_enhanced("car.mp4")  # ← 여기를 car.mp4로 변경
        print("car.mp4 분석 완료!")
    except Exception as e:
        print(f"car.mp4 처리 실패: {e}")
        print("파일 경로를 확인해주세요.")

if __name__ == "__main__":
    main()