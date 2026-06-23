import logging

RISK_WEIGHTS = {
    "rules": 0.6,
    "pattern": 0.3,
    "unexpected": 0.1,
}

RISK_THRESHOLDS = {
    "high": 0.55,
    "medium": 0.40,
}

MAX_RULE_COUNT = 9
RULE_ACCELERATION_EXPONENT = 0.75

RISK_ESCALATION = {
    "moderate_start": 0.40,
    "moderate_end": 0.55,
    "moderate_headroom_fraction": 0.12,
    "severe_start": 0.55,
    "severe_end": 0.75,
    "severe_headroom_fraction": 0.28,
}

logger = logging.getLogger(__name__)


def _clamp_unit(value: float) -> float:
    return min(max(float(value), 0.0), 1.0)


def _smoothstep(start: float, end: float, value: float) -> float:
    if end <= start:
        raise ValueError("Smoothstep end must be greater than start.")
    progress = _clamp_unit((float(value) - start) / (end - start))
    return progress * progress * (3.0 - 2.0 * progress)


def normalize_rule_count(rule_count: float, maximum: int = MAX_RULE_COUNT) -> float:
    """Convert rule occurrences to a bounded, progressively punitive score."""
    if maximum <= 1:
        raise ValueError("Maximum rule count must be greater than 1.")

    capped_count = min(max(float(rule_count), 0.0), float(maximum))
    if capped_count <= 1.0:
        return capped_count / float(maximum)

    anchor = 1.0 / float(maximum)
    progress_after_first = (capped_count - 1.0) / float(maximum - 1)
    accelerated = anchor + (1.0 - anchor) * (
        progress_after_first ** RULE_ACCELERATION_EXPONENT
    )
    return _clamp_unit(accelerated)


def escalate_risk_score(base_score: float) -> float:
    """Apply smooth moderate and severe escalation bands to a base score."""
    base = _clamp_unit(base_score)
    remaining_headroom = 1.0 - base
    moderate_penalty = (
        remaining_headroom
        * RISK_ESCALATION["moderate_headroom_fraction"]
        * _smoothstep(
            RISK_ESCALATION["moderate_start"],
            RISK_ESCALATION["moderate_end"],
            base,
        )
    )
    severe_penalty = (
        remaining_headroom
        * RISK_ESCALATION["severe_headroom_fraction"]
        * _smoothstep(
            RISK_ESCALATION["severe_start"],
            RISK_ESCALATION["severe_end"],
            base,
        )
    )
    return _clamp_unit(base + moderate_penalty + severe_penalty)


def calculate_final_risk_score(
    rule_count_normalized: float,
    pattern_confidence: float,
    unexpected_pattern_score: float,
) -> float:
    logger.info(
        "Calculating final risk score: rules=%.6f pattern=%.6f unexpected=%.6f",
        rule_count_normalized,
        pattern_confidence,
        unexpected_pattern_score,
    )
    base_score = (
        RISK_WEIGHTS["rules"] * _clamp_unit(rule_count_normalized)
        + RISK_WEIGHTS["pattern"] * _clamp_unit(pattern_confidence)
        + RISK_WEIGHTS["unexpected"] * _clamp_unit(unexpected_pattern_score)
    )
    score = escalate_risk_score(base_score)
    rounded = round(score, 6)
    logger.info(
        "Final risk score calculated: base=%.6f escalated=%.6f",
        base_score,
        rounded,
    )
    return rounded


def assign_risk_level(score: float) -> str:
    logger.info("Assigning risk level for score=%.6f", score)
    if score >= RISK_THRESHOLDS["high"]:
        logger.info("Risk level assigned: High")
        return "High"
    if score >= RISK_THRESHOLDS["medium"]:
        logger.info("Risk level assigned: Medium")
        return "Medium"
    logger.info("Risk level assigned: Low")
    return "Low"


def recommended_action(risk_level: str, category: str) -> str:
    logger.info("Selecting recommended action for risk_level=%s category=%s", risk_level, category)
    if category == "Historical Fraud Pattern Match":
        if risk_level == "High":
            action = "Escalate for priority investigation based on similarity to a known historical pattern."
            logger.info("Recommended action selected: %s", action)
            return action
        action = "Review against the matched historical pattern before final disposition."
        logger.info("Recommended action selected: %s", action)
        return action
    if risk_level == "High":
        action = "Escalate for priority investigation and request supporting documentation."
        logger.info("Recommended action selected: %s", action)
        return action
    if risk_level == "Medium":
        if category == "Documentation Gap":
            action = "Request missing documentation before final disposition."
            logger.info("Recommended action selected: %s", action)
            return action
        if category == "Coding Review":
            action = "Review coding and modifier support before payment release."
            logger.info("Recommended action selected: %s", action)
            return action
        action = "Monitor claim patterns and consider selective review."
        logger.info("Recommended action selected: %s", action)
        return action
    action = "No immediate action required; retain for routine monitoring."
    logger.info("Recommended action selected: %s", action)
    return action
