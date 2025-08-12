# 차량 길이 매핑 테이블 (임시용)
VEHICLE_LENGTH_MAPPING = {
    # 번호판 패턴별 차량 길이 (mm)
    # 실제로는 OCR 결과나 차량 클래스로 매핑
    
    # 소형차 (4.2m - 4.5m)
    "소형": 4200,
    "compact": 4200,
    "small": 4200,
    
    # 중형차 (4.5m - 4.8m) 
    "중형": 4650,
    "midsize": 4650,
    "sedan": 4650,
    
    # 대형차 (4.8m - 5.2m)
    "대형": 4900,
    "large": 4900,
    "luxury": 4900,
    
    # SUV (4.6m - 5.0m)
    "SUV": 4750,
    "suv": 4750,
    
    # 기본값
    "default": 4500
}


def get_vehicle_length_by_type(vehicle_type: str) -> int:
    """차량 타입별 길이 반환"""
    return VEHICLE_LENGTH_MAPPING.get(vehicle_type.lower(), VEHICLE_LENGTH_MAPPING["default"])


def get_vehicle_length_by_plate(license_plate: str) -> int:
    """번호판으로 차량 길이 추정 (임시 로직)"""
    
    # 번호판 패턴 분석 (예시)
    if not license_plate or license_plate == "Unknown":
        return VEHICLE_LENGTH_MAPPING["default"]
    
    # 간단한 규칙 기반 분류 (실제로는 더 정교한 로직 필요)
    plate_lower = license_plate.lower()
    
    # 예시: 특정 패턴으로 차량 크기 추정
    if any(x in plate_lower for x in ["suv", "sports"]):
        return VEHICLE_LENGTH_MAPPING["SUV"]
    elif any(x in plate_lower for x in ["compact", "mini"]):
        return VEHICLE_LENGTH_MAPPING["소형"]
    elif any(x in plate_lower for x in ["luxury", "premium"]):
        return VEHICLE_LENGTH_MAPPING["대형"]
    else:
        return VEHICLE_LENGTH_MAPPING["중형"]


# 차종별 임시 데이터베이스 (OCR 없이 테스트용)
TEMP_VEHICLE_DATABASE = {
    "123가4567": {"type": "중형", "brand": "기아", "model": "모닝", "length": 3595},   # 모닝 약 3.6m
    "456나7890": {"type": "중형", "brand": "기아", "model": "K5", "length": 4905},
    "789다1234": {"type": "중형", "brand": "기아", "model": "K8", "length": 4995},
    "321라5678": {"type": "소형", "brand": "현대", "model": "아반떼", "length": 4670},
    "654마9012": {"type": "중형", "brand": "기아", "model": "K5", "length": 4905},  # 중복 제거 가능
}


def get_vehicle_info_from_temp_db(license_plate: str) -> dict:
    """임시 데이터베이스에서 차량 정보 조회"""
    return TEMP_VEHICLE_DATABASE.get(license_plate, {
        "type": "중형",
        "brand": "Unknown",
        "model": "Unknown", 
        "length": 4500
    })
