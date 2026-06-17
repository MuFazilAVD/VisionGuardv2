from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from app.utils.paths import HISTORICAL_CLAIMS_PATH, ROOT_REALTIME_CLAIMS, RULES_XLSX_PATH, ensure_directories

logger = logging.getLogger(__name__)


class DataRepository:
    def __init__(self) -> None:
        logger.info("Initializing data repository")
        ensure_directories()

    def load_historical_claims(self) -> pd.DataFrame:
        logger.info("Loading historical claims from %s", HISTORICAL_CLAIMS_PATH)
        frame = pd.read_csv(HISTORICAL_CLAIMS_PATH, dtype={"ProviderNPI": str, "ProcedureCode": str})
        logger.info("Loaded historical claims: rows=%d columns=%d", len(frame), len(frame.columns))
        return frame

    def load_realtime_sample_claims(self) -> pd.DataFrame:
        if not ROOT_REALTIME_CLAIMS.exists():
            logger.info("Realtime sample claims file missing at %s", ROOT_REALTIME_CLAIMS)
            return pd.DataFrame()
        logger.info("Loading realtime sample claims from %s", ROOT_REALTIME_CLAIMS)
        frame = pd.read_csv(ROOT_REALTIME_CLAIMS, dtype={"ProviderNPI": str, "ProcedureCode": str})
        logger.info("Loaded realtime sample claims: rows=%d columns=%d", len(frame), len(frame.columns))
        return frame

    def load_rules(self) -> pd.DataFrame:
        logger.info("Loading business rules from %s", RULES_XLSX_PATH)
        try:
            frame = pd.read_excel(RULES_XLSX_PATH, sheet_name="Business Rules", dtype=str).fillna("")
        except ValueError:
            logger.info("Business Rules sheet missing; loading first workbook sheet")
            frame = pd.read_excel(RULES_XLSX_PATH, dtype=str).fillna("")
        logger.info("Loaded business rules: rows=%d columns=%d", len(frame), len(frame.columns))
        return frame

    def historical_exists(self) -> bool:
        exists = HISTORICAL_CLAIMS_PATH.exists()
        logger.info("Historical claims exists=%s path=%s", exists, HISTORICAL_CLAIMS_PATH)
        return exists

    def rules_exist(self) -> bool:
        exists = RULES_XLSX_PATH.exists()
        logger.info("Rules workbook exists=%s path=%s", exists, RULES_XLSX_PATH)
        return exists

    def historical_fingerprint(self) -> dict[str, Any] | None:
        logger.info("Computing historical claims fingerprint")
        return self._file_fingerprint(HISTORICAL_CLAIMS_PATH)

    def _file_fingerprint(self, path: Path) -> dict[str, Any] | None:
        if not path.exists():
            logger.info("Fingerprint skipped because file does not exist: %s", path)
            return None

        logger.info("Hashing file for fingerprint: %s", path)
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)

        stat = path.stat()
        modified_at = datetime.fromtimestamp(stat.st_mtime, tz=UTC).isoformat()
        fingerprint = {
            "path": str(path),
            "size_bytes": int(stat.st_size),
            "modified_at": modified_at,
            "sha256": digest.hexdigest(),
        }
        logger.info("Fingerprint computed for %s: size=%d sha256=%s", path, stat.st_size, fingerprint["sha256"])
        return fingerprint
