from __future__ import annotations

from io import BytesIO

import pandas as pd
from fastapi import APIRouter, HTTPException, Request

from app.schemas.claim import validate_claim_payload
from app.schemas.scoring import AnalyzeResponse
from app.services.realtime_service import RealtimeService

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: Request) -> dict:
    try:
        content_type = request.headers.get("content-type", "")
        if "multipart/form-data" in content_type:
            form = await request.form()
            upload = form.get("file")
            if upload is None:
                raise ValueError("CSV upload must use a form field named file.")
            contents = await upload.read()
            frame = pd.read_csv(BytesIO(contents))
            claims = frame.where(pd.notna(frame), "").to_dict(orient="records")
        else:
            payload = await request.json()
            claims = validate_claim_payload(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Unable to parse claim request: {exc}") from exc

    try:
        return RealtimeService().analyze_claims(claims)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

