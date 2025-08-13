from ultralytics import YOLO
import cv2
import numpy as np
import matplotlib.pyplot as plt

# 모델 로드
model = YOLO("last.pt")
# model = YOLO("yolo11n-obb.pt")

# 이미지 불러오기 (BGR->RGB 변환)
img_path = "WIN_20250808_17_42_28_Pro.jpg"
img = cv2.imread(img_path)
img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
# img = cv2.convertScaleAbs(img, alpha=1.5)

# 겹침 완화: 낮은 conf 후보 제거 + NMS 강하게
results = model(
    img,
    conf=0.01,   # 0.3~0.5 권장
    iou=0.3,     # 0.4~0.6 권장
    agnostic_nms=True,
    augment=True,
    imgsz=(640, 640)
)

# 단일 이미지 결과 사용
result = results[0]
names = result.names

# obb 박스, confidence, 클래스
obb = result.obb

if obb is not None and hasattr(obb, 'xyxyxyxy'):
    polys = obb.xyxyxyxy.cpu().numpy() if hasattr(obb.xyxyxyxy, 'cpu') else obb.xyxyxyxy
    confs = obb.conf.cpu().numpy() if hasattr(obb.conf, 'cpu') else obb.conf
    clss = obb.cls.cpu().numpy() if hasattr(obb.cls, 'cpu') else obb.cls

    for i, poly in enumerate(polys):
        pts = poly.reshape(4, 2).astype(np.int32)
        
        # 4개의 선을 각각 다른 색으로 그리기
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]  # 빨강, 초록, 파랑, 노랑
        
        for j in range(4):
            # 현재 점과 다음 점을 연결하는 선 그리기
            pt1 = tuple(pts[j])
            pt2 = tuple(pts[(j + 1) % 4])  # 마지막 점은 첫 번째 점과 연결
            cv2.line(img, pt1, pt2, colors[j], thickness=2)

        # cv point 그리기
        cv2.circle(img, np.mean(pts, axis=0).astype(np.int32), 5, (0, 255, 0), -1)

        # pt 짝별 라인길이 (pt1, pt2), (pt2, pt3), (pt3, pt4), (pt4, pt1)
        line_lengths = [
            np.linalg.norm(pts[j] - pts[(j + 1) % 4])
            for j in range(4)
        ]
        # 짝별 벡터
        vectors = [
            pts[(j + 1) % 4] - pts[j]
            for j in range(4)
        ]
        
        center = np.mean(pts, axis=0).astype(np.int32)
        line1 = np.array(pts[0]) - np.array(pts[1])
        vector = np.array(line1)
        vector_from_center = np.array(line1)
        cv2.arrowedLine(img, center, center + vector, (0, 0, 255), thickness=2)

        line2 = np.array(pts[1]) - np.array(pts[2])
        vector = np.array(line2)
        vector_from_center = np.array(line2)
        cv2.arrowedLine(img, center, center + vector, (0, 255, 255), thickness=2)

        class_id = int(clss[i])
        label = f"{names[class_id]}: {confs[i]:.2f}"
        x, y = pts[0]
        cv2.putText(img, label, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,0,0), 2)
else:
    print("OBB 예측 결과가 없습니다.")

plt.figure(figsize=(10,10))
plt.imshow(img)
plt.axis('off')
plt.tight_layout()
plt.savefig('result_vis.png')
plt.show()
