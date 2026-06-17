from __future__ import annotations

from io import BytesIO
import logging

import pandas as pd
from fastapi import APIRouter, HTTPException, Request

from app.schemas.claim import validate_claim_payload
from app.schemas.scoring import AnalyzeResponse
from app.services.realtime_service import RealtimeService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: Request) -> dict:
    logger.info("Claims analyze request received")
    try:
        content_type = request.headers.get("content-type", "")
        logger.info("Claims analyze content type: %s", content_type or "<missing>")
        if "multipart/form-data" in content_type:
            form = await request.form()
            upload = form.get("file")
            if upload is None:
                raise ValueError("CSV upload must use a form field named file.")
            contents = await upload.read()
            frame = pd.read_csv(BytesIO(contents))
            claims = frame.where(pd.notna(frame), "").to_dict(orient="records")
            logger.info("Parsed %d claim(s) from uploaded CSV", len(claims))
        else:
            payload = await request.json()
            claims = validate_claim_payload(payload)
            logger.info("Parsed %d claim(s) from JSON request", len(claims))
    except ValueError as exc:
        logger.info("Claims analyze request validation failed: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Claims analyze request parsing failed")
        raise HTTPException(status_code=400, detail=f"Unable to parse claim request: {exc}") from exc

    try:
        result = RealtimeService().analyze_claims(claims)
        logger.info("Claims analyze request completed with %d assessment(s)", result.get("count", 0))
        return result
    except ValueError as exc:
        logger.info("Claims analyze service validation failed: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
