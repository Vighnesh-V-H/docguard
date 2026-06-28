from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.processing_log import ProcessingLog, EntityDetectionLog, RiskLevelEnum, DocumentTypeEnum
from app.schemas.analyze import Entity, EntityType, RiskLevel


class AuditRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def log_processing(
        self,
        document_type: DocumentTypeEnum,
        risk_level: RiskLevel,
        entities_detected: int,
        entities_redacted: int,
        processing_latency_ms: float,
        document_length: int,
        language: str = "en",
        entity_counts: Optional[dict[EntityType, int]] = None,
    ) -> ProcessingLog:
        log = ProcessingLog(
            document_type=document_type,
            risk_level=RiskLevelEnum(risk_level.value),
            entities_detected=entities_detected,
            entities_redacted=entities_redacted,
            processing_latency_ms=processing_latency_ms,
            document_length=document_length,
            language=language,
            created_at=datetime.utcnow(),
        )
        self.db.add(log)
        await self.db.flush()
        
        if entity_counts:
            for entity_type, count in entity_counts.items():
                entity_log = EntityDetectionLog(
                    processing_log_id=log.id,
                    entity_type=entity_type.value,
                    entity_count=count,
                )
                self.db.add(entity_log)
        
        await self.db.commit()
        await self.db.refresh(log)
        return log
    
    async def get_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> dict:
        query = select(
            func.count(ProcessingLog.id).label("total_documents"),
            func.avg(ProcessingLog.processing_latency_ms).label("avg_latency_ms"),
            func.sum(ProcessingLog.entities_detected).label("total_entities"),
            func.sum(ProcessingLog.entities_redacted).label("total_redacted"),
        )
        
        if start_date:
            query = query.where(ProcessingLog.created_at >= start_date)
        if end_date:
            query = query.where(ProcessingLog.created_at <= end_date)
        
        result = await self.db.execute(query)
        row = result.one()
        
        return {
            "total_documents": row.total_documents or 0,
            "avg_latency_ms": round(row.avg_latency_ms or 0, 2),
            "total_entities_detected": row.total_entities or 0,
            "total_entities_redacted": row.total_redacted or 0,
        }
    
    async def get_entity_type_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[dict]:
        query = select(
            EntityDetectionLog.entity_type,
            func.sum(EntityDetectionLog.entity_count).label("total_count"),
        ).join(ProcessingLog)
        
        if start_date:
            query = query.where(ProcessingLog.created_at >= start_date)
        if end_date:
            query = query.where(ProcessingLog.created_at <= end_date)
        
        query = query.group_by(EntityDetectionLog.entity_type)
        query = query.order_by(func.sum(EntityDetectionLog.entity_count).desc())
        
        result = await self.db.execute(query)
        return [
            {"entity_type": row.entity_type, "count": row.total_count}
            for row in result.all()
        ]
    
    async def get_risk_distribution(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[dict]:
        query = select(
            ProcessingLog.risk_level,
            func.count(ProcessingLog.id).label("count"),
        )
        
        if start_date:
            query = query.where(ProcessingLog.created_at >= start_date)
        if end_date:
            query = query.where(ProcessingLog.created_at <= end_date)
        
        query = query.group_by(ProcessingLog.risk_level)
        result = await self.db.execute(query)
        
        return [
            {"risk_level": row.risk_level.value, "count": row.count}
            for row in result.all()
        ]
    
    async def get_daily_volume(
        self,
        days: int = 30,
    ) -> List[dict]:
        from datetime import timedelta
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = select(
            func.date(ProcessingLog.created_at).label("date"),
            func.count(ProcessingLog.id).label("count"),
        ).where(ProcessingLog.created_at >= start_date)
        
        query = query.group_by(func.date(ProcessingLog.created_at))
        query = query.order_by(func.date(ProcessingLog.created_at))
        
        result = await self.db.execute(query)
        return [
            {"date": row.date.isoformat(), "count": row.count}
            for row in result.all()
        ]