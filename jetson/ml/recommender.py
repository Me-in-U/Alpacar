from __future__ import annotations

import numpy as np
import pandas as pd
import joblib
from pathlib import Path
import logging
import math

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
            raise RuntimeError(
                f"모델 파일을 로드할 수 없습니다: {filename}. Primary: {e_primary}, Fallback: {e_fallback}"
            )

step_predict_model = None
score_predict_model = None


def _ensure_models_loaded():
    global step_predict_model, score_predict_model
    if step_predict_model is None or score_predict_model is None:
        step_predict_model = _load_model("rf_step_model.joblib")
        score_predict_model = _load_model("rf_score_model.joblib")


def wrap_rad(a):
    return (a + np.pi) % (2 * np.pi) - np.pi


def preprocess_features(features_per_zone):
    df = pd.DataFrame(features_per_zone).copy()

    df["tier_beginner"] = (df["agent_angle_tier"] == "beginner").astype(int)
    df["tier_intermediate"] = (df["agent_angle_tier"] == "intermediate").astype(int)

    feature_columns = [
        "left_occupied",
        "left_size",
        "left_width",
        "left_length",
        "left_has_pillar",
        "right_occupied",
        "right_size",
        "right_width",
        "right_length",
        "right_has_pillar",
        "controlled_width",
        "controlled_length",
        "left_angle_deg",
        "right_angle_deg",
        "tier_beginner",
        "tier_intermediate",
    ]

    zone_ids = df["zone_id"]

    X = pd.DataFrame()
    for col in feature_columns:
        if col in df.columns:
            X[col] = df[col]
        else:
            if col in [
                "left_occupied",
                "right_occupied",
                "left_has_pillar",
                "right_has_pillar",
                "tier_beginner",
                "tier_intermediate",
            ]:
                X[col] = 0
            elif col in ["left_size", "right_size"]:
                X[col] = 0
            elif col in [
                "left_width",
                "left_length",
                "right_width",
                "right_length",
                "controlled_width",
                "controlled_length",
            ]:
                X[col] = 0.0
            elif col in ["left_angle_deg", "right_angle_deg"]:
                X[col] = 0.0
            else:
                X[col] = 0.0

    return zone_ids, X


def predict_per_zone(features_per_zone):
    try:
        _ensure_models_loaded()
        zone_ids, X = preprocess_features(features_per_zone)
        logger.debug(f"[Predictor] 전처리 완료. 구역 수: {len(zone_ids)}, 특성 수: {X.shape[1]}")

        step_preds = step_predict_model.predict(X)
        score_preds = score_predict_model.predict(X)

        logger.debug(f"[Predictor] 예측 완료. step_preds: {step_preds}, score_preds: {score_preds}")

        results = []
        for zid, sp, sc in zip(zone_ids, step_preds, score_preds):
            results.append(
                {
                    "zone_id": zid,
                    "pred_step": float(sp),
                    "pred_deg_score": float(sc),
                }
            )
        return results

    except Exception as e:
        logger.error(f"[Predictor] 예측 과정에서 오류 발생: {e}")
        logger.exception("[Predictor] 상세 오류 정보:")
        return []


def recommend_best_zone_bonus(
    features_per_zone,
    max_time=18.0,
    user_skill_level: str = "beginner",
    preference: str = "balanced",
    ensure_easy_in_top_k: tuple | None = None,
    use_model_predictions: bool = True,
    *,
    beginner_hard_success: bool = False,
):
    CAP_TOTAL = 1.0

    EASE_LEFT_PILLAR = 0.12
    EASE_ANY_EMPTY_SIDE = 0.12
    EASE_BOTH_EMPTY = 0.08
    EASE_INTERMEDIATE = 0.05
    EASE_GEOM_OCC_ANGLE = 0.15
    EASE_CLAMP_MAX = 0.40

    ANGLE_CENTER = 70.0
    ANGLE_STEEP = 0.08
    TIME_CENTER = 0.5
    TIME_STEEP = 7.5

    SKILL_MATCH_EASY = 0.12
    SKILL_MATCH_BALANCED = 0.08
    SKILL_MATCH_HARD = 0.12

    SKILL_PROGRESS_HARD = 0.14
    DIFFICULTY_HARD_THR = 0.45
    SLOW_THR = 0.35


    def _time_norm(t: float, max_time=max_time) -> float:
        if t is None:
            return 0.0
        try:
            t = float(t)
        except (TypeError, ValueError):
            return 0.0
        t = max(0.0, min(t, max_time))
        return (max_time - t) / max_time

    def _sigmoid(x: float, center: float, steep: float) -> float:
        return 1.0 / (1.0 + math.exp(-steep * (x - center)))

    def _angle_bonus(deg_score_0_100: float) -> float:
        return _sigmoid(float(deg_score_0_100), ANGLE_CENTER, ANGLE_STEEP)

    def _time_bonus(time_norm_0_1: float) -> float:
        return _sigmoid(float(time_norm_0_1), TIME_CENTER, TIME_STEEP)

    def _ease_bonus(fm: dict) -> float:
        has_left_pillar = int(fm.get("left_has_pillar", 0)) == 1
        left_empty = int(fm.get("left_occupied", 0)) == 0
        right_empty = int(fm.get("right_occupied", 0)) == 0
        is_intermediate = int(fm.get("tier_intermediate", 0)) == 1

        bonus = 0.0
        if has_left_pillar:
            bonus += EASE_LEFT_PILLAR
        if left_empty or right_empty:
            bonus += EASE_ANY_EMPTY_SIDE
        if left_empty and right_empty:
            bonus += EASE_BOTH_EMPTY
        if is_intermediate:
            bonus += EASE_INTERMEDIATE

        try:
            left_ang = abs(float(fm.get("left_angle_deg", 0.0) or 0.0))
            right_ang = abs(float(fm.get("right_angle_deg", 0.0) or 0.0))
        except (TypeError, ValueError):
            left_ang, right_ang = 0.0, 0.0

        def _angle_ease_component(angle_deg: float) -> float:
            angle_deg = max(0.0, min(90.0, float(angle_deg)))
            return 1.0 - (angle_deg / 90.0)

        if user_skill_level == "beginner":
            geom_coef = EASE_GEOM_OCC_ANGLE * 0.4
        elif user_skill_level == "advanced":
            geom_coef = EASE_GEOM_OCC_ANGLE * 1.5
        else:
            geom_coef = EASE_GEOM_OCC_ANGLE * 1.0
        if not left_empty:
            bonus += geom_coef * _angle_ease_component(left_ang)
        if not right_empty:
            bonus += geom_coef * _angle_ease_component(right_ang)

        return max(0.0, min(bonus, EASE_CLAMP_MAX))

    def _difficulty_from_deg(deg_score_0_100: float, ease_b: float) -> float:
        base = 1.0 - (float(deg_score_0_100) / 100.0)
        return max(0.0, min(base * (1.0 - 0.5 * float(ease_b)), 1.0))

    def _skill_match_bonus(user_skill: str, difficulty: float, time_norm: float) -> tuple[float, float]:
        base_bonus = 0.0
        progress_bonus = 0.0

        if user_skill == "beginner":
            easy = difficulty <= 0.35 and time_norm >= 0.6
            if easy:
                base_bonus = SKILL_MATCH_EASY

            if beginner_hard_success:
                hardish = difficulty >= DIFFICULTY_HARD_THR or time_norm <= SLOW_THR
                if hardish:
                    progress_bonus = SKILL_PROGRESS_HARD

        elif user_skill == "advanced":
            hard = difficulty >= 0.45 or time_norm <= 0.35
            if hard:
                base_bonus = SKILL_MATCH_HARD
        else:
            balanced = 0.35 < difficulty < 0.55 and 0.4 <= time_norm <= 0.75
            if balanced:
                base_bonus = SKILL_MATCH_BALANCED

        return base_bonus, progress_bonus

    feat_map = {}
    for f in (features_per_zone or []):
        zid = f.get("zone_id")
        if zid is None:
            continue
        feat_map[zid] = {
            "left_has_pillar": int(f.get("left_has_pillar", 0)),
            "left_occupied": int(f.get("left_occupied", 0)),
            "right_occupied": int(f.get("right_occupied", 0)),
            "tier_intermediate": int(
                f.get("tier_intermediate", 1 if f.get("agent_angle_tier") == "intermediate" else 0)
            ),
            "left_angle_deg": float(f.get("left_angle_deg", 0.0) or 0.0),
            "right_angle_deg": float(f.get("right_angle_deg", 0.0) or 0.0),
        }

    if not features_per_zone:
        return []

    def _heuristic_preds(features):
        preds_local = []
        for f in features:
            zid = f.get("zone_id")
            if zid is None:
                continue
            left_occ = int(f.get("left_occupied", 0)) == 1
            right_occ = int(f.get("right_occupied", 0)) == 1
            left_ang = float(f.get("left_angle_deg", 0.0) or 0.0)
            right_ang = float(f.get("right_angle_deg", 0.0) or 0.0)

            def _angle_to_ease(a):
                a = abs(float(a))
                if a >= 90.0:
                    return 0.0
                return 1.0 - (a / 90.0)

            parts = []
            if left_occ:
                parts.append(_angle_to_ease(left_ang))
            if right_occ:
                parts.append(_angle_to_ease(right_ang))
            deg_norm = (sum(parts) / len(parts)) if parts else 1.0

            empties = (0 if left_occ else 1) + (0 if right_occ else 1)
            time_norm = 0.5 + 0.25 * empties
            time_norm = max(0.0, min(1.0, time_norm))

            preds_local.append(
                {
                    "zone_id": zid,
                    "pred_step": (1.0 - time_norm) * max_time,
                    "pred_deg_score": deg_norm * 100.0,
                }
            )
        return preds_local

    preds = predict_per_zone(features_per_zone) if use_model_predictions else _heuristic_preds(features_per_zone)
    if not preds:
        logger.warning("[Recommender] 모델 예측이 비어 있음. 휴리스틱으로 대체합니다.")
        preds = _heuristic_preds(features_per_zone)

    pref = (preference or "balanced").lower()
    if pref == "easy":
        W_ANGLE, W_TIME, W_EASE, W_SKILL = 0.25, 0.20, 0.40, 0.15
    elif pref == "pro":
        W_ANGLE, W_TIME, W_EASE, W_SKILL = 0.40, 0.30, 0.15, 0.15
    else:
        W_ANGLE, W_TIME, W_EASE, W_SKILL = 0.33, 0.27, 0.25, 0.15

    if user_skill_level == "advanced":
        W_ANGLE, W_TIME, W_EASE, W_SKILL = 0.45, 0.20, 0.15, 0.20
    elif user_skill_level == "beginner":
        W_ANGLE, W_TIME, W_EASE, W_SKILL = 0.25, 0.30, 0.35, 0.10

    ANGLE_WEIGHT_SCALE = 1.5
    W_ANGLE *= ANGLE_WEIGHT_SCALE
    if user_skill_level == "advanced":
        W_ANGLE *= 1.1
    elif user_skill_level == "beginner":
        W_ANGLE *= 0.8

    results = []
    for p in preds:
        zid = p["zone_id"]
        deg = float(p.get("pred_deg_score", 0.0))
        tnorm = _time_norm(p.get("pred_step"), max_time=max_time)
        fm = feat_map.get(zid, {})

        ease_b = _ease_bonus(fm)
        angle_b = _angle_bonus(deg)
        time_b = _time_bonus(tnorm)
        diff = _difficulty_from_deg(deg, ease_b)
        skill_b_base, progress_b = _skill_match_bonus(user_skill_level, diff, tnorm)

        skill_b_total = skill_b_base + progress_b
        bonus_total = (
            W_ANGLE * angle_b + W_TIME * time_b + W_EASE * ease_b + W_SKILL * skill_b_total
        )
        
        angle_adjustment = 0.0
        left_angle = abs(float(fm.get("left_angle_deg", 0.0) or 0.0))
        
        if user_skill_level == "advanced":
            if deg < 46.5:
                angle_adjustment = 0.18
            elif 5.0 <= left_angle <= 20.0:
                angle_adjustment = 0.15
        elif user_skill_level == "beginner":
            if deg >= 46.5: 
                angle_adjustment = 0.18
            elif left_angle <= 2.0:
                angle_adjustment = 0.15
        
        bonus_total += angle_adjustment
        bonus_total = max(0.0, min(bonus_total, CAP_TOTAL))

        out = dict(p)
        out.update(
            {
                "time_norm": float(tnorm),
                "angle_bonus": float(angle_b),
                "time_bonus": float(time_b),
                "ease_bonus": float(ease_b),
                "skill_bonus_base": float(skill_b_base),
                "progress_bonus": float(progress_b),
                "skill_bonus": float(skill_b_total),
                "difficulty": float(diff),
                "bonus_total": float(bonus_total),
            }
        )
        results.append(out)

    if results:
        for r in results:
            if user_skill_level == "beginner":
                nudge = 0.06 * (0.6 * r["time_norm"] + 0.4 * (1.0 - r["difficulty"]) - 0.5)
            elif user_skill_level == "advanced":
                nudge = 0.06 * (0.6 * (1.0 - r["time_norm"]) + 0.4 * r["difficulty"] - 0.5)
            else:
                nudge = 0.0
            r["bonus_total"] = max(0.0, min(r["bonus_total"] + nudge, CAP_TOTAL))

    if user_skill_level == "advanced":
        results.sort(
            key=lambda r: (r["bonus_total"], r["difficulty"], 1.0 - r["time_norm"]),
            reverse=True,
        )
    elif user_skill_level == "beginner":
        results.sort(
            key=lambda r: (r["bonus_total"], r["ease_bonus"], -r["difficulty"], r["time_norm"]),
            reverse=True,
        )
    else:
        results.sort(
            key=lambda r: (r["bonus_total"], r["ease_bonus"], -abs(r["difficulty"] - 0.5), r["time_norm"]),
            reverse=True,
        )

    if ensure_easy_in_top_k and len(results) > 1:
        try:
            k, easy_thr = int(ensure_easy_in_top_k[0]), float(ensure_easy_in_top_k[1])
        except Exception:
            k, easy_thr = None, None
        if k and k > 0:
            topk = results[:k]
            if not any(r["difficulty"] <= easy_thr for r in topk):
                for i in range(k, len(results)):
                    if results[i]["difficulty"] <= easy_thr:
                        topk[-1], results[i] = results[i], topk[-1]
                        results = topk + results[k:]
                        break

    return results



def recommend_best_zone(*args, **kwargs):
    return recommend_best_zone_bonus(*args, **kwargs)
