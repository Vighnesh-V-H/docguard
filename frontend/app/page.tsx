"use client";

import { useState } from "react";

type Mode = "analyze" | "redact";

type AnalyzeResponse = {
  entities: Array<{
    entity_type: string;
    text: string;
    start: number;
    end: number;
    score: number;
  }>;
  risk_level: string;
  processing_time_ms: number;
  document_length: number;
  document_type: string;
};

type RedactResponse = AnalyzeResponse & {
  redacted_text: string;
  entities_redacted: number;
  entities: Array<{
    entity_type: string;
    original_text: string;
    redacted_text: string;
    start: number;
    end: number;
  }>;
};

type ResultState = {
  mode: Mode;
  title: string;
  summary: string;
  body: string;
  details: string[];
} | null;

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const INITIAL_TEXT = [
  "From: Alex Morgan <alex@example.com>",
  "To: finance@docguard.com",
  "Subject: Vendor payment",
  "",
  "Please charge card 4242 4242 4242 4242 and call me at (555) 010-2044.",
].join("\n");

export default function Page() {
  const [text, setText] = useState(INITIAL_TEXT);
  const [mode, setMode] = useState<Mode>("analyze");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ResultState>(null);

  const documentLength = text.trim().length;

  async function runAction(nextMode: Mode) {
    if (!text.trim()) {
      setError("Paste some text before running an action.");
      setResult(null);
      return;
    }

    setMode(nextMode);
    setIsLoading(true);
    setError(null);

    const endpoint =
      nextMode === "analyze" ? "/api/v1/analyze" : "/api/v1/redact";
    const payload = {
      text,
      language: "en",
      score_threshold: 0.5,
      ...(nextMode === "redact" ? { use_labels: true, mask_char: "*" } : {}),
    };

    try {
      const response = await fetch(`${API_BASE}${endpoint}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const data = (await response.json()) as (
        | AnalyzeResponse
        | RedactResponse
      ) & {
        detail?: string;
      };

      if (!response.ok) {
        throw new Error(data.detail ?? "The backend returned an error.");
      }

      if (nextMode === "analyze") {
        const analysis = data as AnalyzeResponse;
        setResult({
          mode: nextMode,
          title: "Analysis ready",
          summary: `${analysis.risk_level} risk • ${analysis.document_type} • ${analysis.document_length} characters`,
          body:
            analysis.entities.length > 0
              ? analysis.entities
                  .map((entity) => `${entity.entity_type}: ${entity.text}`)
                  .join("\n")
              : "No sensitive entities detected.",
          details: [
            `Processing time: ${analysis.processing_time_ms.toFixed(2)} ms`,
            `Entities found: ${analysis.entities.length}`,
          ],
        });
      } else {
        const redaction = data as RedactResponse;
        setResult({
          mode: nextMode,
          title: "Redaction ready",
          summary: `${redaction.entities_redacted} entities redacted • ${redaction.risk_level} risk`,
          body: redaction.redacted_text,
          details: [
            `Processing time: ${redaction.processing_time_ms.toFixed(2)} ms`,
            `Document type: ${redaction.document_type}`,
          ],
        });
      }
    } catch (requestError) {
      setResult(null);
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Request failed.",
      );
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className='shell'>
      <div className='ambient ambient-one' aria-hidden='true' />
      <div className='ambient ambient-two' aria-hidden='true' />

      <header className='topbar'>
        <div>
          <p className='eyebrow'>DocGuard</p>
          <h1>Quiet document security.</h1>
        </div>
        <div className='status-pill'>
          <span className='dot' />
          <span>Local UI</span>
        </div>
      </header>

      <section className='hero'>
        <p className='lede'>
          Paste text, inspect what matters, then redact it without leaving the
          page.
        </p>
        <div className='stats'>
          <div>
            <span>Mode</span>
            <strong>{mode}</strong>
          </div>
          <div>
            <span>Length</span>
            <strong>{documentLength}</strong>
          </div>
          <div>
            <span>Backend</span>
            <strong>{API_BASE}</strong>
          </div>
        </div>
      </section>

      <section className='workspace'>
        <div className='panel editor-panel'>
          <div className='panel-head'>
            <p>Input</p>
            <span>Analyze or redact the same text.</span>
          </div>

          <label className='sr-only' htmlFor='document-input'>
            Document text
          </label>
          <textarea
            id='document-input'
            value={text}
            onChange={(event) => setText(event.target.value)}
            spellCheck={false}
            placeholder='Paste text here'
          />

          <div className='actions'>
            <button
              type='button'
              onClick={() => runAction("analyze")}
              disabled={isLoading}>
              {isLoading && mode === "analyze" ? "Analyzing..." : "Analyze"}
            </button>
            <button
              type='button'
              className='secondary'
              onClick={() => runAction("redact")}
              disabled={isLoading}>
              {isLoading && mode === "redact" ? "Redacting..." : "Redact"}
            </button>
            <button
              type='button'
              className='ghost'
              onClick={() => {
                setText("");
                setResult(null);
                setError(null);
              }}
              disabled={isLoading}>
              Clear
            </button>
          </div>

          {error ? <p className='error'>{error}</p> : null}
        </div>

        <aside className='panel output-panel' aria-live='polite'>
          <div className='panel-head'>
            <p>Output</p>
            <span>Minimal feedback, no clutter.</span>
          </div>

          {result ? (
            <>
              <div className='result-summary'>
                <p>{result.title}</p>
                <span>{result.summary}</span>
              </div>

              <pre>{result.body}</pre>

              <ul className='result-details'>
                {result.details.map((detail) => (
                  <li key={detail}>{detail}</li>
                ))}
              </ul>
            </>
          ) : (
            <div className='empty-state'>
              <p>Results appear here.</p>
              <span>
                Start the FastAPI backend on port 8000 to use the live analyze
                and redact actions.
              </span>
            </div>
          )}
        </aside>
      </section>
    </main>
  );
}
