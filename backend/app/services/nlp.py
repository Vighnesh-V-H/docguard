import re
from typing import List, Optional

try:
    from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
    from presidio_analyzer.nlp_engine import NlpEngineProvider, NlpEngine
except ImportError:
    AnalyzerEngine = None
    RecognizerRegistry = None
    NlpEngineProvider = None
    NlpEngine = None

try:
    import spacy
except ImportError:
    spacy = None

from app.schemas.analyze import Entity, EntityType
from app.core.config import get_settings
from app.services.redaction.pipeline import (
    extract_transformer_entities,
    load_transformer_detector,
    merge_entities,
    select_transformer_chunks,
)


settings = get_settings()


class NLPService:
    def __init__(self):
        self.analyzer = None
        self._fallback_mode = False
        self._transformer = None
        self._initialize_analyzer()
        self._initialize_transformer()
    
    def _initialize_analyzer(self):
        if AnalyzerEngine is None or RecognizerRegistry is None or NlpEngineProvider is None:
            self._fallback_mode = True
            return

        nlp_engine = self._create_nlp_engine()
        
        registry = RecognizerRegistry()
        registry.load_predefined_recognizers()
        
        self.analyzer = AnalyzerEngine(
            nlp_engine=nlp_engine,
            registry=registry,
            supported_languages=[settings.PRESIDIO_LANGUAGE],
        )

    def _create_nlp_engine(self) -> NlpEngine:
        configuration = {
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": settings.PRESIDIO_LANGUAGE, "model_name": settings.SPACY_MODEL}],
        }

        try:
            provider = NlpEngineProvider(nlp_configuration=configuration)
            return provider.create_engine()
        except Exception:
            self._fallback_mode = True
            return None

    def _initialize_transformer(self) -> None:
        self._transformer = load_transformer_detector()

    def _fallback_analyze(
        self,
        text: str,
        entities: Optional[List[EntityType]] = None,
        score_threshold: float = 0.5,
    ) -> List[Entity]:
        allowed = {entity.value for entity in entities} if entities else None

        patterns = {
            EntityType.EMAIL_ADDRESS: r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
            EntityType.PHONE_NUMBER: r"\b(?:\+?\d{1,3}[\s.-]?)?(?:\(\d{3}\)|\d{3})[\s.-]?\d{3}[\s.-]?\d{4}\b",
            EntityType.US_SSN: r"\b\d{3}-\d{2}-\d{4}\b",
            EntityType.CREDIT_CARD: r"\b(?:\d[ -]*?){13,19}\b",
            EntityType.IP_ADDRESS: r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
            EntityType.IBAN_CODE: r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b",
        }

        results: List[Entity] = []
        for entity_type, pattern in patterns.items():
            if allowed is not None and entity_type.value not in allowed:
                continue

            for match in re.finditer(pattern, text):
                results.append(
                    Entity(
                        entity_type=entity_type,
                        text=match.group(0),
                        start=match.start(),
                        end=match.end(),
                        score=max(score_threshold, 0.9),
                    )
                )

        results.sort(key=lambda entity: entity.start)
        return results
    
    async def analyze(
        self,
        text: str,
        language: str = "en",
        entities: Optional[List[EntityType]] = None,
        score_threshold: float = 0.5,
    ) -> List[Entity]:
        if self._fallback_mode or not self.analyzer:
            base_entities = self._fallback_analyze(text=text, entities=entities, score_threshold=score_threshold)
        else:
            base_entities = self._analyze_with_presidio(
                text=text,
                language=language,
                entities=entities,
                score_threshold=score_threshold,
            )

        if not self._transformer:
            return base_entities

        allowed_types = {
            entity_type
            for entity_type in (entities or [])
            if entity_type
            in {
                EntityType.PERSON,
                EntityType.ORGANIZATION,
                EntityType.LOCATION,
                EntityType.DATE_TIME,
                EntityType.NRP,
            }
        } or None

        chunks = select_transformer_chunks(text=text, entities=base_entities, allowed_types=allowed_types)
        transformer_entities = extract_transformer_entities(text=text, chunks=chunks, detector=self._transformer)
        return merge_entities(base_entities, transformer_entities)

    def _analyze_with_presidio(
        self,
        text: str,
        language: str,
        entities: Optional[List[EntityType]],
        score_threshold: float,
    ) -> List[Entity]:
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