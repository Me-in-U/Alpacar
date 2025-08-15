from __future__ import annotations

import numpy as np
import pandas as pd
import joblib
from pathlib import Path

import logging

logger = logging.getLogger("recommender")

_ARTIFACTS_DIR = (Path(__file__).resolve().parent / "artifacts")

def _load_model(filename: str):
    path_primary = _ARTIFACTS_DIR / filename
    path_fallback = Path("ml") / "artifacts" / filename
    
    logger.info(f"[ModelLoader] 모델 파일 검색 중: {filename}")
    logger.info(f"[ModelLoader] Primary 경로: {path_primary}")
    logger.info(f"[ModelLoader] Fallback 경로: {path_fallback}")
    
    if not path_primary.exists():
        logger.warning(f"[ModelLoader] Primary 경로에 파일이 없습니다: {path_primary}")
    if not path_fallback.exists():
        logger.warning(f"[ModelLoader] Fallback 경로에 파일이 없습니다: {path_fallback}")
    
    try:
        logger.info(f"[ModelLoader] {filename} 모델을 불러오는 중입니다... (primary: {path_primary})")
        model = joblib.load(path_primary)
        logger.info(f"[ModelLoader] {filename} 모델 불러오기 완료 (primary)")
        return model
    except Exception as e_primary:
        logger.warning(f"[ModelLoader] Primary 경로 로드 실패: {e_primary}")
        logger.info(f"[ModelLoader] Fallback 시도: {path_fallback}")
        try:
            model = joblib.load(path_fallback)
            logger.info(f"[ModelLoader] {filename} 모델 불러오기 완료 (fallback)")
            return model
        except Exception as e_fallback:
            logger.error(f"[ModelLoader] Fallback 경로 로드도 실패: {e_fallback}")
            logger.error(f"[ModelLoader] 모델 파일을 찾을 수 없습니다: {filename}")
            raise RuntimeError(f"모델 파일을 로드할 수 없습니다: {filename}. Primary: {e_primary}, Fallback: {e_fallback}")

step_predict_model = _load_model('rf_step_model.joblib')
score_predict_model = _load_model('rf_score_model.joblib')

def wrap_rad(a):
    return (a + np.pi) % (2*np.pi) - np.pi

def preprocess_features(features_per_zone):
    df = pd.DataFrame(features_per_zone).copy()
    
    df['tier_beginner'] = (df['agent_angle_tier'] == 'beginner').astype(int)
    df['tier_intermediate'] = (df['agent_angle_tier'] == 'intermediate').astype(int)

    feature_columns = [
        'left_occupied', 'left_size', 'left_width', 'left_length', 'left_has_pillar',
        'right_occupied', 'right_size', 'right_width', 'right_length', 'right_has_pillar',
        'controlled_width', 'controlled_length',
        'left_angle_deg', 'right_angle_deg',
        'tier_beginner', 'tier_intermediate'
    ]
    
    zone_ids = df['zone_id']
    
    X = pd.DataFrame()
    for col in feature_columns:
        if col in df.columns:
            X[col] = df[col]
        else:
            if col in ['left_occupied', 'right_occupied', 'left_has_pillar', 'right_has_pillar', 'tier_beginner', 'tier_intermediate']:
                X[col] = 0
            elif col in ['left_size', 'right_size']:
                X[col] = 0
            elif col in ['left_width', 'left_length', 'right_width', 'right_length', 'controlled_width', 'controlled_length']:
                X[col] = 0.0
            elif col in ['left_angle_deg', 'right_angle_deg']:
                X[col] = 0.0
            else:
                X[col] = 0.0
    
    return zone_ids, X

def predict_per_zone(features_per_zone):
    try:
        zone_ids, X = preprocess_features(features_per_zone)
        logger.debug(f"[Predictor] 전처리 완료. 구역 수: {len(zone_ids)}, 특성 수: {X.shape[1]}")
        
        step_preds = step_predict_model.predict(X)
        score_preds = score_predict_model.predict(X)
        
        logger.debug(f"[Predictor] 예측 완료. step_preds: {step_preds}, score_preds: {score_preds}")

        results = []
        for zid, sp, sc in zip(zone_ids, step_preds, score_preds):
            results.append({
                'zone_id': zid,
                'pred_step': float(sp),
                'pred_deg_score': float(sc)
            })
        return results
        
    except Exception as e:
        logger.error(f"[Predictor] 예측 과정에서 오류 발생: {e}")
        logger.exception("[Predictor] 상세 오류 정보:")
        return []


# def recommend_best_zone(features_per_zone, max_time=18.0):
#     try:
#         if not features_per_zone:
#             return []

#         preds = predict_per_zone(features_per_zone)
#         if not preds:
#             return []

#         # 안전한 보정 함수: 빠를수록 높은 점수(0~1), 18을 상한선으로 캡
#         def _time_score(t, max_time=max_time):
#             if t is None:
#                 return 0.0
#             try:
#                 t = float(t)
#             except (TypeError, ValueError):
#                 return 0.0
#             t = max(0.0, min(t, max_time))  # [0, max_time]로 클램프
#             return (max_time - t) / max_time  # 0(느림) ~ 1(빠름)

#         for p in preds:
#             t = p.get('pred_step')
#             time_norm = _time_score(t, max_time=max_time)  # 0~1

#             # 가중합: deg 0.6, 시간 0.4
#             p['time_norm'] = time_norm
#             p['score'] = 0.6 * p.get('pred_deg_score', 0.0) / 100 + 0.4 * time_norm

#             logger.info(
#                 f"[Recommender] zone_id={p.get('zone_id')}, "
#                 f"pred_step={t}, pred_deg_score={p.get('pred_deg_score', 0.0)}, "
#                 f"time_norm={time_norm:.3f}, score={p['score']:.3f}"
#             )

#         return sorted(preds, key=lambda x: x['time_norm'], reverse=True)

#     except Exception as e:
#         logger.exception("[Recommender] failed with error")
#         return []

def recommend_best_zone(features_per_zone, max_time=18.0):
    """
    보정 강화 버전
      - 보너스 가중/상한 상향
      - 점수 가중치에서 보너스 비중 확대
      - 동률/근접 시 쉬운 자리 우선 타이브레이커
    """
    # === 튜닝 상수(필요시 여기만 수정) ===
    EASE_LEFT_PILLAR      = 0.15   # 기존 0.10 → 0.15
    EASE_ANY_EMPTY_SIDE   = 0.15   # 기존 0.10 → 0.15
    EASE_BOTH_EMPTY       = 0.10   # 기존 0.05 → 0.10
    EASE_INTERMEDIATE     = 0.07   # 기존 0.05 → 0.07
    EASE_CLAMP_MAX        = 0.45   # 기존 0.30 → 0.45

    # 최종 점수 가중치(합 1.0 권장)
    W_DEG   = 0.40               # 기존 0.50 → 0.40
    W_TIME  = 0.30               # 기존 0.35 → 0.30
    W_EASE  = 0.30               # 기존 0.15 → 0.30

    # 점수 동률/근접일 때 쉬운 자리 우선 기준
    TIE_EPS = 1e-6               # 완전 동률
    NEAR_EPS = 0.02              # 점수 차이 0.02 이내면 쉬운 자리 우선

    try:
        if not features_per_zone:
            return []

        # zone_id -> 원시 피처 맵
        feat_map = {}
        for f in features_per_zone:
            zid = f.get('zone_id')
            if zid is None:
                continue
            feat_map[zid] = {
                'left_has_pillar': int(f.get('left_has_pillar', 0)),
                'left_occupied': int(f.get('left_occupied', 0)),
                'right_occupied': int(f.get('right_occupied', 0)),
                'tier_intermediate': int(
                    f.get('tier_intermediate', 1 if f.get('agent_angle_tier') == 'intermediate' else 0)
                ),
            }

        preds = predict_per_zone(features_per_zone)
        if not preds:
            return []

        def _time_score(t, max_time=max_time):
            if t is None:
                return 0.0
            try:
                t = float(t)
            except (TypeError, ValueError):
                return 0.0
            t = max(0.0, min(t, max_time))
            return (max_time - t) / max_time  # 0(느림)~1(빠름)

        results = []
        for p in preds:
            zid = p.get('zone_id')
            t = p.get('pred_step')
            deg = float(p.get('pred_deg_score', 0.0))
            time_norm = _time_score(t, max_time=max_time)

            fm = feat_map.get(zid, {})
            has_left_pillar = int(fm.get('left_has_pillar', 0)) == 1
            left_empty = int(fm.get('left_occupied', 0)) == 0
            right_empty = int(fm.get('right_occupied', 0)) == 0
            is_intermediate = int(fm.get('tier_intermediate', 0)) == 1

            # 강화된 보너스
            ease_bonus = 0.0
            if has_left_pillar:
                ease_bonus += EASE_LEFT_PILLAR
            if left_empty or right_empty:
                ease_bonus += EASE_ANY_EMPTY_SIDE
            if left_empty and right_empty:
                ease_bonus += EASE_BOTH_EMPTY
            if is_intermediate:
                ease_bonus += EASE_INTERMEDIATE
            ease_bonus = max(0.0, min(ease_bonus, EASE_CLAMP_MAX))

            base_difficulty = 1.0 - (deg / 100.0)
            difficulty = base_difficulty * (1.0 - ease_bonus)
            difficulty = max(0.0, min(difficulty, 1.0))

            # 보너스 비중을 높인 최종 점수
            score = W_DEG * (deg / 100.0) + W_TIME * time_norm + W_EASE * ease_bonus

            out = dict(p)
            out['time_norm'] = time_norm
            out['ease_bonus'] = ease_bonus
            out['difficulty'] = difficulty
            out['score'] = score
            results.append(out)

        # 기본 정렬: score 내림차순
        results.sort(key=lambda x: x['score'], reverse=True)

        # 근접 점수 타이브레이커: score 차이가 작으면 쉬운 자리(ease_bonus↑, difficulty↓)를 앞으로
        # 안정성을 위해 단순한 1패스 버블 조정
        n = len(results)
        for i in range(n - 1):
            a, b = results[i], results[i + 1]
            diff = a['score'] - b['score']
            if abs(diff) <= TIE_EPS:
                # 완전 동률: ease_bonus 큰 쪽, 같으면 time_norm 큰 쪽
                if (b['ease_bonus'], b['time_norm']) > (a['ease_bonus'], a['time_norm']):
                    results[i], results[i + 1] = b, a
            elif diff > 0 and diff <= NEAR_EPS:
                # a가 근소하게 앞설 때도, b가 훨씬 쉬우면 바꿔치기
                if (b['ease_bonus'] - a['ease_bonus'] >= 0.08) or (a['difficulty'] - b['difficulty'] >= 0.08):
                    results[i], results[i + 1] = b, a

        return results

    except Exception:
        logger.exception("[Recommender] failed with error")
        return []
