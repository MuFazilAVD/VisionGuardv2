from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_ROOT.parent
APP_ROOT = BACKEND_ROOT / "app"
DATA_DIR = APP_ROOT / "data"
ARTIFACT_DIR = BACKEND_ROOT / "artifacts"
ROOT_REALTIME_CLAIMS = REPO_ROOT / "realtime_claims.csv"

HISTORICAL_CLAIMS_PATH = DATA_DIR / "historical_claims.csv"
RULES_XLSX_PATH = DATA_DIR / "rules.xlsx"

RF_MODEL_PATH = ARTIFACT_DIR / "rf_model.joblib"
FEATURE_PIPELINE_PATH = ARTIFACT_DIR / "feature_pipeline.joblib"
ENCODERS_PATH = ARTIFACT_DIR / "encoders.joblib"
METADATA_PATH = ARTIFACT_DIR / "metadata.json"
ANOMALY_STATS_PATH = ARTIFACT_DIR / "anomaly_stats.json"
TRAINING_METRICS_PATH = ARTIFACT_DIR / "training_metrics.json"


def ensure_directories() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

