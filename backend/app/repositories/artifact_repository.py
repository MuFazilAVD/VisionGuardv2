from __future__ import annotations

import json
import logging
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

logger = logging.getLogger(__name__)


class ArtifactRepository:
    def __init__(self) -> None:
        logger.info("Initializing artifact repository")
        ensure_directories()

    def artifacts_exist(self) -> bool:
        missing = [path.name for path in REQUIRED_ARTIFACTS if not path.exists()]
        exists = not missing
        logger.info("Checking required artifacts: exists=%s missing=%s", exists, missing)
        return exists

    def list_artifacts(self) -> list[str]:
        if not ARTIFACT_DIR.exists():
            logger.info("Artifact directory missing at %s", ARTIFACT_DIR)
            return []
        artifacts = sorted(path.name for path in ARTIFACT_DIR.iterdir() if path.is_file())
        logger.info("Listed %d artifact file(s)", len(artifacts))
        return artifacts

    def save_joblib(self, path: Path, value: Any) -> None:
        logger.info("Saving joblib artifact to %s", path)
        ensure_directories()
        joblib.dump(value, path)
        logger.info("Saved joblib artifact to %s", path)

    def load_joblib(self, path: Path) -> Any:
        logger.info("Loading joblib artifact from %s", path)
        value = joblib.load(path)
        logger.info("Loaded joblib artifact from %s", path)
        return value

    def save_json(self, path: Path, value: Any) -> None:
        logger.info("Saving JSON artifact to %s", path)
        ensure_directories()
        path.write_text(json.dumps(value, indent=2), encoding="utf-8")
        logger.info("Saved JSON artifact to %s", path)

    def load_json(self, path: Path) -> dict[str, Any]:
        logger.info("Loading JSON artifact from %s", path)
        value = json.loads(path.read_text(encoding="utf-8"))
        logger.info("Loaded JSON artifact from %s", path)
        return value

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
        logger.info("Saving full training artifact bundle")
        self.save_joblib(RF_MODEL_PATH, model)
        self.save_joblib(FEATURE_PIPELINE_PATH, feature_pipeline)
        self.save_joblib(ENCODERS_PATH, encoders)
        self.save_json(METADATA_PATH, metadata)
        self.save_json(ANOMALY_STATS_PATH, anomaly_stats)
        self.save_json(TRAINING_METRICS_PATH, metrics)
        logger.info("Full training artifact bundle saved")

    def load_training_bundle(self) -> dict[str, Any]:
        logger.info("Loading full training artifact bundle")
        bundle = {
            "model": self.load_joblib(RF_MODEL_PATH),
            "feature_pipeline": self.load_joblib(FEATURE_PIPELINE_PATH),
            "encoders": self.load_joblib(ENCODERS_PATH),
            "metadata": self.load_json(METADATA_PATH),
            "anomaly_stats": self.load_json(ANOMALY_STATS_PATH),
            "metrics": self.load_json(TRAINING_METRICS_PATH),
        }
        logger.info("Full training artifact bundle loaded")
        return bundle
