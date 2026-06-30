"use client";

import { useState } from "react";
import { redactText, type RedactResponse } from "@/lib/api";
import OutputPanel, { OutputEmpty } from "./OutputPanel";

const INITIAL_TEXT = [
  "From: Alex Morgan <alex@example.com>",
  "To: finance@docguard.com",
  "Subject: Vendor payment",
  "",
  "Please charge card 4242 4242 4242 4242 and call me at (555) 010-2044.",
].join("\n");

export default function RedactWorkspace() {
  const [text, setText] = useState(INITIAL_TEXT);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<{
    title: string;
    summary: string;
    body: string;
    details: string[];
  } | null>(null);

  async function handleRedact() {
    if (!text.trim()) {
      setError("Paste some text before redacting.");
      return;
    }
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await redactText(text);
      setResult(formatResult(data));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed.");
    } finally {
      setIsLoading(false);
    }
  }

  function handleClear() {
    setText("");
    setResult(null);
    setError(null);
  }

  return (
    <section className="workspace">
      <div className="panel editor-panel">
        <div className="panel-head">
          <p>Input</p>
          <span>Paste text to redact sensitive data.</span>
        </div>

        <label className="sr-only" htmlFor="document-input">
          Document text
        </label>
        <textarea
          id="document-input"
          value={text}
          onChange={(e) => setText(e.target.value)}
          spellCheck={false}
          placeholder="Paste text here"
        />

        <div className="actions">
          <button
            type="button"
            className="secondary"
            onClick={handleRedact}
            disabled={isLoading}
          >
            {isLoading ? "Redacting\u2026" : "Redact"}
          </button>
          <button type="button" className="ghost" onClick={handleClear} disabled={isLoading}>
            Clear
          </button>
        </div>

        {error ? <p className="error">{error}</p> : null}
      </div>

      {result ? (
        <OutputPanel {...result} />
      ) : (
        <OutputEmpty />
      )}
    </section>
  );
}

function formatResult(data: RedactResponse) {
  return {
    title: "Redaction complete",
    summary: `${data.entities_redacted} entities redacted \u2022 ${data.risk_level} risk`,
    body: data.redacted_text,
    details: [
      `Processing time: ${data.processing_time_ms.toFixed(2)} ms`,
      `Document type: ${data.document_type}`,
    ],
  };
}
