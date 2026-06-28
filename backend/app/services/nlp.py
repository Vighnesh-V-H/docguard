from typing import List, Optional
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpEngineProvider

from app.schemas.analyze import Entity, EntityType
from app.core.config import get_settings


settings = get_settings()


class NLPService:
    def __init__(self):
        self.analyzer = None
        self._initialize_analyzer()
    
    def _initialize_analyzer(self):
        configuration = {
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": settings.PRESIDIO_LANGUAGE, "model_name": settings.SPACY_MODEL}],
        }
        
        provider = NlpEngineProvider(nlp_configuration=configuration)
        nlp_engine = provider.create_engine()
        
        registry = RecognizerRegistry()
        registry.load_predefined_recognizers()
        
        self.analyzer = AnalyzerEngine(
            nlp_engine=nlp_engine,
            registry=registry,
            supported_languages=[settings.PRESIDIO_LANGUAGE],
        )
    
    async def analyze(
        self,
        text: str,
        language: str = "en",
        entities: Optional[List[EntityType]] = None,
        score_threshold: float = 0.5,
    ) -> List[Entity]:
        if not self.analyzer:
            self._initialize_analyzer()
        
        entity_types = [e.value for e in entities] if entities else None
        
        results = self.analyzer.analyze(
            text=text,
            language=language,
            entities=entity_types,
            score_threshold=score_threshold,
        )
        
        return [
            Entity(
                entity_type=EntityType(r.entity_type),
                text=text[r.start:r.end],
                start=r.start,
                end=r.end,
                score=r.score,
            )
            for r in results
        ]