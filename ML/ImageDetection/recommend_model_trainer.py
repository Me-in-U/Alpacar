import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import joblib

# -----------------------
# 1. 데이터 로드 및 병합
# -----------------------
paths = [
    Path("advanced_extract_goal_features_dataset.csv"),
    Path("extract_goal_features_dataset.csv"),
]
tiers = ["intermediate", "beginner"]
dfs = []

for p, tier in zip(paths, tiers):
    df_ = pd.read_csv(p)
    if "done" in df_.columns:
        df_ = df_[df_["done"] == True]
    df_["agent_angle_tier"] = tier
    dfs.append(df_)

df = pd.concat(dfs, ignore_index=True)

# -----------------------
# 2. 피처 엔지니어링
# -----------------------
def wrap_rad(a):
    return (a + np.pi) % (2*np.pi) - np.pi

# 각도(deg) 변환
for side in ["left", "right"]:
    rad_col = f"{side}_angle"
    if rad_col in df.columns:
        ang = wrap_rad(df[rad_col].fillna(0.0).values)
        df[f"{side}_angle_deg"] = np.degrees(ang)

# step_adj 계산
unique_x = sorted(df["goal_position_x"].dropna().unique())
x2step_map = {v: 2 * i for i, v in enumerate(unique_x)}
df["step_adj"] = df["step"] - df["goal_position_x"].map(x2step_map)

# agent_angle_deg 필터
if "agent_angle_deg" in df.columns:
    df = df[df["agent_angle_deg"].abs() <= 15]

# -----------------------
# 3. 피처/타깃 분리
# -----------------------
drop_cols = [
    "Reset", "step", "agent_angle_deg", "left_angle", "right_angle", "done",
    "left_offset", "right_offset", "controlled_x", "controlled_y",
    "goal_lane_index", "goal_position_x", "goal_position_y", "goal_heading",
]
drop_cols = [c for c in drop_cols if c in df.columns]
data = df.drop(columns=drop_cols)

# tier 원-핫 인코딩
data["tier_beginner"] = (data["agent_angle_tier"] == "beginner").astype(int)
data["tier_intermediate"] = (data["agent_angle_tier"] == "intermediate").astype(int)
data = data.drop(columns=["agent_angle_tier"])

# 각도형 피처에 sin/cos 추가
angle_deg_cols = [c for c in data.columns if c.endswith("_angle_deg")]
for c in angle_deg_cols:
    rad = np.radians(data[c].astype(float))
    data[c + "_sin"] = np.sin(rad)
    data[c + "_cos"] = np.cos(rad)

# 타깃과 피처 분리
X = data.drop(columns=["step_adj", "agent_angle_score"])
X = X.select_dtypes(include=[np.number]).copy()
y_step = data["step_adj"].values
y_score = data["agent_angle_score"].values

# -----------------------
# 4. 데이터 분할
# -----------------------
X_train, X_val, y_step_tr, y_step_val, y_score_tr, y_score_val = train_test_split(
    X, y_step, y_score, test_size=0.2, random_state=42
)

# -----------------------
# 5. 모델 학습 (RandomForest)
# -----------------------
rf_params = {"n_estimators": 400, "random_state": 42, "n_jobs": -1}
rf_step = RandomForestRegressor(max_features="sqrt", min_samples_leaf=1, **rf_params).fit(X_train, y_step_tr)
rf_score = RandomForestRegressor(max_features="sqrt", min_samples_leaf=1, **rf_params).fit(X_train, y_score_tr)

# -----------------------
# 6. 성능 평가
# -----------------------
def report(y_true, y_pred):
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mae = float(mean_absolute_error(y_true, y_pred))
    r2 = float(r2_score(y_true, y_pred))
    return rmse, mae, r2

print("step_adj:", report(y_step_val, rf_step.predict(X_val)))
print("agent_angle_score:", report(y_score_val, rf_score.predict(X_val)))

# -----------------------
# 7. 모델과 피처 목록 저장
# -----------------------
joblib.dump(rf_step, "rf_step_model.joblib")
joblib.dump(rf_score, "rf_score_model.joblib")
pd.Series(X.columns, name="feature").to_csv("model_features.csv", index=False)
