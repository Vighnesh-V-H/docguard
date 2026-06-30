from app.schemas.analyze import Entity, EntityType
from app.services.redaction.pipeline import TextChunk, extract_transformer_entities, get_transformer_chunks, merge_entities, select_transformer_chunks


def test_get_transformer_chunks_applies_overlap_for_long_text() -> None:
    text = "one two three four five six seven eight"

    chunks = get_transformer_chunks(text, max_tokens=3, overlap_tokens=1)

    assert len(chunks) >= 2
    assert chunks[0].text.startswith("one two three")
    assert chunks[1].text.startswith("three four")


def test_select_transformer_chunks_targets_sentence_with_transformable_entity() -> None:
    text = "Nothing here. Alice met Bob in Seattle. More text follows."
    entities = [
        Entity(entity_type=EntityType.PERSON, text="Alice", start=14, end=19, score=0.99),
    ]

    chunks = select_transformer_chunks(text=text, entities=entities, allowed_types=None)

    assert len(chunks) == 1
    assert "Alice met Bob in Seattle" in chunks[0].text


def test_extract_transformer_entities_maps_offsets_back_to_original_text() -> None:
    text = "Alice met Bob."
    chunks = [TextChunk(start=0, end=len(text), text=text)]

    def detector(chunk_text: str):
        assert chunk_text == text
        return [{"entity_group": "PER", "start": 0, "end": 5, "score": 0.98}]

    entities = extract_transformer_entities(text=text, chunks=chunks, detector=detector)

    assert len(entities) == 1
    assert entities[0].entity_type == EntityType.PERSON
    assert entities[0].start == 0
    assert entities[0].end == 5


def test_merge_entities_prefers_transformer_prediction_for_overlapping_span() -> None:
    base_entities = [
        Entity(entity_type=EntityType.PERSON, text="Apple", start=0, end=5, score=0.60),
    ]
    transformer_entities = [
        Entity(entity_type=EntityType.ORGANIZATION, text="Apple", start=0, end=5, score=0.99),
    ]

    merged = merge_entities(base_entities, transformer_entities)

    assert len(merged) == 1
    assert merged[0].entity_type == EntityType.ORGANIZATION
    assert merged[0].score == 0.99