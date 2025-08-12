#!/usr/bin/env python3
"""
JSON 좌표를 parking_check_copy.py 형식으로 변환
"""

import json

def convert_zones():
    """JSON 구역 데이터를 parking_check_copy.py 형식으로 변환"""
    
    # JSON 데이터 (사용자가 제공한 것)
    zones_data = {
        "zones": {
            "A1": [[658, 760], [807, 758], [807, 1031], [675, 1033]],
            "A2": [[823, 762], [962, 768], [950, 1027], [817, 1027]],
            "A3": [[958, 759], [1089, 762], [1099, 1031], [958, 1024]],
            "A4": [[1151, 769], [1286, 768], [1281, 1027], [1156, 1024]],
            "A5": [[1290, 765], [1413, 762], [1423, 1027], [1287, 1021]],
            "B1": [[686, 9], [814, 13], [817, 251], [686, 249]],
            "B2": [[829, 18], [956, 18], [966, 266], [819, 261]],
            "B3": [[968, 18], [1085, 31], [1089, 277], [969, 256]],
            "C1": [[1153, 32], [1271, 34], [1284, 250], [1148, 243]],
            "C2": [[1284, 41], [1402, 40], [1418, 257], [1288, 243]],
            "C3": [[1404, 49], [1529, 37], [1541, 240], [1408, 238]]
        },
        "image_info": {
            "width": 1656,
            "height": 1044
        }
    }
    
    width = zones_data["image_info"]["width"]
    height = zones_data["image_info"]["height"]
    
    print(f"이미지 크기: {width} x {height}")
    print("\n변환된 PARKING_ZONES_NORM:")
    print("="*60)
    
    # parking_check_copy.py 형식으로 변환
    result = "PARKING_ZONES_NORM = [\n"
    
    # 순서: B1-B3, C1-C3, A1-A5
    zone_order = ['B1', 'B2', 'B3', 'C1', 'C2', 'C3', 'A1', 'A2', 'A3', 'A4', 'A5']
    
    for zone_name in zone_order:
        if zone_name in zones_data["zones"]:
            points = zones_data["zones"][zone_name]
            
            # bbox 계산 (x1, y1, x2, y2)
            x_coords = [p[0] for p in points]
            y_coords = [p[1] for p in points]
            
            x1 = min(x_coords) / width
            y1 = min(y_coords) / height
            x2 = max(x_coords) / width
            y2 = max(y_coords) / height
            
            zone_id = zone_name.lower()
            
            result += "    {\n"
            result += f'        "id": "{zone_id}",\n'
            result += f'        "rect": [{x1:.6f}, {y1:.6f}, {x2:.6f}, {y2:.6f}]\n'
            result += "    },\n"
            
            print(f"{zone_name}: [{x1:.6f}, {y1:.6f}, {x2:.6f}, {y2:.6f}]")
    
    result = result.rstrip(',\n') + "\n]"
    
    print("\n완성된 코드:")
    print("="*60)
    print(result)
    
    return result

if __name__ == "__main__":
    convert_zones()
