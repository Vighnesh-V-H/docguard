from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Iterable

try:
    import spacy
except ImportError:
    spacy = None

try:
    from transformers import pipeline as transformer_pipeline
except ImportError:
    transformer_pipeline = None

from app.core.config import get_settings
from app.schemas.analyze import Entity, EntityType


settings = get_settings()

TRANSFORMABLE_ENTITY_TYPES = {
    EntityType.PERSON,
    EntityType.ORGANIZATION,
    EntityType.LOCATION,
    EntityType.DATE_TIME,
    EntityType.NRP,
}

TRANSFORMER_LABEL_MAP = {
    "PER": EntityType.PERSON,
    "PERSON": EntityType.PERSON,
    "ORG": EntityType.ORGANIZATION,
    "ORGANIZATION": EntityType.ORGANIZATION,
    "LOC": EntityType.LOCATION,
    "GPE": EntityType.LOCATION,
    "LOCATION": EntityType.LOCATION,
    "DATE": EntityType.DATE_TIME,
    "TIME": EntityType.DATE_TIME,
    "DATE_TIME": EntityType.DATE_TIME,
}


@dataclass(frozen=True)
class SentenceSpan:
    start: int
    end: int
    text: str


@dataclass(frozen=True)
class TextChunk:
    start: int
    end: int
    text: str


@dataclass(frozen=True)
class TokenSpan:
    start: int
    end: int


@lru_cache(maxsize=1)
def load_sentence_segmenter() -> Any | None:
    if spacy is None:
        return None

    try:
        return spacy.load(settings.SPACY_MODEL)
    except Exception:
        return None


@lru_cache(maxsize=1)
def load_transformer_detector() -> Any | None:
    if transformer_pipeline is None or not settings.TRANSFORMER_ENABLED:
        return None

    try:
        return transformer_pipeline(
            task="token-classification",
            model=settings.TRANSFORMER_MODEL,
            tokenizer=settings.TRANSFORMER_MODEL,
            aggregation_strategy="simple",
            device=-1,
        )
    except Exception:
        return None


def _regex_sentence_spans(text: str) -> list[SentenceSpan]:
    spans: list[SentenceSpan] = []
    pattern = re.compile(r"[^\n.!?]+(?:[.!?]+|$|\n+)", re.DOTALL)

    for match in pattern.finditer(text):
        start = match.start()
        end = match.end()
        sentence_text = text[start:end]
        if sentence_text.strip():
            spans.append(SentenceSpan(start=start, end=end, text=sentence_text))

    if not spans and text.strip():
        stripped = text.strip()
        leading = text.find(stripped)
        spans.append(SentenceSpan(start=leading, end=leading + len(stripped), text=stripped))

    return spans


def get_sentence_spans(text: str) -> list[SentenceSpan]:
    segmenter = load_sentence_segmenter()
    if segmenter is None:
        return _regex_sentence_spans(text)

    try:
        doc = segmenter(text)
        spans = [SentenceSpan(start=sent.start_char, end=sent.end_char, text=sent.text) for sent in doc.sents]
        if spans:
            return spans
    except Exception:
        pass

    return _regex_sentence_spans(text)


def _token_spans(text: str) -> list[TokenSpan]:
    segmenter = load_sentence_segmenter()
    if segmenter is not None:
        try:
            doc = segmenter(text)
            return [TokenSpan(start=token.idx, end=token.idx + len(token.text)) for token in doc if not token.is_space]
        except Exception:
            pass

    return [TokenSpan(start=match.start(), end=match.end()) for match in re.finditer(r"\S+", text)]


def _token_spans_in_range(text: str, start: int, end: int) -> list[TokenSpan]:
    return [token for token in _token_spans(text) if token.start >= start and token.end <= end]


def get_transformer_chunks(text: str, max_tokens: int, overlap_tokens: int) -> list[TextChunk]:
    sentence_spans = get_sentence_spans(text)
    chunks: list[TextChunk] = []
    active_start: int | None = None
    active_end: int | None = None
    active_token_count = 0

    for sentence in sentence_spans:
        tokens = _token_spans_in_range(text, sentence.start, sentence.end)
        if not tokens:
            continue

        if len(tokens) <= max_tokens:
            if active_start is None:
                active_start = sentence.start
                active_end = sentence.end
                active_token_count = len(tokens)
                continue

            if active_token_count + len(tokens) <= max_tokens:
                active_end = sentence.end
                active_token_count += len(tokens)
                continue

            chunks.append(TextChunk(start=active_start, end=active_end or sentence.start, text=text[active_start:active_end]))
            active_start = sentence.start
            active_end = sentence.end
            active_token_count = len(tokens)
            continue

        if active_start is not None:
            chunks.append(TextChunk(start=active_start, end=active_end or active_start, text=text[active_start:active_end]))
            active_start = None
            active_end = None
            active_token_count = 0

        step = max(1, max_tokens - overlap_tokens)
        for index in range(0, len(tokens), step):
            window = tokens[index : index + max_tokens]
            if not window:
                break

            start = window[0].start
            end = window[-1].end
            chunks.append(TextChunk(start=start, end=end, text=text[start:end]))

            if index + max_tokens >= len(tokens):
                break

    if active_start is not None and active_end is not None and active_end > active_start:
        chunks.append(TextChunk(start=active_start, end=active_end, text=text[active_start:active_end]))

    return chunks


def should_transform_sentence(sentence: SentenceSpan, entities: Iterable[Entity], allowed_types: set[EntityType] | None) -> bool:
    for entity in entities:
        if entity.end <= sentence.start or entity.start >= sentence.end:
            continue

        if allowed_types is not None and entity.entity_type not in allowed_types:
            continue

        if entity.entity_type in TRANSFORMABLE_ENTITY_TYPES or entity.score <= settings.TRANSFORMER_TRIGGER_SCORE:
            return True

    return False


def select_transformer_chunks(text: str, entities: list[Entity], allowed_types: set[EntityType] | None) -> list[TextChunk]:
    if not settings.TRANSFORMER_ENABLED:
        return []

    sentence_spans = get_sentence_spans(text)
    selected_sentences = [sentence for sentence in sentence_spans if should_transform_sentence(sentence, entities, allowed_types)]

    if not selected_sentences:
        return []

    chunks: list[TextChunk] = []
    max_tokens = max(1, settings.TRANSFORMER_MAX_TOKENS)
    overlap_tokens = max(0, min(settings.TRANSFORMER_OVERLAP_TOKENS, max_tokens - 1))

    for sentence in selected_sentences:
        sentence_chunks = get_transformer_chunks(sentence.text, max_tokens=max_tokens, overlap_tokens=overlap_tokens)
        if not sentence_chunks:
            chunks.append(TextChunk(start=sentence.start, end=sentence.end, text=text[sentence.start:sentence.end]))
            continue

        for chunk in sentence_chunks:
            chunks.append(
                TextChunk(
                    start=sentence.start + chunk.start,
                    end=sentence.start + chunk.end,
                    text=text[sentence.start + chunk.start : sentence.start + chunk.end],
                )
            )

    return chunks


def _dedupe_entities(entities: Iterable[Entity]) -> list[Entity]:
    unique: dict[tuple[EntityType, int, int, str], Entity] = {}

    for entity in entities:
        key = (entity.entity_type, entity.start, entity.end, entity.text)
        existing = unique.get(key)
        if existing is None or entity.score > existing.score:
            unique[key] = entity

    return sorted(unique.values(), key=lambda item: (item.start, item.end, item.entity_type.value))


def merge_entities(base_entities: Iterable[Entity], transformer_entities: Iterable[Entity]) -> list[Entity]:
    transformer_list = list(transformer_entities)
    if not transformer_list:
        return _dedupe_entities(base_entities)

    merged: list[Entity] = []
    for entity in base_entities:
        if any(entity.start < other.end and other.start < entity.end for other in transformer_list):
            continue
        merged.append(entity)

    merged.extend(transformer_list)
    return _dedupe_entities(merged)


def map_transformer_label(label: str) -> EntityType | None:
    normalized = label.upper().replace("B-", "").replace("I-", "")
    return TRANSFORMER_LABEL_MAP.get(normalized)


def extract_transformer_entities(text: str, chunks: Iterable[TextChunk], detector: Any | None) -> list[Entity]:
    if detector is None:
        return []

    entities: list[Entity] = []

    for chunk in chunks:
        try:
            predictions = detector(chunk.text)
        except Exception:
            continue

        if isinstance(predictions, dict):
            predictions = [predictions]

        for prediction in predictions:
            label = str(prediction.get("entity_group") or prediction.get("entity") or "")
            entity_type = map_transformer_label(label)
            if entity_type is None:
                continue

            start_offset = prediction.get("start")
            end_offset = prediction.get("end")
            if start_offset is None or end_offset is None:
                continue

            start = chunk.start + int(start_offset)
            end = chunk.start + int(end_offset)
            if start >= end:
                continue

            entities.append(
                Entity(
                    entity_type=entity_type,
                    text=text[start:end],
                    start=start,
                    end=end,
                    score=float(prediction.get("score", 0.0)),
                )
            )

    return _dedupe_entities(entities)