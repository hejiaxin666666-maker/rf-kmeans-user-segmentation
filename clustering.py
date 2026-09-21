"""K-Means evaluation, fitting, and business-facing profile labels."""

from __future__ import annotations

from itertools import permutations
from typing import Any

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler


FEATURE_COLUMNS = ["R", "F"]
BUSINESS_LABELS = ["高价值用户", "潜力新用户", "流失老用户", "沉睡用户"]
BUSINESS_PROFILES: dict[str, dict[str, str]] = {
    "高价值用户": {
        "profile": "近期活跃且购买频繁的忠实用户",
        "strategy": "会员权益、新品优先体验和专属客服，核心目标是留存，避免无差别大额补贴。",
    },
    "潜力新用户": {
        "profile": "近期完成购买但尚未形成复购的新转化用户",
        "strategy": "复购小额优惠券、搭配商品推荐和二次购买提醒，引导完成复购。",
    },
    "流失老用户": {
        "profile": "历史购买频繁但已经较长时间没有购买的用户",
        "strategy": "召回活动、限时专属优惠和历史购买品类推荐，重点唤醒用户。",
    },
    "沉睡用户": {
        "profile": "购买次数较少且长时间没有再次购买的用户",
        "strategy": "低成本内容触达和社群种草，控制高额补贴投入，关注 ROI。",
    },
}


def _validate_features(user_features: pd.DataFrame) -> None:
    missing = [column for column in FEATURE_COLUMNS if column not in user_features.columns]
    if missing:
        raise ValueError(f"用户特征缺少字段：{', '.join(missing)}")
    if user_features.empty:
        raise ValueError("没有用户特征，无法进行聚类")


def _valid_k_values(user_count: int, k_values: list[int] | range) -> list[int]:
    valid = sorted({int(k) for k in k_values if 2 <= int(k) < user_count})
    if not valid:
        raise ValueError("K 值必须在 2 到用户数减 1 之间")
    return valid


def _elbow_recommendation(metrics: pd.DataFrame) -> int:
    if len(metrics) <= 2:
        return int(metrics.iloc[0]["k"])
    x = metrics["k"].to_numpy(dtype=float)
    y = metrics["inertia"].to_numpy(dtype=float)
    x_norm = (x - x.min()) / max(x.max() - x.min(), 1.0)
    y_norm = (y - y.min()) / max(y.max() - y.min(), 1.0)
    start = np.array([x_norm[0], y_norm[0]])
    end = np.array([x_norm[-1], y_norm[-1]])
    line = end - start
    distances = np.abs(line[0] * (start[1] - y_norm) - (start[0] - x_norm) * line[1])
    return int(metrics.iloc[int(np.argmax(distances))]["k"])


def evaluate_k_values(
    user_features: pd.DataFrame,
    k_values: list[int] | range,
    calculate_silhouette: bool = True,
    random_state: int = 42,
) -> tuple[pd.DataFrame, int]:
    """Evaluate inertia and optional silhouette score for candidate K values."""

    _validate_features(user_features)
    valid_k_values = _valid_k_values(len(user_features), k_values)
    scaler = StandardScaler()
    scaled = scaler.fit_transform(user_features[FEATURE_COLUMNS])
    rows: list[dict[str, Any]] = []
    for k in valid_k_values:
        model = KMeans(n_clusters=k, random_state=random_state, n_init=20)
        labels = model.fit_predict(scaled)
        silhouette = np.nan
        if calculate_silhouette and len(set(labels)) > 1:
            silhouette = float(silhouette_score(scaled, labels))
        rows.append({"k": k, "inertia": float(model.inertia_), "silhouette": silhouette})
    metrics = pd.DataFrame(rows)
    finite_silhouette = metrics["silhouette"].dropna()
    if not finite_silhouette.empty:
        recommended_k = int(metrics.loc[metrics["silhouette"].idxmax(), "k"])
    else:
        recommended_k = _elbow_recommendation(metrics)
    return metrics, recommended_k


def business_profile(label: str) -> dict[str, str]:
    """Return user-facing profile copy for a business label."""

    return BUSINESS_PROFILES.get(
        label,
        {"profile": "待结合 R/F 均值进一步解释的用户分组", "strategy": "建议结合品类偏好和后续实验制定策略。"},
    )


def _four_way_mapping(summary: pd.DataFrame) -> dict[int, str]:
    """Assign four cluster IDs to labels by closest R/F quadrant."""

    r_values = summary["avg_R"].to_numpy(dtype=float)
    f_values = summary["avg_F"].to_numpy(dtype=float)
    r_span = max(float(r_values.max() - r_values.min()), 1.0)
    f_span = max(float(f_values.max() - f_values.min()), 1.0)
    r_norm = (r_values - r_values.min()) / r_span
    f_norm = (f_values - f_values.min()) / f_span
    cluster_ids = summary["cluster"].astype(int).tolist()
    targets = {
        "高价值用户": (0.0, 1.0),
        "潜力新用户": (0.0, 0.0),
        "流失老用户": (1.0, 1.0),
        "沉睡用户": (1.0, 0.0),
    }
    best_cost = float("inf")
    best_order: tuple[int, ...] | None = None
    for order in permutations(cluster_ids):
        cost = 0.0
        for index, label in enumerate(BUSINESS_LABELS):
            cluster_position = cluster_ids.index(order[index])
            target_r, target_f = targets[label]
            cost += (r_norm[cluster_position] - target_r) ** 2
            cost += (f_norm[cluster_position] - target_f) ** 2
        if cost < best_cost:
            best_cost = cost
            best_order = order
    assert best_order is not None
    return {int(cluster_id): label for label, cluster_id in zip(BUSINESS_LABELS, best_order)}


def fit_and_profile(
    user_features: pd.DataFrame,
    selected_k: int,
    random_state: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Fit K-Means and attach dynamic business labels to user and summary rows."""

    _validate_features(user_features)
    selected_k = int(selected_k)
    if not 2 <= selected_k < len(user_features):
        raise ValueError("K 值必须在 2 到用户数减 1 之间")

    scaler = StandardScaler()
    scaled = scaler.fit_transform(user_features[FEATURE_COLUMNS])
    model = KMeans(n_clusters=selected_k, random_state=random_state, n_init=20)
    clustered = user_features.copy()
    clustered["cluster"] = model.fit_predict(scaled).astype(int)

    summary = (
        clustered.groupby("cluster", as_index=False)
        .agg(
            user_count=("user_id", "size"),
            avg_R=("R", "mean"),
            median_R=("R", "median"),
            avg_F=("F", "mean"),
            median_F=("F", "median"),
        )
        .sort_values("cluster")
        .reset_index(drop=True)
    )
    summary["user_ratio"] = summary["user_count"] / len(clustered)
    for column in ("browse_count", "favorite_count", "cart_count", "purchase_count"):
        if column in clustered.columns:
            means = clustered.groupby("cluster")[column].mean().rename(f"avg_{column}")
            summary = summary.merge(means, on="cluster", how="left")

    if selected_k == 4:
        mapping = _four_way_mapping(summary)
    else:
        mapping = {cluster_id: f"分群 {cluster_id + 1}" for cluster_id in summary["cluster"]}
    summary["cluster_label"] = summary["cluster"].map(mapping)
    summary["profile"] = summary["cluster_label"].map(lambda label: business_profile(label)["profile"])
    summary["strategy"] = summary["cluster_label"].map(lambda label: business_profile(label)["strategy"])
    clustered = clustered.merge(summary[["cluster", "cluster_label"]], on="cluster", how="left")
    metadata = {
        "selected_k": selected_k,
        "feature_columns": FEATURE_COLUMNS,
        "scaler_mean": scaler.mean_.tolist(),
        "scaler_scale": scaler.scale_.tolist(),
    }
    return clustered, summary, metadata
