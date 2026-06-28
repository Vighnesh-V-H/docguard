import time
from typing import List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from app.schemas.analyze import (
    RedactRequest,
    RedactResponse,
    Entity,
    EntityType,
    RiskLevel,
)
from app.services.nlp import NLPService


router = APIRouter()
nlp_service = NLPService()


def calculate_risk_level(entities: List[Entity]) -> RiskLevel:
    if not entities:
        return RiskLevel.LOW
    
    high_risk_types = {
        EntityType.CREDIT_CARD,
        EntityType.US_SSN,
        EntityType.US_DRIVER_LICENSE,
        EntityType.IBAN_CODE,
    }
    
    medium_risk_types = {
        EntityType.EMAIL_ADDRESS,
        EntityType.PHONE_NUMBER,
        EntityType.IP_ADDRESS,
    }
    
    has_high = any(e.entity_type in high_risk_types for e in entities)
    has_medium = any(e.entity_type in medium_risk_types for e in entities)
    
    if has_high:
        return RiskLevel.HIGH
    elif has_medium or len(entities) > 5:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


def redact_text(text: str, entities: List[Entity], mask_char: str = "*", mask_length: Optional[int] = None) -> str:
    if not entities:
        return text
    
    sorted_entities = sorted(entities, key=lambda e: e.start, reverse=True)
    result = list(text)
    
    for entity in sorted_entities:
        start, end = entity.start, entity.end
        original_length = end - start
        
        if mask_length and mask_length < original_length:
            masked = mask_char * mask_length
        else:
            masked = f"[REDACTED_{entity.entity_type.value}]"
        
        result[start:end] = list(masked)
    
    return "".join(result)


@router.post("", response_model=RedactResponse)
async def redact_text_endpoint(request: RedactRequest):
    start_time = time.perf_counter()
    
    try:
        entities = await nlp_service.analyze(
            text=request.text,
            language=request.language,
            entities=request.entities,
            score_threshold=request.score_threshold,
        )
        
        redacted = redact_text(
            request.text,
            entities,
            mask_char=request.mask_char,
            mask_length=request.mask_length,
        )
        
        processing_time_ms = (time.perf_counter() - start_time) * 1000
        risk_level = calculate_risk_level(entities)
        
        return RedactResponse(
            redacted_text=redacted,
            entities_found=entities,
            risk_level=risk_level,
            processing_time_ms=round(processing_time_ms, 2),
            document_length=len(request.text),
            entities_redacted=len(entities),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/file", response_model=RedactResponse)
async def redact_file(
    file: UploadFile = File(...),
    language: str = Form("en"),
    score_threshold: float = Form(0.5),
    mask_char: str = Form("*"),
    mask_length: Optional[int] = Form(None),
):
    start_time = time.perf_counter()
    
    if file.content_type not in ["application/pdf", "text/plain", "message/rfc822"]:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    
    content = await file.read()
    text = content.decode("utf-8", errors="ignore")
    
    try:
        entities = await nlp_service.analyze(
            text=text,
            language=language,
            score_threshold=score_threshold,
        )
        
        redacted = redact_text(text, entities, mask_char=mask_char, mask_length=mask_length)
        
        processing_time_ms = (time.perf_counter() - start_time) * 1000
        risk_level = calculate_risk_level(entities)
        
        return RedactResponse(
            redacted_text=redacted,
            entities_found=entities,
            risk_level=risk_level,
            processing_time_ms=round(processing_time_ms, 2),
            document_length=len(text),
            entities_redacted=len(entities),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))