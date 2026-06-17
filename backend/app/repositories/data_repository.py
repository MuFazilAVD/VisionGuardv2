from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from app.utils.paths import HISTORICAL_CLAIMS_PATH, ROOT_REALTIME_CLAIMS, RULES_XLSX_PATH, ensure_directories


class DataRepository:
    def __init__(self) -> None:
        ensure_directories()

    def load_historical_claims(self) -> pd.DataFrame:
        return pd.read_csv(HISTORICAL_CLAIMS_PATH, dtype={"ProviderNPI": str, "ProcedureCode": str})

    def load_realtime_sample_claims(self) -> pd.DataFrame:
        if not ROOT_REALTIME_CLAIMS.exists():
            return pd.DataFrame()
        return pd.read_csv(ROOT_REALTIME_CLAIMS, dtype={"ProviderNPI": str, "ProcedureCode": str})

    def load_rules(self) -> pd.DataFrame:
        return pd.read_excel(RULES_XLSX_PATH)

    def historical_exists(self) -> bool:
        return HISTORICAL_CLAIMS_PATH.exists()

    def rules_exist(self) -> bool:
        return RULES_XLSX_PATH.exists()

    def historical_fingerprint(self) -> dict[str, Any] | None:
        return self._file_fingerprint(HISTORICAL_CLAIMS_PATH)

    def _file_fingerprint(self, path: Path) -> dict[str, Any] | None:
        if not path.exists():
            return None

        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)

        stat = path.stat()
        modified_at = datetime.fromtimestamp(stat.st_mtime, tz=UTC).isoformat()
        return {
            "path": str(path),
            "size_bytes": int(stat.st_size),
            "modified_at": modified_at,
            "sha256": digest.hexdigest(),
        }
