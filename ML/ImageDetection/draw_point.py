import cv2
import numpy as np
import os
from datetime import datetime
import json
import ctypes


# 사각형 드로잉 상태 변수들
drawing_rect = False
start_point = (0, 0)
current_point = (0, 0)
rectangles = []  # (x1, y1, x2, y2) in display(view) coordinates
scale = 1.0  # view scale relative to original image
view_image = None  # downscaled image for display


def draw_all_rectangles(base_image, rect_list, preview_rect=None):
    """기존 사각형과 미리보기 사각형을 모두 그려 반환"""
    canvas = base_image.copy()
    # 기존 박스들
    for (x1, y1, x2, y2) in rect_list:
        cv2.rectangle(canvas, (x1, y1), (x2, y2), (0, 0, 255), 2)
    # 미리보기 박스(드래그 중)
    if preview_rect is not None:
        (px1, py1, px2, py2) = preview_rect
        cv2.rectangle(canvas, (px1, py1), (px2, py2), (0, 255, 255), 1)
    # 헬프 텍스트
    help_lines = [
        "L-Drag: Draw rectangle | L-Release: Confirm",
        "d: Undo last box | c: Clear all",
        "s: Save | q or ESC: Quit",
    ]
    y0 = 22
    for line in help_lines:
        cv2.putText(canvas, line, (10, y0), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (50, 200, 50), 2, cv2.LINE_AA)
        y0 += 24
    return canvas


def normalize_rect(p1, p2):
    x1, y1 = p1
    x2, y2 = p2
    return (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))


def mouse_callback(event, x, y, flags, param):
    global drawing_rect, start_point, current_point, display_image, rectangles, view_image

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing_rect = True
        start_point = (x, y)
        current_point = (x, y)

    elif event == cv2.EVENT_MOUSEMOVE and drawing_rect:
        current_point = (x, y)
        preview = normalize_rect(start_point, current_point)
        display_image = draw_all_rectangles(view_image, rectangles, preview_rect=preview)

    elif event == cv2.EVENT_LBUTTONUP:
        if drawing_rect:
            drawing_rect = False
            current_point = (x, y)
            x1, y1, x2, y2 = normalize_rect(start_point, current_point)
            rectangles.append((x1, y1, x2, y2))
            print(f"Rect: ({x1}, {y1}) -> ({x2}, {y2})")
            display_image = draw_all_rectangles(view_image, rectangles)


# 이미지 로드
img_path = "WIN_20250816_23_55_49_Pro.jpg"
base_image = cv2.imread(img_path)
if base_image is None:
    raise FileNotFoundError(f"Image not found: {os.path.abspath(img_path)}")

# 화면 크기에 맞춰 표시용 이미지(view) 자동 축소
img_h, img_w = base_image.shape[:2]
try:
    screen_w = ctypes.windll.user32.GetSystemMetrics(0)
    screen_h = ctypes.windll.user32.GetSystemMetrics(1)
    max_w = int(screen_w * 0.9)
    max_h = int(screen_h * 0.9)
except Exception:
    # 기본값 (대부분 환경에서 무난한 크기)
    max_w, max_h = 1280, 720

scale_w = max_w / img_w
scale_h = max_h / img_h
scale = min(scale_w, scale_h, 1.0)

if scale < 1.0:
    view_w = max(1, int(img_w * scale))
    view_h = max(1, int(img_h * scale))
    view_image = cv2.resize(base_image, (view_w, view_h), interpolation=cv2.INTER_AREA)
else:
    view_image = base_image.copy()
    view_h, view_w = view_image.shape[:2]

display_image = view_image.copy()

cv2.namedWindow('image', cv2.WINDOW_NORMAL)
cv2.resizeWindow('image', view_w, view_h)
cv2.setMouseCallback('image', mouse_callback)

while True:
    cv2.imshow('image', display_image)
    key = cv2.waitKey(1) & 0xFF

    if key == ord('q') or key == 27:  # q 또는 ESC로 종료
        break
    elif key == ord('c'):  # 초기화
        rectangles = []
        display_image = draw_all_rectangles(view_image, rectangles)
    elif key == ord('d'):  # 마지막 박스 삭제
        if rectangles:
            rectangles.pop()
            display_image = draw_all_rectangles(view_image, rectangles)
    elif key == ord('s'):  # save
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        save_name = f"rect_{timestamp}.json"
        # save rectangles as normalized ratios [0,1]
        height, width = base_image.shape[:2]
        rect_list = []
        # rectangles 좌표는 표시용(view) 기준. 저장은 원본 기준 정규화로 변환
        for rect in rectangles:
            x1, y1, x2, y2 = rect
            # view -> original 좌표 변환 후 정규화: (x/scale)/width == x/(width*scale)
            rect_list.append({
                "x1": round(x1 / (width * scale), 6),
                "y1": round(y1 / (height * scale), 6),
                "x2": round(x2 / (width * scale), 6),
                "y2": round(y2 / (height * scale), 6)
            })
        with open(save_name, "w", encoding="utf-8") as f:
            json.dump(rect_list, f, ensure_ascii=False, indent=2)
        print(f"Saved normalized rects (0-1) to JSON: {save_name}")

cv2.destroyAllWindows()