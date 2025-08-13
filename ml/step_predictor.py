"""
주차 시간(또는 이동 소요시간 등) 예측을 위한 학습 파이프라인 모듈.
- CLI 스크립트가 아닌 import 가능한 함수 형태로 구성.
- 사용 예시

from ml.step_predictor import train_model, save_model, load_model

model, report = train_model(data_path='data.csv', target='duration', search=True)
save_model(model, 'artifacts/best_step_model.joblib')
loaded = load_model('artifacts/best_step_model.joblib')
"""

from __future__ import annotations

import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold, RandomizedSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.ensemble import HistGradientBoostingRegressor

RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)


def autodetect_target(df: pd.DataFrame) -> str:
    if 'step' in df.columns:
        return 'step'
    for c in df.columns:
        cl = str(c).lower()
        if any(k in cl for k in ['step', 'duration', 'time']):
            return c
    raise RuntimeError(f'Could not detect target column. Columns: {list(df.columns)}')


def enrich_datetime_features(X: pd.DataFrame) -> pd.DataFrame:
    X = X.copy()
    drops: List[str] = []
    for col in X.columns:
        if X[col].dtype == 'O':
            parsed = pd.to_datetime(X[col], errors='coerce', utc=True)
            if parsed.notna().mean() >= 0.6:
                X[f'{col}__year'] = parsed.dt.year
                X[f'{col}__month'] = parsed.dt.month
                X[f'{col}__day'] = parsed.dt.day
                X[f'{col}__dow'] = parsed.dt.dayofweek
                X[f'{col}__hour'] = parsed.dt.hour
                drops.append(col)
    if drops:
        X = X.drop(columns=drops)
    return X


def build_pipeline(num_cols: List[str], cat_cols: List[str]) -> Pipeline:
    num = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler()),
    ])
    # OneHotEncoder가 기본적으로 희소(sparse)를 반환하면
    # HistGradientBoostingRegressor 입력에서 에러가 발생한다.
    # 버전 호환을 위해 sparse_output(False) 우선, 실패 시 sparse(False)로 생성한다.
    try:
        onehot = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
    except TypeError:  # 구버전 호환
        onehot = OneHotEncoder(handle_unknown='ignore', sparse=False)  # type: ignore
    cat = Pipeline([
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('onehot', onehot),
    ])
    prep = ColumnTransformer([
        ('num', num, num_cols),
        ('cat', cat, cat_cols),
    ])
    model = HistGradientBoostingRegressor(random_state=RANDOM_STATE)
    return Pipeline([
        ('prep', prep),
        ('model', model),
    ])


def train_model(
    data_path: Optional[str] = None,
    df: Optional[pd.DataFrame] = None,
    target: Optional[str] = None,
    outdir: str = 'artifacts',
    search: bool = False,
    n_iter: int = 20,
    cv: int = 3,
    oof: bool = False,
) -> Tuple[Pipeline, Dict]:
    """
    데이터로부터 모델을 학습하고, 모델과 리포트를 반환한다.
    - data_path 또는 df 중 하나를 제공해야 한다.
    - target이 None이면 자동 탐색을 시도한다.
    - search=True면 RandomizedSearchCV로 하이퍼파라미터 탐색 수행.
    """
    assert data_path is not None or df is not None, 'data_path 또는 df를 제공해야 합니다.'
    os.makedirs(outdir, exist_ok=True)

    if df is None:
        df = pd.read_csv(data_path)

    target_col = target or autodetect_target(df)

    df = df[~df[target_col].isna()].copy()
    if not np.issubdtype(df[target_col].dtype, np.number):
        df[target_col] = pd.to_numeric(df[target_col], errors='coerce')
        df = df[~df[target_col].isna()].copy()

    X = enrich_datetime_features(df.drop(columns=[target_col]))
    y = df[target_col].values

    num_cols = [c for c in X.columns if np.issubdtype(X[c].dtype, np.number)]
    cat_cols = [c for c in X.columns if c not in num_cols]
    pipe = build_pipeline(num_cols, cat_cols)

    metrics: Dict[str, float] = {}
    best_params: Optional[Dict] = None

    if search:
        kf = KFold(n_splits=cv, shuffle=True, random_state=RANDOM_STATE)
        space = {
            'model__learning_rate': np.logspace(-3, -0.1, 8),
            'model__max_depth': [None, 5, 7, 9, 12],
            'model__max_leaf_nodes': [None, 31, 63, 127],
            'model__min_samples_leaf': [10, 20, 30, 50, 70],
            'model__l2_regularization': np.logspace(-6, -1, 6),
        }
        searcher = RandomizedSearchCV(
            pipe, space, n_iter=n_iter, scoring='neg_mean_absolute_error',
            refit=True, cv=kf, random_state=RANDOM_STATE, n_jobs=-1, verbose=1
        )
        searcher.fit(X, y)
        pipe = searcher.best_estimator_
        metrics['cv_mae'] = float(-searcher.best_score_)
        best_params = searcher.best_params_

        if oof:
            oof_pred = np.zeros(len(X))
            for tr, te in kf.split(X, y):
                m = clone(searcher.best_estimator_)
                m.fit(X.iloc[tr], y[tr])
                oof_pred[te] = m.predict(X.iloc[te])
            pd.DataFrame({'y_true': y, 'y_pred': oof_pred, 'abs_error': np.abs(y - oof_pred)}).to_csv(
                os.path.join(outdir, 'oof_predictions.csv'), index=False
            )

    pipe.fit(X, y)
    pred = pipe.predict(X)
    # 일부 구버전 scikit-learn은 mean_squared_error의 squared 파라미터를 지원하지 않음
    _mse = mean_squared_error(y, pred)
    _rmse = float(_mse ** 0.5)
    metrics.update({
        'train_mae': float(mean_absolute_error(y, pred)),
        'train_rmse': _rmse,
        'train_r2': float(r2_score(y, pred)),
    })

    ts = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    model_path = os.path.join(outdir, 'best_step_model.joblib')
    joblib.dump(pipe, model_path)

    pd.DataFrame({'y_true': y, 'y_pred': pred, 'abs_error': np.abs(y - pred)}).head(200).to_csv(
        os.path.join(outdir, 'train_predictions_sample.csv'), index=False
    )

    report = {
        'timestamp_utc': ts,
        'rows': int(len(df)),
        'features': int(X.shape[1]),
        'target_column': target_col,
        'best_params': best_params,
        'metrics': metrics,
        'artifacts': {
            'model_path': os.path.abspath(model_path),
            'train_predictions_sample': os.path.abspath(os.path.join(outdir, 'train_predictions_sample.csv')),
        },
    }

    # 이력 저장
    with open(os.path.join(outdir, 'experiment_report.json'), 'w') as f:
        json.dump(report, f, indent=2)

    hist = os.path.join(outdir, 'experiments_history.csv')
    row = {
        'timestamp_utc': ts,
        'best_params': json.dumps(best_params) if best_params is not None else None,
        **metrics,
    }
    if os.path.exists(hist):
        pd.concat([pd.read_csv(hist), pd.DataFrame([row])], ignore_index=True).to_csv(hist, index=False)
    else:
        pd.DataFrame([row]).to_csv(hist, index=False)

    return pipe, report


def save_model(model: Pipeline, path: str) -> None:
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    joblib.dump(model, path)


def load_model(path: str) -> Pipeline:
    return joblib.load(path)


