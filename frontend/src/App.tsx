import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from "react";
import { chat } from "./api";

interface Message {
  role: "user" | "assistant";
  content: string;
  loading?: boolean;
}

const SAMPLE_QUESTIONS = [
  "你擅长什么技术栈？",
  "你在 RAG 项目里负责了哪些核心工作？",
  "介绍一下你的项目经历",
  "你的工作经验有多久？",
];

function App() {
  const [sessionId, setSessionId] = useState(() => crypto.randomUUID());
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function handleNewChat() {
    setSessionId(crypto.randomUUID());
    setMessages([]);
    setInput("");
    setError("");
  }

  async function onSubmit(e?: FormEvent) {
    e?.preventDefault();
    const q = input.trim();
    if (!q || loading) return;

    setInput("");
    setError("");
    setMessages((prev) => [
      ...prev,
      { role: "user", content: q },
      { role: "assistant", content: "", loading: true },
    ]);
    setLoading(true);

    try {
      const result = await chat(q, sessionId);
      setMessages((prev) => [
        ...prev.slice(0, -1),
        { role: "assistant", content: result.answer },
      ]);
    } catch (err) {
      setMessages((prev) => prev.slice(0, -1));
      setError(err instanceof Error ? err.message : "未知错误");
    } finally {
      setLoading(false);
    }
  }

  function onKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSubmit();
    }
  }

  function fillQuestion(q: string) {
    setInput(q);
  }

  return (
    <div className="chat-layout">
      <header className="chat-header">
        <div className="chat-header-inner">
          <div>
            <h1>Self-Agent</h1>
            <p className="desc">基于个人简历与项目经验的 RAG 问答助手</p>
          </div>
          <button className="btn-outline" onClick={handleNewChat}>新对话</button>
        </div>
      </header>

      <main className="message-list">
        {messages.length === 0 ? (
          <div className="empty-state">
            <p className="empty-title">有什么想了解的？试试这些问题：</p>
            <div className="sample-grid">
              {SAMPLE_QUESTIONS.map((q) => (
                <button key={q} className="sample-btn" onClick={() => fillQuestion(q)}>
                  {q}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div key={idx} className={`bubble-row ${msg.role}`}>
              <div className={`bubble ${msg.role}`}>
                {msg.loading ? (
                  <span className="typing-dots"><span /><span /><span /></span>
                ) : (
                  <p className="bubble-text">{msg.content}</p>
                )}
              </div>
            </div>
          ))
        )}
        {error && <p className="error">{error}</p>}
        <div ref={bottomRef} />
      </main>

      <footer className="input-bar">
        <form onSubmit={onSubmit} className="input-bar-inner">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="输入你的问题…（Enter 发送，Shift+Enter 换行）"
            rows={1}
          />
          <button type="submit" disabled={loading || !input.trim()}>
            {loading ? "回答中…" : "发送"}
          </button>
        </form>
      </footer>
    </div>
  );
}

export default App;
