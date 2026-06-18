from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd

from app.pipelines.rules_engine import EXAM_CODES
from app.utils.number_parsing import clean_numeric_series


SIMILARITY_THRESHOLD = 0.85
MEMBER_KEY = "MemberId"
FALLBACK_JOIN_KEYS = ["ProviderNPI", "State", "LOB", "CoverageCode"]
SIMILARITY_FEATURES = [
    "Age",
    "Rule_Flag_Count",
    "AmtCharged",
    "AmtEligible",
    "ClaimLineTotalPaid",
    "AllowedUnits",
]

PATTERN_FAMILIES = {
    "Two Exams in One Day": "Utilization Pattern",
    "Exam after Comprehensive": "Utilization Pattern",
    "CCI Edits Claims": "Coding Conflict",
    "Bilateral Claims": "Coding Irregularity",
}

PATTERN_PRIORITIES = {
    "CCI Edits Claims": "High",
    "Two Exams in One Day": "High",
    "Exam after Comprehensive": "Medium",
    "Bilateral Claims": "Medium",
}

logger = logging.getLogger(__name__)


def score_historical_similarity(
    realtime: pd.DataFrame,
    historical: pd.DataFrame,
    anomaly_stats: dict[str, Any],
    *,
    threshold: float = SIMILARITY_THRESHOLD,
) -> list[dict[str, Any]]:
    logger.info(
        "Scoring historical similarity: realtime_rows=%d historical_rows=%d threshold=%.3f",
        len(realtime),
        len(historical),
        threshold,
    )
    if realtime.empty:
        logger.info("Historical similarity skipped because realtime frame is empty")
        return []
    if historical.empty or "Flag" not in historical.columns:
        logger.info("Historical similarity using defaults because historical data or Flag column is missing")
        return [_default_result() for _ in range(len(realtime))]

    rt = _prepare_frame(realtime).reset_index(drop=True)
    hist = _prepare_frame(historical).reset_index(drop=True)
    hist = hist[hist["Flag"].fillna("").astype(str).str.strip() != ""].copy()
    if hist.empty:
        logger.info("Historical similarity using defaults because no flagged historical rows were found")
        return [_default_result() for _ in range(len(rt))]

    results: list[dict[str, Any]] = []
    for _, row in rt.iterrows():
        candidates = _historical_candidates(row, hist)

        if candidates.empty:
            logger.info("No historical similarity candidates for claim_id=%s", row.get("ClaimId", ""))
            results.append(_default_result())
            continue

        scores = _candidate_scores(row, candidates, anomaly_stats)
        if scores.size == 0:
            logger.info("No historical similarity scores for claim_id=%s", row.get("ClaimId", ""))
            results.append(_default_result())
            continue

        best_position = int(np.nanargmax(scores))
        best_score = float(scores[best_position])
        best = candidates.iloc[best_position]
        if not np.isfinite(best_score):
            best_score = 0.0

        pattern = str(best.get("Flag", "") or "").strip()
        above_threshold = best_score >= threshold
        logger.info(
            "Historical similarity best match: claim_id=%s score=%.6f above_threshold=%s pattern=%s",
            row.get("ClaimId", ""),
            best_score,
            above_threshold,
            pattern if above_threshold else "NONE",
        )
        results.append(
            {
                "similarity_score": round(best_score, 6),
                "similarity_above_threshold": above_threshold,
                "historical_pattern": pattern if above_threshold else "NONE",
                "historical_pattern_family": _pattern_family(pattern) if above_threshold else "NONE",
                "historical_pattern_confidence": round(best_score, 6) if above_threshold else 0.0,
                "historical_case_priority": _case_priority(pattern) if above_threshold else "LOW",
                "historical_claim_id": str(best.get("ClaimId", "")) if above_threshold else "",
                "historical_member_id": str(best.get("MemberId", "")) if above_threshold else "",
                "historical_line_number": int(best.get("LineNumber", 0) or 0) if above_threshold else 0,
            }
        )

    logger.info("Historical similarity scoring complete with %d result(s)", len(results))
    return results


def _prepare_frame(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Preparing frame for historical similarity with shape=%s", df.shape)
    result = df.copy()
    for key in [MEMBER_KEY, *FALLBACK_JOIN_KEYS]:
        if key not in result.columns:
            result[key] = ""
        result[key] = result[key].fillna("").astype(str).str.strip().str.upper()

    if "ProcedureCode" not in result.columns:
        result["ProcedureCode"] = ""
    result["ProcedureCode"] = result["ProcedureCode"].fillna("").astype(str).str.strip().str.upper()

    for feature in SIMILARITY_FEATURES:
        if feature not in result.columns:
            result[feature] = 0.0
        result[feature] = clean_numeric_series(result[feature], index=result.index).astype(float)
    logger.info("Similarity frame prepared with shape=%s", result.shape)
    return result


def _historical_candidates(row: pd.Series, historical: pd.DataFrame) -> pd.DataFrame:
    member_id = str(row.get(MEMBER_KEY, "") or "").strip().upper()
    historical_has_members = historical[MEMBER_KEY].ne("").any()
    if member_id and historical_has_members:
        candidates = historical[historical[MEMBER_KEY] == member_id]
        logger.info(
            "Historical candidates selected by member_id=%s count=%d",
            member_id,
            len(candidates),
        )
        return candidates

    candidates = historical
    for key in FALLBACK_JOIN_KEYS:
        candidates = candidates[candidates[key] == row[key]]
    logger.info("Historical candidates selected by fallback keys count=%d", len(candidates))
    return candidates


def _candidate_scores(row: pd.Series, candidates: pd.DataFrame, anomaly_stats: dict[str, Any]) -> np.ndarray:
    logger.info("Computing similarity scores for %d candidate row(s)", len(candidates))
    rt_vector = _z_vector(row, anomaly_stats)
    hist_matrix = np.vstack([_z_vector(candidate, anomaly_stats) for _, candidate in candidates.iterrows()])
    rt_norm = float(np.linalg.norm(rt_vector))
    hist_norms = np.linalg.norm(hist_matrix, axis=1)

    denominator = rt_norm * hist_norms
    with np.errstate(divide="ignore", invalid="ignore"):
        scores = np.divide(hist_matrix.dot(rt_vector), denominator, out=np.zeros(len(candidates)), where=denominator > 0)

    rt_is_exam = str(row.get("ProcedureCode", "")).upper().strip() in EXAM_CODES
    if not rt_is_exam:
        bad_exam_mismatch = candidates["Flag"].fillna("").astype(str).str.lower().eq("two exams in one day")
        scores[bad_exam_mismatch.to_numpy()] = 0.0
    logger.info("Similarity candidate scoring complete")
    return scores


def _z_vector(row: pd.Series, anomaly_stats: dict[str, Any]) -> np.ndarray:
    means = anomaly_stats.get("means", {})
    stds = anomaly_stats.get("stds", {})
    values = []
    for feature in SIMILARITY_FEATURES:
        mean = float(means.get(feature, 0.0) or 0.0)
        std = float(stds.get(feature, 1.0) or 1.0)
        if std == 0:
            std = 1.0
        value = float(row.get(feature, 0.0) or 0.0)
        values.append((value - mean) / std)
    return np.array(values, dtype=float)


def _pattern_family(pattern: str) -> str:
    return PATTERN_FAMILIES.get(pattern, "Historical Pattern")


def _case_priority(pattern: str) -> str:
    return PATTERN_PRIORITIES.get(pattern, "Medium")


def _default_result() -> dict[str, Any]:
    logger.info("Using default historical similarity result")
    return {
        "similarity_score": 0.0,
        "similarity_above_threshold": False,
        "historical_pattern": "NONE",
        "historical_pattern_family": "NONE",
        "historical_pattern_confidence": 0.0,
        "historical_case_priority": "LOW",
        "historical_claim_id": "",
        "historical_member_id": "",
        "historical_line_number": 0,
    }
