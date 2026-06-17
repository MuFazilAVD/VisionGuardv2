from __future__ import annotations

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


def add_billed_allowed_ratio(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    eligible = clean_numeric_series(result.get("AmtEligible", 0), index=result.index)
    charged = clean_numeric_series(result.get("AmtCharged", 0), index=result.index)
    result["BilledAllowedRatio"] = (charged / eligible.where(eligible > 0, pd.NA)).fillna(0.0)
    return result


def prepare_feature_frame(df: pd.DataFrame) -> pd.DataFrame:
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

    return result[NUMERIC_FEATURES + CATEGORICAL_FEATURES]


def build_feature_pipeline() -> ColumnTransformer:
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
