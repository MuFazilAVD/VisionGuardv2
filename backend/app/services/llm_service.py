from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

from app.utils.config import get_settings


NARRATIVE_KEYS = [
    "executive_summary",
    "investigation_findings",
    "key_risk_indicators",
    "risk_classification",
    "recommended_review_actions",
]


class LLMNarrativeService:
    def generate_for_claim(self, claim_data: dict[str, Any]) -> dict[str, Any]:
        settings = get_settings()
        if not settings.openai_api_key or not settings.openai_model:
            return self._fallback(claim_data, "OPENAI_API_KEY or OPENAI_MODEL is not configured")

        try:
            client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
            completion = client.chat.completions.create(
                model=settings.openai_model,
                temperature=0.2,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You write concise claims investigation summaries for business users. "
                            "Avoid technical model terms. Return valid JSON only with keys: "
                            "executive_summary, investigation_findings, key_risk_indicators, "
                            "risk_classification, recommended_review_actions."
                        ),
                    },
                    {
                        "role": "user",
                        "content": json.dumps(self._business_context(claim_data), default=str),
                    },
                ],
            )
            text = completion.choices[0].message.content or "{}"
            parsed = json.loads(text)
            narrative = self._coerce_narrative(parsed)
            narrative["metadata"] = {
                "model_used": settings.openai_model,
                "llm_success": True,
                "fallback_reason": None,
            }
            return narrative
        except Exception as exc:  # LLM failure must never block scoring.
            return self._fallback(claim_data, str(exc))

    def _coerce_narrative(self, value: dict[str, Any]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        result["executive_summary"] = str(value.get("executive_summary") or "Claim assessment completed.")
        for key in ["investigation_findings", "key_risk_indicators", "recommended_review_actions"]:
            item = value.get(key) or []
            if isinstance(item, str):
                item = [item]
            result[key] = [str(entry) for entry in item if str(entry).strip()]
        result["risk_classification"] = str(value.get("risk_classification") or "Risk level assigned.")
        return result

    def _fallback(self, claim_data: dict[str, Any], reason: str) -> dict[str, Any]:
        risk_level = claim_data.get("risk_level", "Low")
        indicators = claim_data.get("triggered_indicators", [])
        indicator_names = [item.get("name", "Risk indicator") for item in indicators]
        top_reason = claim_data.get("top_reason") or "No dominant concern identified"
        action = claim_data.get("recommended_action") or "Retain for routine monitoring."
        score = float(claim_data.get("final_risk_score") or 0.0)

        if indicator_names:
            summary = (
                f"This claim is rated {risk_level} risk with {len(indicator_names)} review "
                f"indicator(s). The main concern is {top_reason.lower()}."
            )
        else:
            summary = f"This claim is rated {risk_level} risk with no rule-based indicators."

        return {
            "executive_summary": summary,
            "investigation_findings": [
                f"Overall claim assessment score is {score:.2f}.",
                f"Primary review focus: {top_reason}.",
            ],
            "key_risk_indicators": indicator_names or ["No rule-based indicators were triggered."],
            "risk_classification": f"{risk_level} risk based on indicators, pattern confidence, and billing consistency.",
            "recommended_review_actions": [action],
            "metadata": {
                "model_used": "deterministic-fallback",
                "llm_success": False,
                "fallback_reason": reason,
            },
        }

    def _business_context(self, claim_data: dict[str, Any]) -> dict[str, Any]:
        return {
            "claim": {
                "claim_id": claim_data.get("claim_id"),
                "line_number": claim_data.get("line_number"),
                "procedure_code": claim_data.get("procedure_code"),
                "procedure_name": claim_data.get("procedure_name"),
                "provider_npi": claim_data.get("provider_npi"),
                "state": claim_data.get("state"),
                "line_of_business": claim_data.get("lob"),
                "coverage": claim_data.get("coverage_code"),
                "amount_charged": claim_data.get("amount_charged"),
                "amount_eligible": claim_data.get("amount_eligible"),
                "allowed_units": claim_data.get("allowed_units"),
            },
            "assessment": {
                "risk_level": claim_data.get("risk_level"),
                "final_risk_score": claim_data.get("final_risk_score"),
                "confidence_level": claim_data.get("confidence_level"),
                "unexpected_pattern_score": claim_data.get("unexpected_pattern_score"),
                "predicted_pattern": claim_data.get("predicted_pattern"),
                "historical_match": claim_data.get("historical_match"),
                "top_reason": claim_data.get("top_reason"),
                "recommended_action": claim_data.get("recommended_action"),
                "triggered_indicators": claim_data.get("triggered_indicators"),
            },
        }
