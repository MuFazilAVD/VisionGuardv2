import logging

RISK_WEIGHTS = {
    "rules": 0.6,
    "pattern": 0.3,
    "unexpected": 0.1,
}

RISK_THRESHOLDS = {
    "high": 0.5,
    "medium": 0.35,
}

logger = logging.getLogger(__name__)


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
    score = (
        RISK_WEIGHTS["rules"] * rule_count_normalized
        + RISK_WEIGHTS["pattern"] * pattern_confidence
        + RISK_WEIGHTS["unexpected"] * unexpected_pattern_score
    )
    rounded = round(float(score), 6)
    logger.info("Final risk score calculated: %.6f", rounded)
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
