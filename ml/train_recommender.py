"""
extract_goal_features_dataset_10000.csv 같은 피처 CSV를 이용해
추천 모델을 학습하고, 결과 모델을 ml/artifacts/best_step_model.joblib 으로 저장하는 스크립트.

사용 예시
  python -m ml.train_recommender --data path/to/extract_goal_features_dataset_10000.csv \
      --target step --outdir ml/artifacts

타깃 컬럼을 지정하지 않으면 자동 탐색을 시도합니다.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

from ml.step_predictor import train_model


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True, help="학습에 사용할 CSV 경로")
    parser.add_argument("--target", default=None, help="타깃 컬럼명(미지정 시 자동 탐색)")
    parser.add_argument(
        "--outdir",
        default=str(Path(__file__).with_name("artifacts")),
        help="모델/리포트 저장 경로 (기본: ml/artifacts)",
    )
    parser.add_argument("--search", action="store_true", help="랜덤 탐색으로 하이퍼파라미터 튜닝 수행")
    parser.add_argument("--n_iter", type=int, default=20, help="탐색 반복 횟수")
    parser.add_argument("--cv", type=int, default=3, help="CV 폴드 수")
    args = parser.parse_args()

    model, report = train_model(
        data_path=args.data,
        target=args.target,
        outdir=args.outdir,
        search=args.search,
        n_iter=args.n_iter,
        cv=args.cv,
    )

    print("=== Training Finished ===")
    print(f"Artifacts dir: {Path(args.outdir).resolve()}")
    print(f"Model path   : {report['artifacts']['model_path']}")
    print("Metrics:")
    for k, v in report["metrics"].items():
        print(f"  - {k}: {v}")


if __name__ == "__main__":
    main()


