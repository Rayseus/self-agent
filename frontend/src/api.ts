export interface Citation {
  source_name: string;
  snippet: string;
}

export interface ChatResponse {
  answer: string;
  citations: Citation[];
  trace_id: string;
}

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

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
    throw new Error(`请求失败: ${res.status}`);
  }
  return res.json() as Promise<ChatResponse>;
}
