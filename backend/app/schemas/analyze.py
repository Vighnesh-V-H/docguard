from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class EntityType(str, Enum):
    PERSON = "PERSON"
    EMAIL_ADDRESS = "EMAIL_ADDRESS"
    PHONE_NUMBER = "PHONE_NUMBER"
    CREDIT_CARD = "CREDIT_CARD"
    US_SSN = "US_SSN"
    US_DRIVER_LICENSE = "US_DRIVER_LICENSE"
    IP_ADDRESS = "IP_ADDRESS"
    LOCATION = "LOCATION"
    ORGANIZATION = "ORGANIZATION"
    DATE_TIME = "DATE_TIME"
    NRP = "NRP"
    IBAN_CODE = "IBAN_CODE"


class RiskLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class DocumentType(str, Enum):
    PDF = "PDF"
    EMAIL = "EMAIL"
    TEXT = "TEXT"
    DOCX = "DOCX"
    UNKNOWN = "UNKNOWN"


class Entity(BaseModel):
    entity_type: EntityType
    text: str
    start: int = Field(ge=0)
    end: int = Field(ge=0)
    score: float = Field(ge=0.0, le=1.0)


class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=100000)
    language: str = Field(default="en", min_length=2, max_length=10)
    entities: Optional[List[EntityType]] = None
    score_threshold: float = Field(default=0.5, ge=0.0, le=1.0)


class AnalyzeResponse(BaseModel):
    entities: List[Entity]
    risk_level: RiskLevel
    processing_time_ms: float
    document_length: int
    document_type: DocumentType = DocumentType.UNKNOWN


class RedactRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=100000)
    language: str = Field(default="en", min_length=2, max_length=10)
    entities: Optional[List[EntityType]] = None
    score_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    mask_char: str = Field(default="*", min_length=1, max_length=1)
    use_labels: bool = True


class RedactedEntity(BaseModel):
    entity_type: EntityType
    original_text: str
    redacted_text: str
    start: int
    end: int


class RedactResponse(BaseModel):
    redacted_text: str
    entities: List[RedactedEntity]
    risk_level: RiskLevel
    processing_time_ms: float
    document_length: int
    document_type: DocumentType = DocumentType.UNKNOWN
    entities_redacted: int = 0


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str