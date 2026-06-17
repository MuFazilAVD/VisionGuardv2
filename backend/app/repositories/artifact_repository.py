from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib

from app.utils.paths import (
    ANOMALY_STATS_PATH,
    ARTIFACT_DIR,
    ENCODERS_PATH,
    FEATURE_PIPELINE_PATH,
    METADATA_PATH,
    RF_MODEL_PATH,
    TRAINING_METRICS_PATH,
    ensure_directories,
)


REQUIRED_ARTIFACTS = [
    RF_MODEL_PATH,
    FEATURE_PIPELINE_PATH,
    ENCODERS_PATH,
    METADATA_PATH,
    ANOMALY_STATS_PATH,
    TRAINING_METRICS_PATH,
]


class ArtifactRepository:
    def __init__(self) -> None:
        ensure_directories()

    def artifacts_exist(self) -> bool:
        return all(path.exists() for path in REQUIRED_ARTIFACTS)

    def list_artifacts(self) -> list[str]:
        if not ARTIFACT_DIR.exists():
            return []
        return sorted(path.name for path in ARTIFACT_DIR.iterdir() if path.is_file())

    def save_joblib(self, path: Path, value: Any) -> None:
        ensure_directories()
        joblib.dump(value, path)

    def load_joblib(self, path: Path) -> Any:
        return joblib.load(path)

    def save_json(self, path: Path, value: Any) -> None:
        ensure_directories()
        path.write_text(json.dumps(value, indent=2), encoding="utf-8")

    def load_json(self, path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    def save_training_bundle(
        self,
        *,
        model: Any,
        feature_pipeline: Any,
        encoders: dict[str, Any],
        metadata: dict[str, Any],
        anomaly_stats: dict[str, Any],
        metrics: dict[str, Any],
    ) -> None:
        self.save_joblib(RF_MODEL_PATH, model)
        self.save_joblib(FEATURE_PIPELINE_PATH, feature_pipeline)
        self.save_joblib(ENCODERS_PATH, encoders)
        self.save_json(METADATA_PATH, metadata)
        self.save_json(ANOMALY_STATS_PATH, anomaly_stats)
        self.save_json(TRAINING_METRICS_PATH, metrics)

    def load_training_bundle(self) -> dict[str, Any]:
        return {
            "model": self.load_joblib(RF_MODEL_PATH),
            "feature_pipeline": self.load_joblib(FEATURE_PIPELINE_PATH),
            "encoders": self.load_joblib(ENCODERS_PATH),
            "metadata": self.load_json(METADATA_PATH),
            "anomaly_stats": self.load_json(ANOMALY_STATS_PATH),
            "metrics": self.load_json(TRAINING_METRICS_PATH),
        }

