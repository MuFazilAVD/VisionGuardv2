RISK_WEIGHTS = {
    "rules": 0.4,
    "pattern": 0.3,
    "unexpected": 0.3,
}

RISK_THRESHOLDS = {
    "high": 0.75,
    "medium": 0.50,
}


def calculate_final_risk_score(
    rule_count_normalized: float,
    pattern_confidence: float,
    unexpected_pattern_score: float,
) -> float:
    score = (
        RISK_WEIGHTS["rules"] * rule_count_normalized
        + RISK_WEIGHTS["pattern"] * pattern_confidence
        + RISK_WEIGHTS["unexpected"] * unexpected_pattern_score
    )
    return round(float(score), 6)


def assign_risk_level(score: float) -> str:
    if score >= RISK_THRESHOLDS["high"]:
        return "High"
    if score >= RISK_THRESHOLDS["medium"]:
        return "Medium"
    return "Low"


def recommended_action(risk_level: str, category: str) -> str:
    if category == "Historical Fraud Pattern Match":
        if risk_level == "High":
            return "Escalate for priority investigation based on similarity to a known historical pattern."
        return "Review against the matched historical pattern before final disposition."
    if risk_level == "High":
        return "Escalate for priority investigation and request supporting documentation."
    if risk_level == "Medium":
        if category == "Documentation Gap":
            return "Request missing documentation before final disposition."
        if category == "Coding Review":
            return "Review coding and modifier support before payment release."
        return "Monitor claim patterns and consider selective review."
    return "No immediate action required; retain for routine monitoring."
