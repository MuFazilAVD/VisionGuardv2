from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
import logging
from typing import Any

import pandas as pd

from app.pipelines.anomaly import score_anomalies
from app.pipelines.features import add_billed_allowed_ratio, prepare_feature_frame
from app.pipelines.risk_scoring import assign_risk_level, calculate_final_risk_score, recommended_action
from app.pipelines.rules_engine import REALTIME_RULE_COLUMNS, apply_rules, triggered_indicators
from app.pipelines.similarity import score_historical_similarity
from app.repositories.artifact_repository import ArtifactRepository
from app.repositories.data_repository import DataRepository
from app.services.llm_service import LLMNarrativeService
from app.services.training_service import TrainingService

logger = logging.getLogger(__name__)


class RealtimeService:
    def __init__(self) -> None:
        logger.info("Initializing realtime service")
        self.artifact_repository = ArtifactRepository()
        self.data_repository = DataRepository()
        self.training_service = TrainingService()
        self.llm_service = LLMNarrativeService()

    def analyze_claims(self, claims: list[dict[str, Any]]) -> dict[str, Any]:
        logger.info("Starting realtime analysis for %d claim(s)", len(claims))
        if not claims:
            logger.info("Realtime analysis rejected because no claims were submitted")
            raise ValueError("Submit at least one claim for realtime assessment.")

        if not self.training_service.artifacts_current():
            logger.info("Training artifacts are missing or stale; retraining before realtime scoring")
            self.training_service.retrain()
        else:
            logger.info("Training artifacts are current")

        logger.info("Loading training bundle for realtime scoring")
        bundle = self.artifact_repository.load_training_bundle()
        model = bundle["model"]
        feature_pipeline = bundle["feature_pipeline"]
        label_encoder = bundle["encoders"]["label_encoder"]
        anomaly_stats = bundle["anomaly_stats"]

        incoming = pd.DataFrame(claims)
        logger.info("Incoming claims frame created with shape=%s", incoming.shape)
        historical = self.data_repository.load_historical_claims()
        logger.info("Loaded historical context with %d row(s)", len(historical))
        ruled = apply_rules(incoming, mode="realtime", context_df=historical)
        logger.info("Realtime rules applied; total triggered flags=%d", int(ruled["Rule_Flag_Count"].sum()))
        scored_base = add_billed_allowed_ratio(ruled)
        features = prepare_feature_frame(scored_base)
        logger.info("Prepared realtime feature frame with shape=%s", features.shape)
        encoded = feature_pipeline.transform(features)
        logger.info("Realtime feature encoding complete with shape=%s", getattr(encoded, "shape", "<unknown>"))
        probabilities = model.predict_proba(encoded)
        predictions = model.predict(encoded)
        predicted_patterns = label_encoder.inverse_transform(predictions)
        confidence_scores = probabilities.max(axis=1)
        logger.info("ML predictions completed for %d claim(s)", len(predicted_patterns))
        anomaly_scores, anomaly_normalized, top_features = score_anomalies(scored_base, anomaly_stats)
        logger.info("Anomaly scoring completed for %d claim(s)", len(anomaly_scores))
        historical_ruled = apply_rules(historical, mode="historical")
        similarity_matches = score_historical_similarity(scored_base, historical_ruled, anomaly_stats)
        logger.info("Historical similarity scoring completed for %d claim(s)", len(similarity_matches))

        assessments = []
        for idx, row in scored_base.reset_index(drop=True).iterrows():
            rule_count = int(row.get("Rule_Flag_Count", 0) or 0)
            rule_count_normalized = min(rule_count / float(len(REALTIME_RULE_COLUMNS)), 1.0)
            confidence = float(confidence_scores[idx])
            unexpected = float(anomaly_normalized[idx])
            final_score = calculate_final_risk_score(rule_count_normalized, confidence, unexpected)
            risk_level = assign_risk_level(final_score)
            indicators = triggered_indicators(row, mode="realtime")
            similarity = similarity_matches[idx]
            category, top_reason = self._categorize(indicators, top_features[idx], similarity)
            action = recommended_action(risk_level, category)
            model_pattern = str(predicted_patterns[idx])
            final_pattern = (
                str(similarity["historical_pattern"])
                if similarity["similarity_above_threshold"]
                else model_pattern
            )

            context = {
                "claim_id": str(row.get("ClaimId", "")),
                "member_id": str(row.get("MemberId", "")),
                "line_number": int(row.get("LineNumber", 1) or 1),
                "provider_npi": str(row.get("ProviderNPI", "")),
                "procedure_code": str(row.get("ProcedureCode", "")),
                "procedure_name": str(row.get("ProcedureName", "")),
                "state": str(row.get("State", "")),
                "lob": str(row.get("LOB", "")),
                "coverage_code": str(row.get("CoverageCode", "")),
                "amount_charged": float(row.get("AmtCharged", 0) or 0),
                "amount_eligible": float(row.get("AmtEligible", 0) or 0),
                "allowed_units": float(row.get("AllowedUnits", 0) or 0),
                "risk_level": risk_level,
                "final_risk_score": final_score,
                "confidence_level": round(confidence, 6),
                "unexpected_pattern_score": round(unexpected, 6),
                "predicted_pattern": final_pattern,
                "top_reason": top_reason,
                "recommended_action": action,
                "triggered_indicators": self._public_indicators(indicators),
                "historical_match": {
                    "similarity_score": similarity["similarity_score"],
                    "above_threshold": similarity["similarity_above_threshold"],
                    "pattern": similarity["historical_pattern"],
                    "pattern_family": similarity["historical_pattern_family"],
                    "confidence": similarity["historical_pattern_confidence"],
                    "case_priority": similarity["historical_case_priority"],
                },
            }
            narrative = self.llm_service.generate_for_claim(context)
            assessments.append(
                {
                    **context,
                    "rule_flag_count": rule_count,
                    "category": category,
                    "narrative": narrative,
                    "details": {
                        "billed_allowed_ratio": round(float(row.get("BilledAllowedRatio", 0) or 0), 6),
                        "unexpected_pattern_driver": top_features[idx],
                        "raw_unexpected_pattern_score": round(float(anomaly_scores[idx]), 6),
                        "rule_count_normalization_denominator": len(REALTIME_RULE_COLUMNS),
                        "similarity_score": similarity["similarity_score"],
                        "similarity_above_threshold": similarity["similarity_above_threshold"],
                        "historical_pattern": similarity["historical_pattern"],
                        "historical_pattern_family": similarity["historical_pattern_family"],
                        "historical_pattern_confidence": similarity["historical_pattern_confidence"],
                        "historical_case_priority": similarity["historical_case_priority"],
                        "historical_claim_id": similarity["historical_claim_id"],
                        "historical_member_id": similarity["historical_member_id"],
                        "historical_line_number": similarity["historical_line_number"],
                        "ml_predicted_pattern": model_pattern,
                        "service_date": str(row.get("ServiceDateFrom", "")),
                        "gender": str(row.get("Gender", "")),
                        "age": float(row.get("Age", 0) or 0),
                    },
                }
            )
            logger.info(
                "Realtime assessment built: claim_id=%s line=%s risk=%s score=%.6f rules=%d pattern=%s",
                context["claim_id"],
                context["line_number"],
                risk_level,
                final_score,
                rule_count,
                final_pattern,
            )

        batch_summary = self._build_batch_summary(assessments)
        batch_narrative = self.llm_service.generate_for_batch(
            {
                **batch_summary,
                "top_categories": self._top_counts(assessment["category"] for assessment in assessments),
                "top_reasons": self._top_counts(assessment["top_reason"] for assessment in assessments),
            }
        )

        result = {
            "processed_at": datetime.now(UTC).isoformat(),
            "count": len(assessments),
            "batch_summary": {
                **batch_summary,
                "summary": batch_narrative["summary"],
                "metadata": batch_narrative["metadata"],
            },
            "assessments": assessments,
        }
        logger.info("Realtime analysis completed with %d assessment(s)", len(assessments))
        return result

    def _build_batch_summary(self, assessments: list[dict[str, Any]]) -> dict[str, Any]:
        total = len(assessments)
        high = sum(1 for assessment in assessments if assessment["risk_level"] == "High")
        medium = sum(1 for assessment in assessments if assessment["risk_level"] == "Medium")
        low = sum(1 for assessment in assessments if assessment["risk_level"] == "Low")
        average_score = (
            sum(float(assessment["final_risk_score"]) for assessment in assessments) / total
            if total
            else 0.0
        )

        logger.info(
            "Batch summary counts: total=%d high=%d medium=%d low=%d",
            total,
            high,
            medium,
            low,
        )
        return {
            "total_claims": total,
            "fraud_count": high,
            "suspicious_count": medium,
            "clean_count": low,
            "high_risk_count": high,
            "medium_risk_count": medium,
            "low_risk_count": low,
            "review_count": high + medium,
            "average_risk_score": round(float(average_score), 6),
        }

    def _top_counts(self, values: Any) -> list[dict[str, Any]]:
        counts = Counter(str(value) for value in values if str(value or "").strip())
        return [{"name": name, "count": count} for name, count in counts.most_common(3)]

    def _public_indicators(self, indicators: list[dict[str, Any]]) -> list[dict[str, str]]:
        logger.info("Preparing %d public triggered indicator(s)", len(indicators))
        return [
            {
                "rule_id": item["rule_id"],
                "name": item["name"],
                "description": item["description"],
                "severity": item["severity"],
                "category": item["category"],
            }
            for item in indicators
        ]

    def _categorize(
        self,
        indicators: list[dict[str, Any]],
        top_feature: str,
        similarity: dict[str, Any],
    ) -> tuple[str, str]:
        if similarity["similarity_above_threshold"]:
            pattern = similarity["historical_pattern"]
            family = similarity["historical_pattern_family"]
            logger.info("Categorized claim as historical match: pattern=%s family=%s", pattern, family)
            return "Historical Fraud Pattern Match", f"Matches historical pattern: {pattern} ({family})"
        if indicators:
            first = indicators[0]
            logger.info("Categorized claim from first triggered indicator: %s", first["name"])
            return first["category"], first["name"]
        logger.info("Categorized claim from anomaly top feature: %s", top_feature)
        return "Billing Pattern", f"Unexpected pattern in {top_feature}"
