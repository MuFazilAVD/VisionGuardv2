from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import numpy as np
import pandas as pd

from app.pipelines.features import NUMERIC_FEATURES, add_billed_allowed_ratio
from app.utils.number_parsing import clean_numeric_series


BUSINESS_FEATURE_LABELS = {
    "Age": "member age",
    "Rule_Flag_Count": "number of risk indicators",
    "AmtCharged": "charged amount",
    "AmtEligible": "eligible amount",
    "ClaimLineTotalPaid": "paid amount",
    "AllowedUnits": "allowed units",
    "BilledAllowedRatio": "billed-to-allowed relationship",
}


def _numeric_matrix(df: pd.DataFrame) -> pd.DataFrame:
    result = add_billed_allowed_ratio(df)
    for column in NUMERIC_FEATURES:
        if column not in result.columns:
            result[column] = 0.0
        result[column] = clean_numeric_series(result[column], index=result.index).astype(float)
    return result[NUMERIC_FEATURES]


def compute_anomaly_stats(df: pd.DataFrame) -> dict[str, Any]:
    numeric = _numeric_matrix(df)
    means = numeric.mean().to_dict()
    stds = numeric.std(ddof=1).replace(0, 1.0).fillna(1.0).to_dict()
    raw_scores, _, _ = score_anomalies(df, {"means": means, "stds": stds, "max_anomaly_score": 1.0}, clip=False)
    max_score = float(np.max(raw_scores)) if len(raw_scores) else 1.0
    if max_score == 0:
        max_score = 1.0
    return {
        "features": NUMERIC_FEATURES,
        "means": {key: float(value) for key, value in means.items()},
        "stds": {key: float(value) if value else 1.0 for key, value in stds.items()},
        "max_anomaly_score": max_score,
        "computed_at": datetime.now(UTC).isoformat(),
    }


def score_anomalies(
    df: pd.DataFrame,
    stats: dict[str, Any],
    *,
    clip: bool = True,
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    numeric = _numeric_matrix(df)
    means = pd.Series(stats["means"], dtype=float)
    stds = pd.Series(stats["stds"], dtype=float).replace(0, 1.0).fillna(1.0)
    max_score = float(stats.get("max_anomaly_score") or 1.0)
    if max_score == 0:
        max_score = 1.0

    z = (numeric[NUMERIC_FEATURES] - means[NUMERIC_FEATURES]) / stds[NUMERIC_FEATURES]
    scores = np.sqrt(np.square(z.to_numpy(dtype=float)).sum(axis=1))
    normalized = scores / max_score
    if clip:
        normalized = np.clip(normalized, 0.0, 1.0)
    top_features = z.abs().idxmax(axis=1).map(BUSINESS_FEATURE_LABELS).tolist()
    return scores, normalized, top_features
