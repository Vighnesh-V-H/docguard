"use client";

import { useState } from "react";
import { analyzeText, type AnalyzeResponse } from "@/lib/api";
import OutputPanel, { OutputEmpty } from "./OutputPanel";

const INITIAL_TEXT = [
  "From: Alex Morgan <alex@example.com>",
  "To: finance@docguard.com",
  "Subject: Vendor payment",
  "",
  "Please charge card 4242 4242 4242 4242 and call me at (555) 010-2044.",
].join("\n");

export default function AnalyzeWorkspace() {
  const [text, setText] = useState(INITIAL_TEXT);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<{
    title: string;
    summary: string;
    body: string;
    details: string[];
  } | null>(null);

  async function handleAnalyze() {
    if (!text.trim()) {
      setError("Paste some text before analyzing.");
      return;
    }
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await analyzeText(text);
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
          <span>Paste text to scan for sensitive data.</span>
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
          <button type="button" onClick={handleAnalyze} disabled={isLoading}>
            {isLoading ? "Analyzing\u2026" : "Analyze"}
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

function formatResult(data: AnalyzeResponse) {
  return {
    title: "Analysis complete",
    summary: `${data.risk_level} risk \u2022 ${data.document_type} \u2022 ${data.document_length} characters`,
    body:
      data.entities.length > 0
        ? data.entities
            .map((e) => `${e.entity_type}: ${e.text}`)
            .join("\n")
        : "No sensitive entities detected.",
    details: [
      `Processing time: ${data.processing_time_ms.toFixed(2)} ms`,
      `Entities found: ${data.entities.length}`,
    ],
  };
}
