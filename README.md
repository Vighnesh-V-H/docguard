# DocGuard AI

DocGuard AI is a backend-first document security pipeline for unstructured enterprise content. It ingests text, PDFs, and email messages, runs a two-stage PII detection flow with Presidio/SpaCy plus an optional transformer refinement step, redacts sensitive spans, and records compliance-oriented audit metrics without storing raw PII.

## What the backend does

The current backend is organized as a FastAPI application under `backend/app` and is centered on four operational paths:

- `/health` and `/` for service status checks.
- `/api/v1/analyze` for entity detection and document risk classification.
- `/api/v1/redact` for full text sanitization with placeholder masking or partial masking.
- Audit logging through PostgreSQL-backed repositories for operational metrics.

## Technical stack

- FastAPI for the HTTP layer.
- Pydantic for request and response schemas.
- SQLAlchemy async ORM with PostgreSQL/asyncpg for persistence.
- Presidio Analyzer for named entity recognition.
- spaCy as the NLP engine provider for Presidio and sentence segmentation.
- Hugging Face Transformers for contextual refinement on selected document spans.
- pypdf for PDF text extraction.
- Python `email` parsing for raw `.eml` content.

## Backend structure

- `backend/app/main.py`: application bootstrap, CORS, lifespan, router registration.
- `backend/app/api/v1/endpoints/analyze.py`: analyze routes for JSON and file uploads.
- `backend/app/api/v1/endpoints/redact.py`: redact routes for JSON and file uploads.
- `backend/app/utils/extractors/document.py`: shared upload classification and extraction helpers.
- `backend/app/services/nlp.py`: NLP wrapper around Presidio.
- `backend/app/services/audit.py`: audit service orchestration.
- `backend/app/repositories/audit.py`: database queries and inserts for analytics.
- `backend/app/models/processing_log.py`: SQLAlchemy models for processing logs.
- `backend/app/schemas/analyze.py`: Pydantic request and response models.
- `backend/app/core/config.py`: environment-driven settings.
- `backend/app/core/logging.py`: application logging setup.

## Core functions and how they work

### `analyze_text`

This route accepts structured JSON containing text and optional entity filters. It calls `NLPService.analyze`, measures processing latency, calculates the highest document risk, infers a document type, and writes an audit row with counts only. The response returns detected entities, risk level, latency, document length, and document type.

### `analyze_file`

This route accepts uploaded PDFs, text files, or email messages. It uses the shared extractor utility to detect file type, extract text, and normalize the payload before passing it to the NLP layer. The function keeps extraction separate from analysis so the pipeline can later grow more advanced parsers without changing endpoint semantics.

### `redact_text`

This helper applies entity redaction safely from the end of the string back to the front. That reverse ordering prevents span offsets from shifting while replacements are applied. It also supports two masking strategies: semantic labels like `[REDACTED_EMAIL_ADDRESS]` or partial masking using a repeated character.

### `redact_text_endpoint`

This route runs entity detection, transforms the text, returns the redacted string, and logs the redaction event. The response now includes `RedactedEntity` objects so callers can see exactly what was changed and where.

### `extract_text_from_upload`

This helper detects upload type from MIME type or filename. It uses `pypdf.PdfReader` for PDFs, the stdlib email parser for `.eml` files, and UTF-8 decoding for plain text. The helper returns the extracted text, the inferred document type, and any metadata collected from email headers.

### `AuditService.log_analysis` and `AuditService.log_redaction`

These methods map application-level risk and entity data into database inserts without storing raw PII. They compute per-entity counts for analytics and write only compliance-safe metrics such as latency, document length, and document type.

### `NLPService.analyze`

This method now runs a two-stage NLP pipeline. Presidio first detects obvious entities, then the service selects high-value or ambiguous sentence spans and runs them through a transformer NER model. Overlong segments are split with a sliding window and overlapping token ranges so boundary entities are not dropped. Transformer predictions replace overlapping base spans before the normalized `Entity` list is returned.

## Data model

The persistence layer stores:

- `processing_logs` for document-level audit rows.
- `entity_detection_logs` for aggregate counts of detected entity types.

The schema is intentionally designed so that raw PII is not written to PostgreSQL. Only counts, lengths, risk levels, and timing metrics are persisted.

## Configuration

Key settings live in `backend/app/core/config.py`:

- `APP_NAME`
- `API_V1_PREFIX`
- `DATABASE_URL`
- `DATABASE_ECHO`
- `PRESIDIO_LANGUAGE`
- `SPACY_MODEL`
- `TRANSFORMER_ENABLED`
- `TRANSFORMER_MODEL`
- `TRANSFORMER_MAX_TOKENS`
- `TRANSFORMER_OVERLAP_TOKENS`
- `TRANSFORMER_TRIGGER_SCORE`
- `LOG_LEVEL`
- `LOG_FORMAT`
- `CORS_ORIGINS`

## Running the backend

The backend is structured as a standard FastAPI app. After installing dependencies, run it with Uvicorn from the `backend` directory:

```bash
uvicorn app.main:app --reload
```

## Development notes

- The backend is intentionally layered so ingestion, NLP, redaction, and audit responsibilities stay isolated.
- File extraction is centralized in one utility module so future parsers can be added without duplicating upload logic.
- The redaction/NLP path now uses a lightweight first pass plus transformer refinement for ambiguous spans and long documents.
- Redaction returns both the sanitized text and structured metadata for downstream systems.
- Audit logging is metrics-only by design.

## Current status

The backend codebase now has:

- package structure and import boundaries,
- audit persistence models,
- entity detection and redaction APIs,
- file ingestion helpers for PDF and email content,
- logging/config defaults,
- and a documentation/reporting split between README and report files.
