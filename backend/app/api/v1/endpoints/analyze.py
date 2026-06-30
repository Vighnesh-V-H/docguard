import time
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.analyze import (
    AnalyzeRequest, AnalyzeResponse, Entity, EntityType, RiskLevel, DocumentType
)
from app.services.nlp import NLPService
from app.services.audit import AuditService
from app.db.session import get_db
from app.utils.extractors.document import extract_text_from_upload


router = APIRouter()


def get_nlp_service() -> NLPService:
    return NLPService()


def get_audit_service(db: AsyncSession = Depends(get_db)) -> AuditService:
    return AuditService(db)


RISK_KEYWORDS = {
    EntityType.CREDIT_CARD: RiskLevel.CRITICAL,
    EntityType.US_SSN: RiskLevel.CRITICAL,
    EntityType.US_DRIVER_LICENSE: RiskLevel.HIGH,
    EntityType.EMAIL_ADDRESS: RiskLevel.MEDIUM,
    EntityType.PHONE_NUMBER: RiskLevel.MEDIUM,
    EntityType.PERSON: RiskLevel.LOW,
    EntityType.LOCATION: RiskLevel.LOW,
    EntityType.ORGANIZATION: RiskLevel.LOW,
    EntityType.IP_ADDRESS: RiskLevel.MEDIUM,
    EntityType.DATE_TIME: RiskLevel.LOW,
    EntityType.NRP: RiskLevel.HIGH,
    EntityType.IBAN_CODE: RiskLevel.CRITICAL,
}


def calculate_risk_level(entities: list[Entity]) -> RiskLevel:
    if not entities:
        return RiskLevel.LOW
    
    max_risk = RiskLevel.LOW
    risk_order = {
        RiskLevel.LOW: 0,
        RiskLevel.MEDIUM: 1,
        RiskLevel.HIGH: 2,
        RiskLevel.CRITICAL: 3,
    }
    
    for entity in entities:
        entity_risk = RISK_KEYWORDS.get(entity.entity_type, RiskLevel.LOW)
        if risk_order[entity_risk] > risk_order[max_risk]:
            max_risk = entity_risk
    
    return max_risk


def detect_document_type(text: str) -> DocumentType:
    text_lower = text.lower()
    if "from:" in text_lower and "to:" in text_lower and "subject:" in text_lower:
        return DocumentType.EMAIL
    elif text.startswith("%pdf") or "pdf" in text_lower[:100]:
        return DocumentType.PDF
    elif len(text) > 1000 and ("\n\n" in text or "\r\n\r\n" in text):
        return DocumentType.DOCX
    return DocumentType.TEXT


@router.post("", response_model=AnalyzeResponse)
async def analyze_text(
    request: AnalyzeRequest,
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"NLP analysis failed: {str(e)}")
    
    processing_time_ms = (time.perf_counter() - start_time) * 1000
    risk_level = calculate_risk_level(entities)
    document_type = detect_document_type(request.text)
    
    await audit_service.log_analysis(
        document_type=document_type.value,
        risk_level=risk_level,
        entities=entities,
        processing_latency_ms=processing_time_ms,
        document_length=len(request.text),
        language=request.language,
    )
    
    return AnalyzeResponse(
        entities=entities,
        risk_level=risk_level,
        processing_time_ms=round(processing_time_ms, 2),
        document_length=len(request.text),
        document_type=document_type,
    )


@router.post("/file", response_model=AnalyzeResponse)
async def analyze_file(
    file: UploadFile = File(...),
    language: str = Form("en"),
    score_threshold: float = Form(0.5),
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    processing_time_ms = (time.perf_counter() - start_time) * 1000
    risk_level = calculate_risk_level(entities)

    document_type = upload_document_type if upload_document_type != DocumentType.UNKNOWN else detect_document_type(text)

    await audit_service.log_analysis(
        document_type=document_type.value,
        risk_level=risk_level,
        entities=entities,
        processing_latency_ms=processing_time_ms,
        document_length=len(text),
        language=language,
    )
    
    return AnalyzeResponse(
        entities=entities,
        risk_level=risk_level,
        processing_time_ms=round(processing_time_ms, 2),
        document_length=len(text),
        document_type=document_type,
    )