"use client";

import { useState, useRef } from "react";
import { analyzeFile, redactFile, type AnalyzeResponse, type RedactResponse } from "@/lib/api";
import OutputPanel, { OutputEmpty } from "./OutputPanel";

type Mode = "analyze" | "redact";

export default function FileUploadWorkspace({ mode }: { mode: Mode }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<{
    title: string;
    summary: string;
    body: string;
    details: string[];
  } | null>(null);

  function handleFile(f: File) {
    const allowed = [".pdf", ".eml", ".txt", "application/pdf", "message/rfc822", "text/plain"];
    const ext = "." + f.name.split(".").pop()?.toLowerCase();
    const isAllowed =
      allowed.includes(f.type) || allowed.includes(ext);
    if (!isAllowed) {
      setError("Unsupported file type. Use PDF, EML, or plain text.");
      return;
    }
    setFile(f);
    setError(null);
    setResult(null);
  }

  async function handleSubmit() {
    if (!file) {
      setError("Select or drop a file first.");
      return;
    }
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      if (mode === "analyze") {
        const data = await analyzeFile(file);
        setResult(formatAnalyzeResult(data));
      } else {
        const data = await redactFile(file);
        setResult(formatRedactResult(data));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed.");
    } finally {
      setIsLoading(false);
    }
  }

  function handleReset() {
    setFile(null);
    setResult(null);
    setError(null);
    if (inputRef.current) inputRef.current.value = "";
  }

  const actionLabel = mode === "analyze" ? "Analyze" : "Redact";

  return (
    <section className="workspace">
      <div className="panel editor-panel">
        <div className="panel-head">
          <p>Upload</p>
          <span>{mode === "analyze" ? "Scan" : "Redact"} a PDF, EML, or text file.</span>
        </div>

        <div
          className={`drop-zone ${dragOver ? "drop-zone--active" : ""}`}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragOver(false);
            const f = e.dataTransfer.files[0];
            if (f) handleFile(f);
          }}
          onClick={() => inputRef.current?.click()}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") inputRef.current?.click(); }}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".pdf,.eml,.txt,application/pdf,message/rfc822,text/plain"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) handleFile(f);
            }}
            className="sr-only"
            id="file-input"
          />
          {file ? (
            <div className="drop-zone__file">
              <span className="drop-zone__name">{file.name}</span>
              <span className="drop-zone__size">{(file.size / 1024).toFixed(1)} KB</span>
            </div>
          ) : (
            <>
              <span className="drop-zone__icon">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                  <polyline points="17 8 12 3 7 8" />
                  <line x1="12" y1="3" x2="12" y2="15" />
                </svg>
              </span>
              <span className="drop-zone__label">Drop a file here, or click to browse</span>
              <span className="drop-zone__hint">PDF, EML, or plain text</span>
            </>
          )}
        </div>

        <div className="actions">
          <button type="button" onClick={handleSubmit} disabled={isLoading || !file}>
            {isLoading ? `${actionLabel}ing\u2026` : actionLabel}
          </button>
          <button type="button" className="ghost" onClick={handleReset} disabled={isLoading}>
            Reset
          </button>
        </div>

        {error ? <p className="error">{error}</p> : null}
      </div>

      {result ? <OutputPanel {...result} /> : <OutputEmpty />}
    </section>
  );
}

function formatAnalyzeResult(data: AnalyzeResponse) {
  return {
    title: "Analysis complete",
    summary: `${data.risk_level} risk \u2022 ${data.document_type} \u2022 ${data.document_length} characters`,
    body:
      data.entities.length > 0
        ? data.entities.map((e) => `${e.entity_type}: ${e.text}`).join("\n")
        : "No sensitive entities detected.",
    details: [
      `Processing time: ${data.processing_time_ms.toFixed(2)} ms`,
      `Entities found: ${data.entities.length}`,
    ],
  };
}

function formatRedactResult(data: RedactResponse) {
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
