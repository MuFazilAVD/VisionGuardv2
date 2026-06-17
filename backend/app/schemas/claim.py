import logging
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.utils.number_parsing import parse_numeric_value


STRING_FIELDS = [
    "ClaimId",
    "Gender",
    "ServiceDateFrom",
    "PlaceOfService",
    "ProcedureCode",
    "ProcedureName",
    "Modifier",
    "Modifier2",
    "Modifier3",
    "Primary_Diagnosis_Pointer",
    "Primary_Diagnosis",
    "LONG_DESCRIPTION",
    "ProviderNPI",
    "GroupId",
    "GroupNumber",
    "LOB",
    "CoverageCode",
    "State",
]

NUMERIC_FIELDS = [
    "Age",
    "LineNumber",
    "ClaimLineTotalPaid",
    "AmtCharged",
    "AllowedUnits",
    "AmtDisallowed",
    "AmtEligible",
    "AmtCopay",
    "AmtCoinsurance",
    "AmtDeductible",
]

logger = logging.getLogger(__name__)


class ClaimInput(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    ClaimId: str = Field(..., min_length=1)
    Gender: str = ""
    Age: int | float = 0
    ServiceDateFrom: str = ""
    PlaceOfService: str = ""
    LineNumber: int = 1
    ProcedureCode: str = ""
    ProcedureName: str = ""
    Modifier: str | None = ""
    Modifier2: str | None = ""
    Modifier3: str | None = ""
    Primary_Diagnosis_Pointer: str | None = ""
    Primary_Diagnosis: str | None = ""
    LONG_DESCRIPTION: str | None = ""
    ClaimLineTotalPaid: float | int = 0
    AmtCharged: float | int = 0
    AllowedUnits: float | int = 0
    AmtDisallowed: float | int = 0
    AmtEligible: float | int = 0
    AmtCopay: float | int = 0
    AmtCoinsurance: float | int = 0
    AmtDeductible: float | int = 0
    ProviderNPI: str = ""
    GroupId: str = ""
    GroupNumber: str = ""
    LOB: str = ""
    CoverageCode: str = ""
    State: str = ""

    @field_validator(*STRING_FIELDS, mode="before")
    @classmethod
    def coerce_string_fields(cls, value: Any) -> str:
        if value is None:
            return ""
        return str(value).strip()

    @field_validator(*NUMERIC_FIELDS, mode="before")
    @classmethod
    def coerce_blank_numbers(cls, value: Any) -> Any:
        if value is None:
            return 0
        if isinstance(value, str) and value.strip() == "":
            return 0
        return parse_numeric_value(value)


class AnalyzeRequest(BaseModel):
    claims: list[ClaimInput]


def validate_claim_payload(payload: Any) -> list[dict[str, Any]]:
    logger.info("Validating claim payload")
    if isinstance(payload, list):
        raw_claims = payload
    elif isinstance(payload, dict) and isinstance(payload.get("claims"), list):
        raw_claims = payload["claims"]
    else:
        logger.info("Claim payload validation failed: unsupported payload shape")
        raise ValueError("Request body must be a claim list or an object with a claims list.")

    claims = [ClaimInput.model_validate(item).model_dump() for item in raw_claims]
    if not claims:
        logger.info("Claim payload validation failed: no claims submitted")
        raise ValueError("Submit at least one claim for realtime assessment.")
    logger.info("Validated %d claim payload item(s)", len(claims))
    return claims
