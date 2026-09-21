"""Data cleaning helpers for Taobao user behavior records."""

from __future__ import annotations

from typing import Any

import pandas as pd


EXPECTED_COLUMNS = [
    "user_id",
    "item_id",
    "category_id",
    "behavior_type",
    "timestamp",
]
VALID_BEHAVIORS = {1, 2, 3, 4}


def clean_behavior_frame(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Clean one parsed CSV chunk and return it with a quality report."""

    missing = [column for column in EXPECTED_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"CSV 缺少必要字段：{', '.join(missing)}")

    data = frame[EXPECTED_COLUMNS].copy()
    report: dict[str, Any] = {
        "input_rows": int(len(data)),
        "duplicate_rows": 0,
        "empty_user_rows": 0,
        "invalid_timestamp_rows": 0,
        "invalid_behavior_rows": 0,
    }

    duplicate_mask = data.duplicated(keep="first")
    report["duplicate_rows"] = int(duplicate_mask.sum())
    data = data.loc[~duplicate_mask].copy()

    empty_user_mask = data["user_id"].isna() | data["user_id"].astype(str).str.strip().eq("")
    report["empty_user_rows"] = int(empty_user_mask.sum())
    data = data.loc[~empty_user_mask].copy()
    data["user_id"] = data["user_id"].astype(str).str.strip()

    behavior = pd.to_numeric(data["behavior_type"], errors="coerce")
    valid_behavior_mask = behavior.isin(VALID_BEHAVIORS)
    report["invalid_behavior_rows"] = int((~valid_behavior_mask).sum())
    data = data.loc[valid_behavior_mask].copy()
    data["behavior_type"] = behavior.loc[valid_behavior_mask].astype(int)

    if pd.api.types.is_datetime64_any_dtype(data["timestamp"]):
        parsed_time = pd.to_datetime(data["timestamp"], errors="coerce")
    else:
        numeric_time = pd.to_numeric(data["timestamp"], errors="coerce")
        parsed_time = pd.to_datetime(numeric_time, unit="s", errors="coerce")
    invalid_time_mask = parsed_time.isna()
    report["invalid_timestamp_rows"] = int(invalid_time_mask.sum())
    data = data.loc[~invalid_time_mask].copy()
    data["timestamp"] = parsed_time.loc[~invalid_time_mask]

    data = data.reset_index(drop=True)
    report["cleaned_rows"] = int(len(data))
    report["removed_rows"] = int(report["input_rows"] - report["cleaned_rows"])
    if not data.empty:
        report["min_timestamp"] = data["timestamp"].min().isoformat()
        report["max_timestamp"] = data["timestamp"].max().isoformat()
    else:
        report["min_timestamp"] = None
        report["max_timestamp"] = None
    return data, report
