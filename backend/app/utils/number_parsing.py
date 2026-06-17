from __future__ import annotations

import logging
import re
from typing import Any

import pandas as pd


NON_NUMERIC_MARKERS = {"", "nan", "none", "null", "na", "n/a"}

logger = logging.getLogger(__name__)


def parse_numeric_value(value: Any) -> Any:
    """Return a number-like value for strings such as "$1,234.56"."""
    if value is None:
        return 0
    if not isinstance(value, str):
        return value

    text = value.strip()
    if text.lower() in NON_NUMERIC_MARKERS:
        return 0

    negative = text.startswith("(") and text.endswith(")")
    cleaned = text.strip("()")
    cleaned = re.sub(r"[$,%\s,]", "", cleaned)
    if cleaned.lower() in NON_NUMERIC_MARKERS:
        return 0

    try:
        number = float(cleaned)
    except ValueError:
        return value
    return -number if negative else number


def clean_numeric_series(value: Any, *, index: pd.Index | None = None, default: float = 0.0) -> pd.Series:
    logger.info("Cleaning numeric series with default=%s", default)
    if isinstance(value, pd.Series):
        series = value
    else:
        series = pd.Series(value, index=index)

    parsed = series.map(parse_numeric_value)
    cleaned = pd.to_numeric(parsed, errors="coerce").fillna(default)
    logger.info("Numeric series cleaned with %d value(s)", len(cleaned))
    return cleaned
