export interface Citation {
  source_name: string;
  snippet: string;
}

export interface ChatResponse {
  answer: string;
  citations: Citation[];
  trace_id: string;
}

export class ApiError extends Error {
  status: number;
  constructor(status: number) {
    super(`api_error_${status}`);
    this.name = "ApiError";
    this.status = status;
  }
}

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export async function pingHealth(): Promise<void> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) {
    throw new ApiError(res.status);
  }
}

export async function chat(
  question: string,
  sessionId: string,
): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, session_id: sessionId }),
  });
  if (!res.ok) {
    throw new ApiError(res.status);
  }
  return res.json() as Promise<ChatResponse>;
}
