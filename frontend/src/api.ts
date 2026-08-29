export type PipelineMode = "grounded" | "naive";
export type DeskMode = PipelineMode | "compare";

export type GradedChunk = {
  chunk_id: string;
  source: string;
  relevant: boolean;
  reason: string;
  score?: number | null;
  snippet?: string;
  section?: string;
};

export type Citation = {
  id: number;
  source: string;
  title: string;
  url: string;
  chunk_id: string;
  quote: string;
  section?: string;
};

export type PipelineTrace = {
  rewritten_query: string | null;
  rewrite_count: number;
  retrieved_count: number;
  graded: GradedChunk[];
  decision: "answer" | "refuse";
  refuse_reason?: string;
  retrieval?: "hybrid" | "dense";
  steps?: string[];
  mode?: PipelineMode;
};

export type AskResponse = {
  status: "answered" | "refused";
  answer: string;
  citations: Citation[];
  trace: PipelineTrace;
  error?: string | null;
  mode?: PipelineMode;
  latency_ms?: number;
  warnings?: string[];
};

export type CompareResponse = {
  grounded: AskResponse;
  naive: AskResponse;
  contrast: string;
};

export type Health = {
  ok: boolean;
  llm_configured: boolean;
  index_ready: boolean;
  chunk_count: number;
  sources: string[];
  retrieve_mode?: "hybrid" | "dense";
  rewrite_max?: number;
};

export type CorpusSource = {
  id: string;
  title: string;
  url: string;
};

export type RetrievalEvalRow = {
  id: string;
  question: string;
  must_sources: string[];
  hit: boolean;
};

export type RetrievalEval = {
  recall: number;
  rows: RetrievalEvalRow[];
};

function humanDetail(payload: unknown): string | null {
  if (!payload || typeof payload !== "object") return null;
  const detail = (payload as { detail?: unknown }).detail;
  if (typeof detail === "string" && detail.trim()) return detail;
  if (Array.isArray(detail)) {
    const parts = detail
      .map((item) => {
        if (typeof item === "string") return item;
        if (item && typeof item === "object" && "msg" in item) {
          return String((item as { msg: unknown }).msg);
        }
        return "";
      })
      .filter(Boolean);
    if (parts.length) return parts.join(" ");
  }
  return null;
}

export function humanizeError(err: unknown, fallback: string): string {
  const raw = err instanceof Error ? err.message.trim() : "";
  if (!raw || raw.startsWith("{") || raw.startsWith("[")) return fallback;
  const lower = raw.toLowerCase();
  if (
    lower.includes("not reachable") ||
    lower.includes("failed to fetch") ||
    lower === "request failed." ||
    lower === "request failed"
  ) {
    return "The desk cannot reach the API. Start the backend on 127.0.0.1:8000.";
  }
  if (lower.includes("index is empty") || lower.includes("ingest first")) {
    return "The index is empty. Ingest the RFC corpus before asking.";
  }
  if (lower.includes("no llm key") || lower.includes("no api key")) {
    return "No API key found. Add FASTROUTER_API_KEY or OPENAI_API_KEY to the repo-root .env.";
  }
  if (lower.startsWith("ingest failed")) {
    return "Indexing failed. Check embedding keys and try Ingest corpus again.";
  }
  if (lower.startsWith("rag pipeline failed")) {
    return "The pipeline could not finish. Try again, or ingest if the index looks stale.";
  }
  if (raw.length > 220) return fallback;
  return raw;
}

export function warningCopy(code: string): string {
  switch (code) {
    case "faithfulness_off":
      return "Faithfulness is off. The model may answer from memory.";
    case "uncited_sentences":
      return "At least one long sentence has no [n] citation.";
    case "invented_citations":
      return "The answer cites an id that was never retrieved.";
    case "citation_mismatch":
      return "Cited ids do not match the numbered passages.";
    case "no_citations":
      return "No footnotes. This answer is likely from model memory.";
    default:
      return code.replace(/_/g, " ");
  }
}

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, {
      ...init,
      headers: {
        Accept: "application/json",
        ...(init?.body ? { "Content-Type": "application/json" } : {}),
        ...init?.headers,
      },
    });
  } catch {
    throw new Error("Backend is not reachable.");
  }

  const text = await response.text();
  let parsed: unknown = null;
  if (text) {
    try {
      parsed = JSON.parse(text);
    } catch {
      parsed = null;
    }
  }

  if (!response.ok) {
    if (response.status >= 500 && !humanDetail(parsed)) {
      throw new Error("Backend is not reachable.");
    }
    throw new Error(humanDetail(parsed) || "Request failed.");
  }

  return parsed as T;
}

export function getHealth(): Promise<Health> {
  return api<Health>("/api/health");
}

export function getCorpus(): Promise<{ sources: CorpusSource[] }> {
  return api("/api/corpus");
}

export function getRetrievalEval(): Promise<RetrievalEval> {
  return api("/api/eval/retrieval");
}

export function ingestCorpus(): Promise<Record<string, unknown>> {
  return api("/api/ingest", { method: "POST" });
}

export function askQuestion(question: string, mode: PipelineMode = "grounded"): Promise<AskResponse> {
  return api<AskResponse>("/api/ask", {
    method: "POST",
    body: JSON.stringify({ question, mode }),
  });
}

export function compareQuestion(question: string): Promise<CompareResponse> {
  return api<CompareResponse>("/api/compare", {
    method: "POST",
    body: JSON.stringify({ question }),
  });
}
