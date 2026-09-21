"""User-level RF and behavior profile features."""

from __future__ import annotations

import pandas as pd


def build_user_features(clean_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Timestamp]:
    """Build RF features and lightweight behavior features from clean events."""

    if clean_df.empty:
        raise ValueError("清洗后没有可用行为记录")
    purchase_df = clean_df.loc[clean_df["behavior_type"] == 4].copy()
    if purchase_df.empty:
        raise ValueError("没有购买行为，无法计算 RF 用户特征")

    reference_date = pd.Timestamp(purchase_df["timestamp"].max()).normalize()
    rf = (
        purchase_df.groupby("user_id", as_index=False)
        .agg(last_buy_date=("timestamp", "max"), F=("timestamp", "size"))
    )
    rf["last_buy_date"] = pd.to_datetime(rf["last_buy_date"]).dt.normalize()
    rf["R"] = (reference_date - rf["last_buy_date"]).dt.days.astype(int)

    behavior_counts = pd.crosstab(clean_df["user_id"], clean_df["behavior_type"])
    behavior_counts = behavior_counts.reindex(columns=[1, 2, 3, 4], fill_value=0)
    behavior_counts = behavior_counts.rename(
        columns={
            1: "browse_count",
            2: "favorite_count",
            3: "cart_count",
            4: "purchase_count",
        }
    )
    behavior_counts.index.name = "user_id"
    behavior_counts = behavior_counts.reset_index()

    activity = (
        clean_df.assign(activity_date=clean_df["timestamp"].dt.normalize())
        .groupby("user_id", as_index=False)
        .agg(
            active_days=("activity_date", "nunique"),
            last_active_date=("timestamp", "max"),
            category_count=("category_id", "nunique"),
        )
    )
    activity["last_active_date"] = pd.to_datetime(activity["last_active_date"]).dt.normalize()

    features = rf.merge(behavior_counts, on="user_id", how="left").merge(
        activity, on="user_id", how="left"
    )
    count_columns = [
        "F",
        "browse_count",
        "favorite_count",
        "cart_count",
        "purchase_count",
        "active_days",
        "category_count",
    ]
    features[count_columns] = features[count_columns].fillna(0).astype(int)
    return features.sort_values("user_id").reset_index(drop=True), reference_date
