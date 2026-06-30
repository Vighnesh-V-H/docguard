from __future__ import annotations

import io
from email import policy
from email.parser import BytesParser

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

from app.schemas.analyze import DocumentType


def detect_upload_document_type(content_type: str | None, filename: str | None = None) -> DocumentType:
    normalized_filename = (filename or "").lower()
    normalized_content_type = (content_type or "").lower()

    if normalized_content_type == "application/pdf" or normalized_filename.endswith(".pdf"):
        return DocumentType.PDF
    if normalized_content_type in {"message/rfc822", "text/rfc822-headers"} or normalized_filename.endswith(".eml"):
        return DocumentType.EMAIL
    if normalized_content_type.startswith("text/") or normalized_filename.endswith(".txt"):
        return DocumentType.TEXT
    return DocumentType.UNKNOWN


def extract_pdf_text(content: bytes) -> str:
    if PdfReader is None:
        return content.decode("utf-8", errors="ignore")

    reader = PdfReader(io.BytesIO(content))
    return "\n".join(page.extract_text() or "" for page in reader.pages).strip()


def extract_email_text(content: bytes) -> tuple[str, dict[str, str]]:
    message = BytesParser(policy=policy.default).parsebytes(content)
    body = message.get_body(preferencelist=("plain", "html"))

    text = ""
    if body is not None:
        try:
            text = body.get_content()
        except Exception:
            text = body.get_payload(decode=True).decode("utf-8", errors="ignore") if body.get_payload(decode=True) else ""
    elif message.is_multipart():
        parts = []
        for part in message.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    parts.append(payload.decode("utf-8", errors="ignore"))
        text = "\n".join(parts).strip()
    else:
        payload = message.get_payload(decode=True)
        text = payload.decode("utf-8", errors="ignore") if payload else str(message.get_payload())

    metadata = {
        "from": message.get("from", ""),
        "to": message.get("to", ""),
        "subject": message.get("subject", ""),
    }
    return text.strip(), metadata


def extract_text_from_upload(content: bytes, content_type: str | None, filename: str | None = None) -> tuple[str, DocumentType, dict[str, str]]:
    document_type = detect_upload_document_type(content_type, filename)

    if document_type == DocumentType.PDF:
        return extract_pdf_text(content), document_type, {}
    if document_type == DocumentType.EMAIL:
        text, metadata = extract_email_text(content)
        return text, document_type, metadata

    return content.decode("utf-8", errors="ignore"), document_type, {}