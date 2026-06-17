from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

from app.pipelines.anomaly import compute_anomaly_stats
from app.pipelines.features import CATEGORICAL_FEATURES, NUMERIC_FEATURES, build_feature_pipeline, prepare_feature_frame
from app.pipelines.risk_scoring import RISK_THRESHOLDS, RISK_WEIGHTS
from app.pipelines.rules_engine import HISTORICAL_RULE_COLUMNS, REALTIME_RULE_COLUMNS, RULE_DEFINITIONS, apply_rules
from app.repositories.artifact_repository import ArtifactRepository
from app.repositories.data_repository import DataRepository
from app.services.sample_data_service import SampleDataService
from app.utils.paths import METADATA_PATH, TRAINING_METRICS_PATH


class TrainingService:
    def __init__(self) -> None:
        self.sample_data_service = SampleDataService()
        self.data_repository = DataRepository()
        self.artifact_repository = ArtifactRepository()

    def retrain(self) -> dict[str, Any]:
        self.sample_data_service.ensure_sample_data()
        historical = self.data_repository.load_historical_claims()
        self.data_repository.load_rules()
        historical_fingerprint = self.data_repository.historical_fingerprint()

        rules_df = apply_rules(historical, mode="historical")
        labeled = rules_df[rules_df["Flag"].fillna("").astype(str).str.strip() != ""].copy()
        labeled["Flag"] = labeled["Flag"].replace({"Two Exams in One day": "Two Exams in One Day"})
        X = prepare_feature_frame(labeled)
        y_text = labeled["Flag"].astype(str)

        label_encoder = LabelEncoder()
        y = label_encoder.fit_transform(y_text)

        stratify = y if min(pd.Series(y).value_counts()) >= 2 else None
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=0.2,
            random_state=42,
            stratify=stratify,
        )

        feature_pipeline = build_feature_pipeline()
        X_train_encoded = feature_pipeline.fit_transform(X_train)
        X_test_encoded = feature_pipeline.transform(X_test)

        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=8,
            random_state=42,
            n_jobs=-1,
            class_weight="balanced_subsample",
        )
        model.fit(X_train_encoded, y_train)

        predictions = model.predict(X_test_encoded)
        trained_at = datetime.now(UTC).isoformat()
        artifact_version = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        metrics = {
            "trained_at": trained_at,
            "accuracy": round(float(accuracy_score(y_test, predictions)), 6),
            "f1_weighted": round(float(f1_score(y_test, predictions, average="weighted")), 6),
            "train_records": int(len(X_train)),
            "test_records": int(len(X_test)),
            "class_counts": y_text.value_counts().to_dict(),
            "dataset_statistics": {
                "historical_records": int(len(historical)),
                "labeled_records": int(len(labeled)),
                "average_rule_count": round(float(rules_df["Rule_Flag_Count"].mean()), 4),
                "max_rule_count": int(rules_df["Rule_Flag_Count"].max()),
                "historical_dataset_sha256": historical_fingerprint["sha256"] if historical_fingerprint else None,
            },
            "artifact_files": [
                "rf_model.joblib",
                "feature_pipeline.joblib",
                "encoders.joblib",
                "metadata.json",
                "anomaly_stats.json",
                "training_metrics.json",
            ],
        }

        anomaly_stats = compute_anomaly_stats(rules_df)
        index_to_label = {str(index): label for index, label in enumerate(label_encoder.classes_)}
        metadata = {
            "artifact_version": artifact_version,
            "trained_at": trained_at,
            "record_count": int(len(historical)),
            "numeric_features": NUMERIC_FEATURES,
            "categorical_features": CATEGORICAL_FEATURES,
            "classes": list(label_encoder.classes_),
            "index_to_label": index_to_label,
            "rule_mode": "historical",
            "historical_rules": HISTORICAL_RULE_COLUMNS,
            "realtime_supported_rules": REALTIME_RULE_COLUMNS,
            "rule_definitions": [
                {
                    "rule_id": rule.rule_id,
                    "column": rule.column,
                    "name": rule.name,
                    "description": rule.description,
                    "severity": rule.severity,
                    "category": rule.category,
                    "realtime_supported": rule.realtime_supported,
                }
                for rule in RULE_DEFINITIONS
            ],
            "risk_weights": RISK_WEIGHTS,
            "risk_thresholds": RISK_THRESHOLDS,
            "historical_dataset": historical_fingerprint,
        }

        encoders = {
            "label_encoder": label_encoder,
            "numeric_features": NUMERIC_FEATURES,
            "categorical_features": CATEGORICAL_FEATURES,
        }
        self.artifact_repository.save_training_bundle(
            model=model,
            feature_pipeline=feature_pipeline,
            encoders=encoders,
            metadata=metadata,
            anomaly_stats=anomaly_stats,
            metrics=metrics,
        )

        return {
            "status": "trained",
            "trained_at": trained_at,
            "metrics": metrics,
            "artifact_version": artifact_version,
        }

    def status(self) -> dict[str, Any]:
        trained = self.artifact_repository.artifacts_exist()
        artifacts = self.artifact_repository.list_artifacts()
        if not trained:
            return {
                "trained": False,
                "last_training_date": None,
                "metrics": None,
                "artifact_version": None,
                "artifacts": artifacts,
            }

        metadata = self.artifact_repository.load_json(METADATA_PATH)
        metrics = self.artifact_repository.load_json(TRAINING_METRICS_PATH)
        return {
            "trained": True,
            "last_training_date": metadata.get("trained_at"),
            "metrics": metrics,
            "artifact_version": metadata.get("artifact_version"),
            "artifacts": artifacts,
            "artifacts_current": self.artifacts_current(),
        }

    def artifacts_current(self) -> bool:
        if not self.artifact_repository.artifacts_exist():
            return False
        self.sample_data_service.ensure_sample_data()
        current = self.data_repository.historical_fingerprint()
        if current is None:
            return False

        try:
            metadata = self.artifact_repository.load_json(METADATA_PATH)
        except Exception:
            return False

        saved = metadata.get("historical_dataset") or {}
        return saved.get("sha256") == current.get("sha256")
