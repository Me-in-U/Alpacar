"""
빈 주차구역 후보들에 대해 이동/접근 소요시간(또는 점수)을 예측하고, 가장 빠른/좋은 구역을 추천하는 모듈.

가정
- 입력 특성(features)은 모델 학습 시점과 동일한 스키마를 따른다.
- 예측 대상은 'step' 또는 'duration' 같은 연속값(낮을수록 좋음).

사용 예시
from ml.step_predictor import load_model
from ml.recommender import recommend_best_zone

model = load_model('artifacts/best_step_model.joblib')
features_per_zone = [
    {'zone_id': 'a1', 'distance_m': 35.0, 'dow': 2, 'hour': 14, ...},
    {'zone_id': 'a3', 'distance_m': 28.0, 'dow': 2, 'hour': 14, ...},
]
best = recommend_best_zone(model, features_per_zone)
print(best)  # {'zone_id': 'a3', 'pred': 12.3, 'rank': 1}
"""

from __future__ import annotations

from typing import Dict, List, Optional
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline

# 예측 피처 명세: 각 항목은 이름/설명/출처/현재 가용 여부/기본값을 포함한다.
# - available_now=True: 현재 저장소 코드만으로 합리적으로 생성 가능
# - available_now=False: 추가 구현/지도 데이터/이력 데이터가 필요 [추가 구현 필요]
FEATURE_SPEC: List[Dict] = [
    # 기본/시간 정보 (현재 가능)
    {
        "name": "hour",
        "desc": "현지 시각 시(hour)",
        "source": "temporal",
        "available_now": True,
        "default": 12,
    },
    {
        "name": "dow",
        "desc": "요일(0=월 ~ 6=일)",
        "source": "temporal",
        "available_now": True,
        "default": 2,
    },
    {
        "name": "size_class",
        "desc": "차량 크기 분류(예: small/medium/large). 서버 요청에 포함됨",
        "source": "request",
        "available_now": True,
        "default": "unknown",
    },

    # 좌/우 인접 차량 및 구조물 특성 (추정용 지도/검출 로직 필요) [추가 구현 필요]
    {"name": "left_occupied",  "desc": "좌측 칸 점유 여부",           "source": "neighbor",  "available_now": False, "default": 0},
    {"name": "left_angle",     "desc": "좌측 차량 각도(rad)",        "source": "neighbor",  "available_now": False, "default": 0.0},
    {"name": "left_offset",    "desc": "좌측 차량 중심 오프셋",      "source": "neighbor",  "available_now": False, "default": 0.0},
    {"name": "left_size",      "desc": "좌측 차량 크기 클래스",      "source": "neighbor",  "available_now": False, "default": 2},
    {"name": "left_width",     "desc": "좌측 차량 폭(m)",            "source": "neighbor",  "available_now": False, "default": 2.5},
    {"name": "left_length",    "desc": "좌측 차량 길이(m)",          "source": "neighbor",  "available_now": False, "default": 5.0},
    {"name": "left_has_pillar", "desc": "좌측 기둥/장애물 존재 여부",  "source": "geometry",  "available_now": False, "default": 0},
    {"name": "right_occupied", "desc": "우측 칸 점유 여부",          "source": "neighbor",  "available_now": False, "default": 0},
    {"name": "right_angle",    "desc": "우측 차량 각도(rad)",        "source": "neighbor",  "available_now": False, "default": 0.0},
    {"name": "right_offset",   "desc": "우측 차량 중심 오프셋",      "source": "neighbor",  "available_now": False, "default": 0.0},
    {"name": "right_size",     "desc": "우측 차량 크기 클래스",      "source": "neighbor",  "available_now": False, "default": 2},
    {"name": "right_width",    "desc": "우측 차량 폭(m)",            "source": "neighbor",  "available_now": False, "default": 2.5},
    {"name": "right_length",   "desc": "우측 차량 길이(m)",          "source": "neighbor",  "available_now": False, "default": 5.0},
    {"name": "right_has_pillar","desc": "우측 기둥/장애물 존재 여부",  "source": "geometry",  "available_now": False, "default": 0},

    # 목표/구역 좌표 및 치수 (정밀 지도 또는 사전 정의 필요) [추가 구현 필요]
    {"name": "controlled_x",      "desc": "통제 차량의 x 좌표",     "source": "geometry",  "available_now": False, "default": 0.0},
    {"name": "controlled_y",      "desc": "통제 차량의 y 좌표",     "source": "geometry",  "available_now": False, "default": 0.0},
    {"name": "controlled_width",  "desc": "통제 차량 폭",           "source": "geometry",  "available_now": False, "default": 2.5},
    {"name": "controlled_length", "desc": "통제 차량 길이",         "source": "geometry",  "available_now": False, "default": 5.0},

    # 거리/접근성 특성 (동선 추정 필요) [추가 구현 필요]
    {"name": "distance_m",  "desc": "현재 위치→구역까지 예상 이동거리(m)", "source": "routing", "available_now": False, "default": 30.0},
    {"name": "heading_diff","desc": "현재 진행 방향과 구역 진입 각도 차(rad)", "source": "routing", "available_now": False, "default": 0.0},
]

def get_feature_spec() -> List[Dict]:
    """피처 명세 반환. available_now=False 항목은 [추가 구현 필요]."""
    return FEATURE_SPEC


def predict_per_zone(model: Pipeline, features_per_zone: List[Dict]) -> List[Dict]:
    """
    각 구역별 feature dict를 받아 모델로 예측값을 생성한다.
    입력:
      - features_per_zone: [{ 'zone_id': str, <feature...> }]
        권장 피처(샘플):
          - hour, dow, size_class  (현재 코드만으로 산출 가능)
          - left/right_* , controlled_* , distance_m , heading_diff  [추가 구현 필요]

    반환: [{ 'zone_id': str, 'pred': float, 'features': Dict }, ...]
    """
    # feature_cols = [
    #     "left_occupied","left_angle","left_offset","left_size","left_width","left_length","left_has_pillar",
    #     "right_occupied","right_angle","right_offset","right_size","right_width","right_length","right_has_pillar",
    #     "controlled_x","controlled_y","controlled_width","controlled_length"
    # ]
    if not features_per_zone:
        return []
    df = pd.DataFrame(features_per_zone)
    if 'zone_id' not in df.columns:
        raise ValueError('features_per_zone의 각 항목에 zone_id 키가 필요합니다.')
    zone_ids = df['zone_id'].tolist()
    X = df.drop(columns=['zone_id'])
    preds = model.predict(X)
    results = []
    for zid, p, feats in zip(zone_ids, preds, X.to_dict(orient='records')):
        results.append({'zone_id': zid, 'pred': float(p), 'features': feats})
    return results

def recommend_best_zone(model: Pipeline, features_per_zone: List[Dict]) -> Optional[List[Dict]]:
    """
    각 주차구역별 예측 step 값을 반환한다.
    반환: [{ 'zone_id': str, 'step': float, 'rank': int, 'features': Dict }, ...]
    """
    preds = predict_per_zone(model, features_per_zone)
    if not preds:
        return None
    # 'pred'를 'step'으로 이름 변경
    for item in preds:
        item['step'] = item.pop('pred')
    preds_sorted = sorted(preds, key=lambda x: x['step'])
    return preds_sorted
