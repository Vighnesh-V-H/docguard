from datetime import datetime
from sqlalchemy import DateTime, func, Enum as SQLEnum, Integer, Float, String, JSON
from sqlalchemy.orm import Mapped, mapped_column
from enum import Enum as PyEnum

from app.db.session import Base


class DocumentTypeEnum(str, PyEnum):
    PDF = "PDF"
    EMAIL = "EMAIL"
    TEXT = "TEXT"
    DOCX = "DOCX"
    UNKNOWN = "UNKNOWN"


class RiskLevelEnum(str, PyEnum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class ProcessingLog(Base):
    __tablename__ = "processing_logs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_type: Mapped[DocumentTypeEnum] = mapped_column(
        SQLEnum(DocumentTypeEnum), index=True, nullable=False
    )
    risk_level: Mapped[RiskLevelEnum] = mapped_column(
        SQLEnum(RiskLevelEnum), index=True, nullable=False
    )
    entities_detected: Mapped[int] = mapped_column(Integer, default=0)
    entities_redacted: Mapped[int] = mapped_column(Integer, default=0)
    processing_latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    document_length: Mapped[int] = mapped_column(Integer, nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="en")
    entity_counts: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )


class EntityDetectionLog(Base):
    __tablename__ = "entity_detection_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    processing_log_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_count: Mapped[int] = mapped_column(Integer, default=0)