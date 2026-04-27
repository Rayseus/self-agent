import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from "react";
import { ApiError, chat, pingHealth } from "./api";
import { useLang } from "./i18n";
import type { Lang } from "./i18n";

const COLD_START_TIMEOUT_MS = 30000;

interface Message {
  role: "user" | "assistant";
  content: string;
  loading?: boolean;
}

function App() {
  const { lang, t, setLang } = useLang();
  const [sessionId, setSessionId] = useState(() => crypto.randomUUID());
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [healthReady, setHealthReady] = useState(false);
  const [showColdStartTip, setShowColdStartTip] = useState(false);
  const [coldStartShown, setColdStartShown] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    pingHealth()
      .then(() => setHealthReady(true))
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (healthReady && showColdStartTip) {
      setShowColdStartTip(false);
    }
  }, [healthReady, showColdStartTip]);

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

    if (!healthReady && !coldStartShown) {
      setShowColdStartTip(true);
      setColdStartShown(true);
      window.setTimeout(
        () => setShowColdStartTip(false),
        COLD_START_TIMEOUT_MS,
      );
    }

    try {
      const result = await chat(q, sessionId);
      setMessages((prev) => [
        ...prev.slice(0, -1),
        { role: "assistant", content: result.answer },
      ]);
      setShowColdStartTip(false);
    } catch (err) {
      setMessages((prev) => prev.slice(0, -1));
      if (err instanceof ApiError) {
        setError(t.error.request(err.status));
      } else {
        setError(t.error.unknown);
      }
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

  const langOptions: { value: Lang; label: string }[] = [
    { value: "zh", label: "中文" },
    { value: "en", label: "English" },
  ];

  return (
    <div className="chat-layout">
      <header className="chat-header">
        <div className="chat-header-inner">
          <div className="chat-header-title">
            <h1>{t.header.title}</h1>
            <p className="desc">{t.header.desc}</p>
          </div>
          <div className="chat-header-actions">
            <div className="lang-switch" role="group" aria-label="language">
              {langOptions.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  className={lang === opt.value ? "active" : ""}
                  aria-pressed={lang === opt.value}
                  onClick={() => setLang(opt.value)}
                >
                  {opt.label}
                </button>
              ))}
            </div>
            <button className="btn-outline" onClick={handleNewChat}>
              {t.header.newChat}
            </button>
          </div>
        </div>
      </header>

      {showColdStartTip && (
        <div className="cold-start-banner" role="status">
          <span className="cold-start-icon" aria-hidden="true">ⓘ</span>
          <span className="cold-start-text">{t.coldStart.tip}</span>
          <button
            type="button"
            className="cold-start-close"
            aria-label={t.coldStart.dismiss}
            onClick={() => setShowColdStartTip(false)}
          >
            ✕
          </button>
        </div>
      )}

      <main className="message-list">
        {messages.length === 0 ? (
          <div className="empty-state">
            <p className="empty-title">{t.empty.title}</p>
            <div className="sample-grid">
              {t.empty.samples.map((q) => (
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
            placeholder={t.input.placeholder}
            rows={1}
          />
          <button type="submit" disabled={loading || !input.trim()}>
            {loading ? t.input.sending : t.input.send}
          </button>
        </form>
      </footer>
    </div>
  );
}

export default App;
