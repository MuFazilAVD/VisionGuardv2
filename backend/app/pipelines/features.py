from __future__ import annotations

import logging

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder

from app.utils.number_parsing import clean_numeric_series


NUMERIC_FEATURES = [
    "Age",
    "Rule_Flag_Count",
    "AmtCharged",
    "AmtEligible",
    "ClaimLineTotalPaid",
    "AllowedUnits",
    "BilledAllowedRatio",
]

CATEGORICAL_FEATURES = [
    "ProcedureCode",
    "Gender",
    "State",
    "LOB",
    "CoverageCode",
]

logger = logging.getLogger(__name__)


def add_billed_allowed_ratio(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Adding billed-to-allowed ratio for %d row(s)", len(df))
    result = df.copy()
    eligible = clean_numeric_series(result.get("AmtEligible", 0), index=result.index)
    charged = clean_numeric_series(result.get("AmtCharged", 0), index=result.index)
    result["BilledAllowedRatio"] = (charged / eligible.where(eligible > 0, pd.NA)).fillna(0.0)
    logger.info("Billed-to-allowed ratio added")
    return result


def prepare_feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Preparing feature frame from input shape=%s", df.shape)
    result = add_billed_allowed_ratio(df)

    for column in NUMERIC_FEATURES:
        if column not in result.columns:
            result[column] = 0.0
        result[column] = clean_numeric_series(result[column], index=result.index).astype(float)

    for column in CATEGORICAL_FEATURES:
        if column not in result.columns:
            result[column] = "UNKNOWN"
        result[column] = (
            result[column]
            .fillna("UNKNOWN")
            .astype(str)
            .str.strip()
            .replace({"": "UNKNOWN", "nan": "UNKNOWN", "None": "UNKNOWN"})
        )

    prepared = result[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    logger.info("Feature frame prepared with shape=%s", prepared.shape)
    return prepared


def build_feature_pipeline() -> ColumnTransformer:
    logger.info(
        "Building feature pipeline with %d numeric and %d categorical feature(s)",
        len(NUMERIC_FEATURES),
        len(CATEGORICAL_FEATURES),
    )
    return ColumnTransformer(
        transformers=[
            ("numeric", "passthrough", NUMERIC_FEATURES),
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                CATEGORICAL_FEATURES,
            ),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )
