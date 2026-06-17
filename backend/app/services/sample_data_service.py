from __future__ import annotations

import logging
from random import Random
from typing import Any

import numpy as np
import pandas as pd

from app.pipelines.rules_engine import (
    CANONICAL_CLAIM_COLUMNS,
    executable_rule_definitions_for_workbook,
    rule_definitions_for_workbook,
)
from app.repositories.data_repository import DataRepository
from app.utils.paths import HISTORICAL_CLAIMS_PATH, ROOT_REALTIME_CLAIMS, RULES_XLSX_PATH, ensure_directories


FLAGS = [
    "CCI Edits Claims",
    "Exam after Comprehensive",
    "Bilateral Claims",
    "Two Exams in One Day",
]

VISION_EXAMS = [
    ("92002", "Intermediate Eye Exam New Patient"),
    ("92004", "Comprehensive Eye Exam New Patient"),
    ("92012", "Intermediate Eye Exam Established Patient"),
    ("92014", "Comprehensive Eye Exam"),
    ("S0620", "Routine Ophthalmological Examination New Patient"),
    ("S0621", "Routine Ophthalmological Examination Established Patient"),
]

MATERIAL_CODES = [
    ("V2020", "Frames"),
    ("V2100", "Single Vision Lenses"),
    ("V2200", "Bifocal Lenses"),
    ("V2300", "Trifocal Lenses"),
    ("V2750", "Anti-Reflective Coating"),
    ("V2755", "UV Coating"),
    ("V2760", "Scratch Resistant Coating"),
]

NON_VISION_CODES = [
    ("99213", "Office Visit Established Patient"),
    ("80050", "General Health Panel"),
    ("93000", "Electrocardiogram"),
]

DIAGNOSES = [
    ("H52.4", "Presbyopia"),
    ("H52.13", "Myopia, bilateral"),
    ("H52.03", "Hypermetropia, bilateral"),
    ("E11.9", "Diabetes type 2 without complications"),
    ("H25.13", "Age-related nuclear cataract, bilateral"),
]

STATES = ["OH", "FL", "TX", "CA", "NY", "PA", "GA", "IL", "NC", "AZ"]
LOBS = ["COMM", "MEDICARE", "MEDICAID"]
COVERAGE_CODES = ["PPO", "HMO", "EPO", "VSP"]
GENDERS = ["F", "M", "U"]

logger = logging.getLogger(__name__)


class SampleDataService:
    def __init__(self) -> None:
        logger.info("Initializing sample data service")
        self.data_repository = DataRepository()

    def ensure_sample_data(self, record_count: int = 8000) -> dict[str, Any]:
        logger.info("Ensuring sample data exists with target historical record count=%d", record_count)
        ensure_directories()
        if not HISTORICAL_CLAIMS_PATH.exists():
            logger.info("Historical sample claims missing; generating %d row(s)", record_count)
            self.generate_historical_claims(record_count)
        else:
            logger.info("Historical sample claims already exist at %s", HISTORICAL_CLAIMS_PATH)
        if not RULES_XLSX_PATH.exists():
            logger.info("Rules workbook missing; generating workbook")
            self.generate_rules_workbook()
        else:
            logger.info("Rules workbook already exists at %s", RULES_XLSX_PATH)
        return self.summary()

    def generate_rules_workbook(self) -> None:
        logger.info("Generating rules workbook at %s", RULES_XLSX_PATH)
        rules_df = pd.DataFrame(rule_definitions_for_workbook())
        executable_rules_df = pd.DataFrame(executable_rule_definitions_for_workbook())
        with pd.ExcelWriter(RULES_XLSX_PATH, engine="openpyxl") as writer:
            rules_df.to_excel(writer, index=False, sheet_name="Business Rules")
            executable_rules_df.to_excel(writer, index=False, sheet_name="Executable Rules")
        logger.info("Rules workbook generated with %d catalog row(s)", len(rules_df))

    def generate_historical_claims(self, record_count: int = 8000) -> None:
        logger.info("Generating %d historical sample claim row(s)", record_count)
        rng = np.random.default_rng(42)
        py_rng = Random(42)
        rows: list[dict[str, Any]] = []
        provider_pool = [f"{1100000000 + i}" for i in range(220)]
        special_providers = {
            "exam": "9000000001",
            "material": "9000000002",
            "billed": "9000000003",
            "addon": "9000000004",
        }

        for idx in range(record_count):
            row = self._base_row(idx, rng, py_rng, provider_pool)
            rows.append(row)

        self._inject_rule_coverage(rows, special_providers, rng, py_rng)
        df = pd.DataFrame(rows)
        df = df[CANONICAL_CLAIM_COLUMNS + ["Flag"]]
        df.to_csv(HISTORICAL_CLAIMS_PATH, index=False)
        logger.info("Historical sample claims written to %s", HISTORICAL_CLAIMS_PATH)

    def _base_row(
        self,
        idx: int,
        rng: np.random.Generator,
        py_rng: Random,
        provider_pool: list[str],
    ) -> dict[str, Any]:
        code, name = self._pick_procedure(rng, py_rng)
        flag = self._pick_flag(code, rng)
        diagnosis, long_description = py_rng.choice(DIAGNOSES)
        lob = str(rng.choice(LOBS, p=[0.63, 0.27, 0.10]))
        age = int(np.clip(rng.normal(47 if lob == "COMM" else 69, 16), 4, 92))
        eligible = self._eligible_amount(code, rng)
        charged_multiplier = float(np.clip(rng.normal(1.28, 0.28), 0.75, 2.15))
        charged = round(eligible * charged_multiplier, 2)
        units = 1
        paid = max(0.0, eligible - float(rng.choice([0, 5, 10, 15, 20])))
        modifier = "59" if rng.random() < 0.035 and (code.startswith("92") or code.startswith("V")) else ""
        if flag == "Bilateral Claims" and rng.random() < 0.45:
            modifier = "50"

        return {
            "ClaimId": f"H{idx + 1:06d}",
            "Gender": str(rng.choice(GENDERS, p=[0.52, 0.47, 0.01])),
            "Age": age,
            "ServiceDateFrom": (pd.Timestamp("2024-01-01") + pd.Timedelta(days=int(rng.integers(0, 365)))).strftime("%Y-%m-%d"),
            "PlaceOfService": str(rng.choice(["11", "22", "49"], p=[0.76, 0.18, 0.06])),
            "LineNumber": int(rng.integers(1, 4)),
            "ProcedureCode": code,
            "ProcedureName": name,
            "Modifier": modifier,
            "Modifier2": "",
            "Modifier3": "",
            "Primary_Diagnosis_Pointer": "1",
            "Primary_Diagnosis": diagnosis if rng.random() > 0.035 else "",
            "LONG_DESCRIPTION": long_description,
            "ClaimLineTotalPaid": round(paid, 2),
            "AmtCharged": charged,
            "AllowedUnits": units,
            "AmtDisallowed": round(max(charged - eligible, 0.0), 2),
            "AmtEligible": round(eligible, 2),
            "AmtCopay": float(rng.choice([0, 5, 10, 15, 20, 25])),
            "AmtCoinsurance": float(rng.choice([0, 0, 0, 5, 10])),
            "AmtDeductible": float(rng.choice([0, 0, 10, 25, 50])),
            "ProviderNPI": str(rng.choice(provider_pool)),
            "GroupId": f"G{int(rng.integers(1, 60))}",
            "GroupNumber": f"GRP{int(rng.integers(100, 999))}",
            "LOB": lob,
            "CoverageCode": str(rng.choice(COVERAGE_CODES)),
            "State": str(rng.choice(STATES)),
            "Flag": flag,
        }

    def _pick_procedure(self, rng: np.random.Generator, py_rng: Random) -> tuple[str, str]:
        bucket = rng.choice(["exam", "material", "addon", "nonvision"], p=[0.46, 0.32, 0.14, 0.08])
        if bucket == "exam":
            return py_rng.choice(VISION_EXAMS)
        if bucket == "addon":
            return py_rng.choice([item for item in MATERIAL_CODES if item[0] in {"V2750", "V2755", "V2760"}])
        if bucket == "material":
            return py_rng.choice(MATERIAL_CODES)
        return py_rng.choice(NON_VISION_CODES)

    def _pick_flag(self, code: str, rng: np.random.Generator) -> str:
        del rng
        if code in {"V2750", "V2755", "V2760"}:
            return "CCI Edits Claims"
        if code in {"92004", "92014"}:
            return "Exam after Comprehensive"
        if code.startswith("92") or code.startswith("S"):
            return "Two Exams in One Day"
        if code.startswith("V"):
            return "Bilateral Claims"
        return "CCI Edits Claims"

    def _eligible_amount(self, code: str, rng: np.random.Generator) -> float:
        if code.startswith("92") or code.startswith("S"):
            return float(np.clip(rng.normal(135, 28), 65, 230))
        if code in {"V2750", "V2755", "V2760"}:
            return float(np.clip(rng.normal(45, 16), 12, 110))
        if code.startswith("V"):
            return float(np.clip(rng.normal(92, 32), 20, 260))
        return float(np.clip(rng.normal(105, 35), 35, 260))

    def _inject_rule_coverage(
        self,
        rows: list[dict[str, Any]],
        providers: dict[str, str],
        rng: np.random.Generator,
        py_rng: Random,
    ) -> None:
        logger.info("Injecting deterministic rule coverage into sample data")
        for i in range(0, 120):
            rows[i].update({"ProcedureCode": "92014", "ProcedureName": "Comprehensive Eye Exam", "Modifier": "59"})

        for i in range(120, 240):
            rows[i].update({"AmtEligible": 80.0, "AmtCharged": 230.0, "AmtDisallowed": 150.0})

        for i in range(240, 360):
            rows[i].update({"ProcedureCode": "92012", "ProcedureName": "Intermediate Eye Exam Established Patient", "AllowedUnits": 2})

        for i in range(360, 480):
            code, name = py_rng.choice(NON_VISION_CODES)
            rows[i].update({"ProcedureCode": code, "ProcedureName": name})

        for i in range(480, 600):
            rows[i].update({"Primary_Diagnosis": ""})

        for i in range(600, 850):
            code, name = py_rng.choice(VISION_EXAMS)
            rows[i].update({"ProviderNPI": providers["exam"], "ProcedureCode": code, "ProcedureName": name})

        for i in range(850, 1100):
            code, name = py_rng.choice(MATERIAL_CODES)
            rows[i].update({"ProviderNPI": providers["material"], "ProcedureCode": code, "ProcedureName": name})

        for i in range(1100, 1300):
            rows[i].update({
                "ProviderNPI": providers["billed"],
                "AmtEligible": 190.0,
                "AmtCharged": 650.0 + float(rng.integers(0, 125)),
                "AmtDisallowed": 430.0,
            })

        for i in range(1300, 1550):
            code, name = py_rng.choice([item for item in MATERIAL_CODES if item[0] in {"V2750", "V2755", "V2760"}])
            rows[i].update({"ProviderNPI": providers["addon"], "ProcedureCode": code, "ProcedureName": name})
        logger.info("Rule coverage injection complete")

    def summary(self) -> dict[str, Any]:
        logger.info("Building sample data summary")
        historical = self.data_repository.load_historical_claims() if HISTORICAL_CLAIMS_PATH.exists() else pd.DataFrame()
        rules = self.data_repository.load_rules() if RULES_XLSX_PATH.exists() else pd.DataFrame()
        realtime = self.data_repository.load_realtime_sample_claims() if ROOT_REALTIME_CLAIMS.exists() else pd.DataFrame()
        result = {
            "historical_claims": self._dataset_summary(HISTORICAL_CLAIMS_PATH, historical),
            "rules": self._dataset_summary(RULES_XLSX_PATH, rules),
            "realtime_claims": self._dataset_summary(ROOT_REALTIME_CLAIMS, realtime),
        }
        logger.info(
            "Sample data summary built: historical=%d rules=%d realtime=%d",
            result["historical_claims"]["record_count"],
            result["rules"]["record_count"],
            result["realtime_claims"]["record_count"],
        )
        return result

    def _dataset_summary(self, path, df: pd.DataFrame) -> dict[str, Any]:
        logger.info("Summarizing dataset %s with %d row(s)", path, len(df))
        preview = df.head(5).replace({np.nan: None}).to_dict(orient="records") if not df.empty else []
        return {
            "path": str(path),
            "record_count": int(len(df)),
            "preview": preview,
        }
