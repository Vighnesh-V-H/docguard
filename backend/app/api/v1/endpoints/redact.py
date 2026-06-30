import time
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.analyze import (
    DocumentType,
    Entity,
    EntityType,
    RedactRequest,
    RedactResponse,
    RedactedEntity,
    RiskLevel,
)
from app.services.audit import AuditService
from app.services.nlp import NLPService
from app.utils.extractors.document import detect_upload_document_type, extract_text_from_upload


router = APIRouter()


def get_nlp_service() -> NLPService:
    return NLPService()


def get_audit_service(db: AsyncSession = Depends(get_db)) -> AuditService:
    return AuditService(db)


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
    if has_medium or len(entities) > 5:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


def detect_document_type(text: str) -> DocumentType:
    text_lower = text.lower()
    if "from:" in text_lower and "to:" in text_lower and "subject:" in text_lower:
        return DocumentType.EMAIL
    if text.startswith("%pdf") or "pdf" in text_lower[:100]:
        return DocumentType.PDF
    if len(text) > 1000 and ("\n\n" in text or "\r\n\r\n" in text):
        return DocumentType.DOCX
    return DocumentType.TEXT


def redact_text(
    text: str,
    entities: List[Entity],
    mask_char: str = "*",
    mask_length: Optional[int] = None,
    use_labels: bool = True,
) -> tuple[str, List[RedactedEntity]]:
    if not entities:
        return text, []

    sorted_entities = sorted(entities, key=lambda e: e.start, reverse=True)
    result = list(text)
    redacted_entities: List[RedactedEntity] = []

    for entity in sorted_entities:
        start, end = entity.start, entity.end
        original_length = end - start
        original_text = text[start:end]

        if not use_labels and mask_length and mask_length < original_length:
            masked = mask_char * mask_length
        else:
            masked = f"[REDACTED_{entity.entity_type.value}]" if use_labels else mask_char * original_length

        result[start:end] = list(masked)
        redacted_entities.append(
            RedactedEntity(
                entity_type=entity.entity_type,
                original_text=original_text,
                redacted_text=masked,
                start=start,
                end=end,
            )
        )

    redacted_entities.sort(key=lambda item: item.start)
    return "".join(result), redacted_entities


@router.post("", response_model=RedactResponse)
async def redact_text_endpoint(
    request: RedactRequest,
    nlp_service: NLPService = Depends(get_nlp_service),
    audit_service: AuditService = Depends(get_audit_service),
):
    start_time = time.perf_counter()

    try:
        entities = await nlp_service.analyze(
            text=request.text,
            language=request.language,
            entities=request.entities,
            score_threshold=request.score_threshold,
        )

        redacted_text, redacted_entities = redact_text(
            request.text,
            entities,
            mask_char=request.mask_char,
            mask_length=request.mask_length,
            use_labels=request.use_labels,
        )

        processing_time_ms = (time.perf_counter() - start_time) * 1000
        risk_level = calculate_risk_level(entities)
        document_type = detect_document_type(request.text)

        await audit_service.log_redaction(
            document_type=document_type.value,
            risk_level=risk_level,
            entities=entities,
            entities_redacted=len(redacted_entities),
            processing_latency_ms=processing_time_ms,
            document_length=len(request.text),
        )

        return RedactResponse(
            redacted_text=redacted_text,
            entities=redacted_entities,
            risk_level=risk_level,
            processing_time_ms=round(processing_time_ms, 2),
            document_length=len(request.text),
            document_type=document_type,
            entities_redacted=len(redacted_entities),
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
    use_labels: bool = Form(True),
    nlp_service: NLPService = Depends(get_nlp_service),
    audit_service: AuditService = Depends(get_audit_service),
):
    start_time = time.perf_counter()

    upload_document_type = detect_upload_document_type(file.content_type, file.filename)
    if upload_document_type == DocumentType.UNKNOWN:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    content = await file.read()
    text, upload_document_type, _ = extract_text_from_upload(content, file.content_type, file.filename)

    try:
        entities = await nlp_service.analyze(
            text=text,
            language=language,
            score_threshold=score_threshold,
        )

        redacted_text, redacted_entities = redact_text(
            text,
            entities,
            mask_char=mask_char,
            mask_length=mask_length,
            use_labels=use_labels,
        )

        processing_time_ms = (time.perf_counter() - start_time) * 1000
        risk_level = calculate_risk_level(entities)
        document_type = upload_document_type

        await audit_service.log_redaction(
            document_type=document_type.value,
            risk_level=risk_level,
            entities=entities,
            entities_redacted=len(redacted_entities),
            processing_latency_ms=processing_time_ms,
            document_length=len(text),
            language=language,
        )

        return RedactResponse(
            redacted_text=redacted_text,
            entities=redacted_entities,
            risk_level=risk_level,
            processing_time_ms=round(processing_time_ms, 2),
            document_length=len(text),
            document_type=document_type,
            entities_redacted=len(redacted_entities),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))