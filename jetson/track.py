import cv2
from ultralytics import YOLO

# 모델 로드 (예: obb 모델 가중치 사용)
model = YOLO('best (6).pt')  # 적절한 OBB 모델 가중치 경로 사용

# 카메라 열기
cap = cv2.VideoCapture(1)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # YOLO OBB 추론
    results = model(frame)

    # 결과에서 OBB 박스 꺼내서 그리기
    for r in results:
        if hasattr(results, "obb") and results.obb is not None:
            obb_boxes = results.obb.xywhn  # 모델 및 버전에 따라 xywhn, xyxy, polys 등 사용
            for box in obb_boxes:
                if len(box) >= 7:
                    cx, cy, w, h, angle, conf, cls = box[:7]
        for box in obb_boxes:
            # box: [cx, cy, w, h, angle, conf, cls]
            cx, cy, w, h, angle = box[:5]
            conf, cls = box[5], int(box[6])

            # OBB를 폴리곤(점 4개)으로 변환해서 그리기
            poly = r.obb2poly(box[:5])  # ultralytics 함수
            pts = poly.reshape(-1, 1, 2).astype(int)
            cv2.polylines(frame, [pts], isClosed=True, color=(0,255,0), thickness=2)

            # 클래스 이름, 확률 표시
            label = f"{model.names[cls]} {conf:.2f}"
            cv2.putText(frame, label, (int(cx), int(cy)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)

    cv2.imshow('YOLO OBB Real-time', frame)
    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
