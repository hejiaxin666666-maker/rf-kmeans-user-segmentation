"""Deterministic synthetic behavior data for first-load demos and tests."""

from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd


def make_sample_data(n_users: int = 180, seed: int = 42) -> pd.DataFrame:
    """Create clearly synthetic events spanning four RF-like user groups."""

    if n_users < 8:
        raise ValueError("示例用户数至少需要 8 人")
    rng = np.random.default_rng(seed)
    reference = pd.Timestamp("2017-12-03")
    rows: list[list[object]] = []
    segments = (
        (2, 8),   # recent and frequent
        (3, 1),   # recent and low frequency
        (48, 6),  # old and frequent
        (55, 1),  # old and low frequency
    )
    behavior_counts = {1: 4, 2: 2, 3: 2}

    for user_index in range(n_users):
        segment_index = user_index % 4
        base_recency, base_purchase_count = segments[segment_index]
        recency = max(0, base_recency + int(rng.integers(-2, 5)))
        count_jitter = int(rng.integers(-1, 3)) if base_purchase_count > 1 else int(rng.integers(0, 2))
        purchase_count = max(1, base_purchase_count + count_jitter)
        user_id = f"sample_user_{user_index + 1:04d}"
        for purchase_index in range(purchase_count):
            event_date = reference - timedelta(
                days=recency + purchase_index * int(rng.integers(5, 16))
            )
            rows.append(
                [
                    user_id,
                    f"item_purchase_{user_index}_{purchase_index}",
                    f"category_{int(rng.integers(1, 8))}",
                    4,
                    event_date,
                ]
            )
        for behavior_type, count in behavior_counts.items():
            for action_index in range(count + int(rng.integers(0, 3))):
                event_date = reference - timedelta(
                    days=int(rng.integers(0, recency + 14))
                )
                rows.append(
                    [
                        user_id,
                        f"item_action_{user_index}_{behavior_type}_{action_index}",
                        f"category_{int(rng.integers(1, 8))}",
                        behavior_type,
                        event_date,
                    ]
                )

    return pd.DataFrame(
        rows,
        columns=["user_id", "item_id", "category_id", "behavior_type", "timestamp"],
    )
