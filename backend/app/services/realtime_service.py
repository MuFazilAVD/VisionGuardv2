from __future__ import annotations

from datetime import UTC, datetime
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


class RealtimeService:
    def __init__(self) -> None:
        self.artifact_repository = ArtifactRepository()
        self.data_repository = DataRepository()
        self.training_service = TrainingService()
        self.llm_service = LLMNarrativeService()

    def analyze_claims(self, claims: list[dict[str, Any]]) -> dict[str, Any]:
        if not 1 <= len(claims) <= 5:
            raise ValueError("Submit between 1 and 5 claims for realtime assessment.")

        if not self.training_service.artifacts_current():
            self.training_service.retrain()

        bundle = self.artifact_repository.load_training_bundle()
        model = bundle["model"]
        feature_pipeline = bundle["feature_pipeline"]
        label_encoder = bundle["encoders"]["label_encoder"]
        anomaly_stats = bundle["anomaly_stats"]

        incoming = pd.DataFrame(claims)
        historical = self.data_repository.load_historical_claims()
        ruled = apply_rules(incoming, mode="realtime", context_df=historical)
        scored_base = add_billed_allowed_ratio(ruled)
        features = prepare_feature_frame(scored_base)
        encoded = feature_pipeline.transform(features)
        probabilities = model.predict_proba(encoded)
        predictions = model.predict(encoded)
        predicted_patterns = label_encoder.inverse_transform(predictions)
        confidence_scores = probabilities.max(axis=1)
        anomaly_scores, anomaly_normalized, top_features = score_anomalies(scored_base, anomaly_stats)
        historical_ruled = apply_rules(historical, mode="historical")
        similarity_matches = score_historical_similarity(scored_base, historical_ruled, anomaly_stats)

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
                        "historical_line_number": similarity["historical_line_number"],
                        "ml_predicted_pattern": model_pattern,
                        "service_date": str(row.get("ServiceDateFrom", "")),
                        "gender": str(row.get("Gender", "")),
                        "age": float(row.get("Age", 0) or 0),
                    },
                }
            )

        return {
            "processed_at": datetime.now(UTC).isoformat(),
            "count": len(assessments),
            "assessments": assessments,
        }

    def _public_indicators(self, indicators: list[dict[str, Any]]) -> list[dict[str, str]]:
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
            return "Historical Fraud Pattern Match", f"Matches historical pattern: {pattern} ({family})"
        if indicators:
            first = indicators[0]
            return first["category"], first["name"]
        return "Billing Pattern", f"Unexpected pattern in {top_feature}"
