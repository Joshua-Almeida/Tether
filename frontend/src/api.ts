export type GradedChunk = {
  chunk_id: string;
  source: string;
  relevant: boolean;
  reason: string;
};

export type Citation = {
  id: number;
  source: string;
  title: string;
  url: string;
  chunk_id: string;
  quote: string;
};

export type PipelineTrace = {
  rewritten_query: string | null;
  rewrite_count: number;
  retrieved_count: number;
  graded: GradedChunk[];
  decision: "answer" | "refuse";
};

export type AskResponse = {
  status: "answered" | "refused";
  answer: string;
  citations: Citation[];
  trace: PipelineTrace;
  error?: string | null;
};

export type Health = {
  ok: boolean;
  llm_configured: boolean;
  index_ready: boolean;
  chunk_count: number;
  sources: string[];
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
    throw new Error(humanDetail(parsed) || "Request failed.");
  }

  return parsed as T;
}

export function getHealth(): Promise<Health> {
  return api<Health>("/api/health");
}

export function ingestCorpus(): Promise<Record<string, unknown>> {
  return api("/api/ingest", { method: "POST" });
}

export function askQuestion(question: string): Promise<AskResponse> {
  return api<AskResponse>("/api/ask", {
    method: "POST",
    body: JSON.stringify({ question }),
  });
}
