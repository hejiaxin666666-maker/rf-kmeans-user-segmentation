"""End-to-end RF + K-Means analysis pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from .clustering import evaluate_k_values, fit_and_profile
from .data_loader import Source, load_behavior_data
from .feature_engineering import build_user_features
from .preprocessing import clean_behavior_frame
from .sample_data import make_sample_data


class AnalysisError(ValueError):
    """User-facing error raised for invalid or unusable analysis input."""


@dataclass
class AnalysisResult:
    user_features: pd.DataFrame
    cluster_summary: pd.DataFrame
    evaluation: pd.DataFrame
    quality_report: dict[str, Any]
    metadata: dict[str, Any]
    recommend_k: int


def _prepare_source(source: Source | pd.DataFrame | None) -> tuple[pd.DataFrame, dict, bool]:
    if source is None:
        sample = make_sample_data()
        cleaned, report = clean_behavior_frame(sample)
        report["source_type"] = "synthetic"
        return cleaned, report, True
    if isinstance(source, pd.DataFrame):
        cleaned, report = clean_behavior_frame(source)
        report["source_type"] = "dataframe"
        return cleaned, report, False
    cleaned, report = load_behavior_data(source)
    report["source_type"] = "csv"
    return cleaned, report, False


def run_analysis(
    source: Source | pd.DataFrame | None,
    selected_k: int = 4,
    calculate_silhouette: bool = True,
    source_name: str = "",
) -> AnalysisResult:
    """Run cleaning, RF feature engineering, evaluation, and clustering."""

    try:
        clean_df, quality_report, is_synthetic = _prepare_source(source)
        user_features, reference_date = build_user_features(clean_df)
        max_candidate_k = min(7, len(user_features))
        if max_candidate_k <= 2:
            raise AnalysisError("用户数量过少，至少需要 3 个有购买行为的用户才能聚类")
        evaluation, recommend_k = evaluate_k_values(
            user_features,
            range(2, max_candidate_k),
            calculate_silhouette=calculate_silhouette,
        )
        selected_k = int(selected_k)
        if selected_k not in set(evaluation["k"].astype(int)):
            raise AnalysisError(
                f"当前用户数不支持 K={selected_k}，请选择 {int(evaluation['k'].min())} 到 {int(evaluation['k'].max())}"
            )
        clustered, summary, cluster_metadata = fit_and_profile(user_features, selected_k)
    except AnalysisError:
        raise
    except ValueError as exc:
        raise AnalysisError(str(exc)) from exc

    quality_report = dict(quality_report)
    quality_report["purchase_rows"] = int((clean_df["behavior_type"] == 4).sum())
    quality_report["user_count"] = int(len(user_features))
    metadata = {
        **cluster_metadata,
        "source_name": source_name or ("内置示例数据" if is_synthetic else "上传数据"),
        "is_synthetic": is_synthetic,
        "reference_date": reference_date.date().isoformat(),
        "evaluated_k_values": evaluation["k"].astype(int).tolist(),
        "recommend_k": int(recommend_k),
        "selected_k": int(selected_k),
        "run_at": datetime.now(timezone.utc).isoformat(),
    }
    return AnalysisResult(
        user_features=clustered,
        cluster_summary=summary,
        evaluation=evaluation,
        quality_report=quality_report,
        metadata=metadata,
        recommend_k=int(recommend_k),
    )
