from datetime import datetime
from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.analyze import Entity, EntityType, RiskLevel
from app.models.processing_log import DocumentTypeEnum, RiskLevelEnum
from app.repositories.audit import AuditRepository


class AuditService:
    def __init__(self, db: AsyncSession):
        self.repo = AuditRepository(db)
    
    async def log_analysis(
        self,
        document_type: str,
        risk_level: RiskLevel,
        entities: List[Entity],
        processing_latency_ms: float,
        document_length: int,
        language: str = "en",
    ) -> None:
        entity_counts: Dict[EntityType, int] = {}
        for entity in entities:
            entity_counts[entity.entity_type] = entity_counts.get(entity.entity_type, 0) + 1
        
        await self.repo.log_processing(
            document_type=DocumentTypeEnum(document_type.upper()),
            risk_level=risk_level,
            entities_detected=len(entities),
            entities_redacted=0,
            processing_latency_ms=processing_latency_ms,
            document_length=document_length,
            language=language,
            entity_counts=entity_counts,
        )
    
    async def log_redaction(
        self,
        document_type: str,
        risk_level: RiskLevel,
        entities: List[Entity],
        entities_redacted: int,
        processing_latency_ms: float,
        document_length: int,
        language: str = "en",
    ) -> None:
        entity_counts: Dict[EntityType, int] = {}
        for entity in entities:
            entity_counts[entity.entity_type] = entity_counts.get(entity.entity_type, 0) + 1
        
        await self.repo.log_processing(
            document_type=DocumentTypeEnum(document_type.upper()),
            risk_level=risk_level,
            entities_detected=len(entities),
            entities_redacted=entities_redacted,
            processing_latency_ms=processing_latency_ms,
            document_length=document_length,
            language=language,
            entity_counts=entity_counts,
        )
    
    async def get_dashboard_stats(self, days: int = 30) -> dict:
        from datetime import timedelta
        start_date = datetime.utcnow() - timedelta(days=days)
        
        stats = await self.repo.get_stats(start_date=start_date)
        entity_stats = await self.repo.get_entity_type_stats(start_date=start_date)
        risk_dist = await self.repo.get_risk_distribution(start_date=start_date)
        daily_volume = await self.repo.get_daily_volume(days=days)
        
        return {
            **stats,
            "entity_type_distribution": entity_stats,
            "risk_distribution": risk_dist,
            "daily_volume": daily_volume,
        }