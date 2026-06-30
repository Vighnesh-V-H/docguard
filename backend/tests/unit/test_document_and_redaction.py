from app.api.v1.endpoints.analyze import calculate_risk_level as analyze_risk_level, detect_document_type
from app.api.v1.endpoints.redact import calculate_risk_level as redact_risk_level, redact_text
from app.schemas.analyze import DocumentType, Entity, EntityType, RiskLevel
from app.utils.extractors.document import detect_upload_document_type, extract_text_from_upload


def test_detect_upload_document_type_by_filename_and_mime() -> None:
    assert detect_upload_document_type("application/pdf", "contract.pdf") == DocumentType.PDF
    assert detect_upload_document_type("message/rfc822", "message.eml") == DocumentType.EMAIL
    assert detect_upload_document_type("text/plain", "note.txt") == DocumentType.TEXT


def test_extract_text_from_plain_text_upload() -> None:
    text, document_type, metadata = extract_text_from_upload(b"Hello world", "text/plain", "note.txt")

    assert text == "Hello world"
    assert document_type == DocumentType.TEXT
    assert metadata == {}


def test_extract_text_from_email_upload() -> None:
    content = (
        b"From: alice@example.com\n"
        b"To: bob@example.com\n"
        b"Subject: Status Update\n"
        b"Content-Type: text/plain; charset=utf-8\n\n"
        b"This is the body."
    )

    text, document_type, metadata = extract_text_from_upload(content, "message/rfc822", "mail.eml")

    assert document_type == DocumentType.EMAIL
    assert "This is the body." in text
    assert metadata["from"] == "alice@example.com"
    assert metadata["subject"] == "Status Update"


def test_redact_text_uses_placeholders_and_keeps_offsets_ordered() -> None:
    text = "Contact Alice at alice@example.com"
    entities = [
        Entity(entity_type=EntityType.PERSON, text="Alice", start=8, end=13, score=0.99),
        Entity(entity_type=EntityType.EMAIL_ADDRESS, text="alice@example.com", start=17, end=34, score=0.98),
    ]

    redacted_text, redacted_entities = redact_text(text, entities, use_labels=True)

    assert "[REDACTED_PERSON]" in redacted_text
    assert "[REDACTED_EMAIL_ADDRESS]" in redacted_text
    assert len(redacted_entities) == 2
    assert redacted_entities[0].start == 8
    assert redacted_entities[1].start == 17


def test_redact_text_can_partial_mask() -> None:
    text = "Account 123456789"
    entities = [
        Entity(entity_type=EntityType.CREDIT_CARD, text="123456789", start=8, end=17, score=0.99),
    ]

    redacted_text, redacted_entities = redact_text(text, entities, mask_char="#", mask_length=4, use_labels=False)

    assert "####" in redacted_text
    assert redacted_entities[0].redacted_text == "####"


def test_risk_level_helpers_choose_highest_severity() -> None:
    entities = [
        Entity(entity_type=EntityType.PERSON, text="Alice", start=0, end=5, score=0.99),
        Entity(entity_type=EntityType.CREDIT_CARD, text="4111111111111111", start=6, end=22, score=0.99),
    ]

    assert analyze_risk_level(entities) == RiskLevel.CRITICAL
    assert redact_risk_level(entities) == RiskLevel.HIGH


def test_detect_document_type_heuristics() -> None:
    assert detect_document_type("From: a\nTo: b\nSubject: Hello") == DocumentType.EMAIL
    assert detect_document_type("%PDF-1.7 header bytes") == DocumentType.PDF
