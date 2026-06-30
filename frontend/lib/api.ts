const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type Entity = {
  entity_type: string;
  text: string;
  start: number;
  end: number;
  score: number;
};

export type RedactEntity = {
  entity_type: string;
  original_text: string;
  redacted_text: string;
  start: number;
  end: number;
};

export type AnalyzeResponse = {
  entities: Entity[];
  risk_level: string;
  processing_time_ms: number;
  document_length: number;
  document_type: string;
};

export type RedactResponse = AnalyzeResponse & {
  redacted_text: string;
  entities_redacted: number;
  entities: RedactEntity[];
};

export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(endpoint: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  const data = await res.json();
  if (!res.ok) {
    throw new ApiError(data.detail ?? "Backend request failed.", res.status);
  }
  return data as T;
}

export async function analyzeText(text: string, language = "en", scoreThreshold = 0.5) {
  return request<AnalyzeResponse>("/api/v1/analyze", {
    text,
    language,
    score_threshold: scoreThreshold,
  });
}

export async function redactText(
  text: string,
  language = "en",
  scoreThreshold = 0.5,
  useLabels = true,
  maskChar = "*",
) {
  return request<RedactResponse>("/api/v1/redact", {
    text,
    language,
    score_threshold: scoreThreshold,
    use_labels: useLabels,
    mask_char: maskChar,
  });
}

export async function analyzeFile(file: File, language = "en", scoreThreshold = 0.5) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("language", language);
  formData.append("score_threshold", String(scoreThreshold));

  const res = await fetch(`${API_BASE}/api/v1/analyze/file`, {
    method: "POST",
    body: formData,
  });

  const data = await res.json();
  if (!res.ok) {
    throw new ApiError(data.detail ?? "File analysis failed.", res.status);
  }
  return data as AnalyzeResponse;
}

export async function redactFile(
  file: File,
  language = "en",
  scoreThreshold = 0.5,
  useLabels = true,
  maskChar = "*",
) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("language", language);
  formData.append("score_threshold", String(scoreThreshold));
  formData.append("use_labels", String(useLabels));
  formData.append("mask_char", maskChar);

  const res = await fetch(`${API_BASE}/api/v1/redact/file`, {
    method: "POST",
    body: formData,
  });

  const data = await res.json();
  if (!res.ok) {
    throw new ApiError(data.detail ?? "File redaction failed.", res.status);
  }
  return data as RedactResponse;
}
