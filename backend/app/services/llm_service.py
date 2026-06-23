from __future__ import annotations

import json
import logging
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

logger = logging.getLogger(__name__)


class LLMNarrativeService:
    def generate_for_claim(self, claim_data: dict[str, Any]) -> dict[str, Any]:
        logger.info("Generating narrative for claim_id=%s", claim_data.get("claim_id", "<missing>"))
        settings = get_settings()
        if not settings.openai_api_key or not settings.openai_model:
            logger.info("LLM narrative using fallback because model configuration is incomplete")
            return self._fallback(claim_data, "OPENAI_API_KEY or OPENAI_MODEL is not configured")

        try:
            logger.info("Calling LLM model %s for claim narrative", settings.openai_model)
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
            logger.info("LLM narrative generated successfully for claim_id=%s", claim_data.get("claim_id", "<missing>"))
            return narrative
        except Exception as exc:  # LLM failure must never block scoring.
            logger.exception("LLM narrative generation failed; using fallback")
            return self._fallback(claim_data, str(exc))

    def generate_for_batch(self, batch_data: dict[str, Any]) -> dict[str, Any]:
        logger.info("Generating batch summary for %d claim(s)", int(batch_data.get("total_claims") or 0))
        settings = get_settings()
        if not settings.openai_api_key or not settings.openai_model:
            logger.info("Batch summary using fallback because model configuration is incomplete")
            return self._batch_fallback(batch_data, "OPENAI_API_KEY or OPENAI_MODEL is not configured")

        try:
            logger.info("Calling LLM model %s for batch summary", settings.openai_model)
            client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
            completion = client.chat.completions.create(
                model=settings.openai_model,
                temperature=0.2,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You write concise batch-level claims assessment summaries for business users. "
                            "Use one short sentence, no more than 28 words. Avoid technical model terms. "
                            "Return valid JSON only with key: summary."
                        ),
                    },
                    {
                        "role": "user",
                        "content": json.dumps(self._batch_business_context(batch_data), default=str),
                    },
                ],
            )
            text = completion.choices[0].message.content or "{}"
            parsed = json.loads(text)
            logger.info("LLM batch summary generated successfully")
            return {
                "summary": self._concise_text(str(parsed.get("summary") or "Batch assessment completed.")),
                "metadata": {
                    "model_used": settings.openai_model,
                    "llm_success": True,
                    "fallback_reason": None,
                },
            }
        except Exception as exc:  # LLM failure must never block scoring.
            logger.exception("LLM batch summary generation failed; using fallback")
            return self._batch_fallback(batch_data, str(exc))

    def _coerce_narrative(self, value: dict[str, Any]) -> dict[str, Any]:
        logger.info("Coercing LLM narrative response")
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
        logger.info("Building deterministic narrative fallback: reason=%s", reason)
        risk_level = claim_data.get("risk_level", "Low")
        indicators = claim_data.get("triggered_indicators", [])
        indicator_names = [item.get("name", "Risk indicator") for item in indicators]
        rule_count = int(claim_data.get("rule_flag_count") or len(indicator_names))
        top_reason = claim_data.get("top_reason") or "No dominant concern identified"
        action = claim_data.get("recommended_action") or "Retain for routine monitoring."
        score = float(claim_data.get("final_risk_score") or 0.0)

        if indicator_names:
            summary = (
                f"This claim is rated {risk_level} risk with {rule_count} review "
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

    def _batch_fallback(self, batch_data: dict[str, Any], reason: str) -> dict[str, Any]:
        logger.info("Building deterministic batch summary fallback: reason=%s", reason)
        total = int(batch_data.get("total_claims") or 0)
        fraud = int(batch_data.get("fraud_count") or 0)
        suspicious = int(batch_data.get("suspicious_count") or 0)
        clean = int(batch_data.get("clean_count") or 0)

        if fraud:
            summary = (
                f"{total} claims processed: {fraud} fraud review case(s), "
                f"{suspicious} suspicious, and {clean} clean."
            )
        elif suspicious:
            summary = (
                f"{total} claims processed with {suspicious} suspicious case(s) "
                f"and {clean} clean; prioritize selective review."
            )
        else:
            summary = f"{total} claims processed with no fraud review cases; {clean} clean case(s)."

        return {
            "summary": self._concise_text(summary),
            "metadata": {
                "model_used": "deterministic-fallback",
                "llm_success": False,
                "fallback_reason": reason,
            },
        }

    def _concise_text(self, value: str, max_words: int = 32) -> str:
        text = " ".join(value.strip().split())
        words = text.split()
        if len(words) <= max_words:
            return text
        return " ".join(words[:max_words]).rstrip(".,;:") + "."

    def _business_context(self, claim_data: dict[str, Any]) -> dict[str, Any]:
        logger.info("Building business context for LLM narrative")
        return {
            "claim": {
                "claim_id": claim_data.get("claim_id"),
                "line_number": claim_data.get("line_number"),
                "line_numbers": claim_data.get("line_numbers"),
                "line_count": claim_data.get("line_count"),
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

    def _batch_business_context(self, batch_data: dict[str, Any]) -> dict[str, Any]:
        logger.info("Building business context for LLM batch summary")
        return {
            "batch": {
                "total_claims": batch_data.get("total_claims"),
                "fraud_count": batch_data.get("fraud_count"),
                "suspicious_count": batch_data.get("suspicious_count"),
                "clean_count": batch_data.get("clean_count"),
                "review_count": batch_data.get("review_count"),
                "average_risk_score": batch_data.get("average_risk_score"),
            },
            "risk_mix": {
                "high": batch_data.get("high_risk_count"),
                "medium": batch_data.get("medium_risk_count"),
                "low": batch_data.get("low_risk_count"),
            },
            "top_categories": batch_data.get("top_categories", []),
            "top_reasons": batch_data.get("top_reasons", []),
        }
