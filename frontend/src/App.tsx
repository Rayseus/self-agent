import { FormEvent, useState } from "react";
import { chat, Citation } from "./api";

function App() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [citations, setCitations] = useState<Citation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!question.trim()) return;

    setLoading(true);
    setError("");
    try {
      const result = await chat(question.trim());
      setAnswer(result.answer);
      setCitations(result.citations);
    } catch (err) {
      setError(err instanceof Error ? err.message : "未知错误");
      setAnswer("");
      setCitations([]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="container">
      <h1>Seft-Agent</h1>
      <p className="desc">基于个人简历与项目经验的 RAG 问答助手</p>

      <form onSubmit={onSubmit} className="card">
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="例如：你在 RAG 项目里负责了哪些核心工作？"
          rows={4}
        />
        <button type="submit" disabled={loading}>
          {loading ? "回答中..." : "发送问题"}
        </button>
      </form>

      {error ? <p className="error">{error}</p> : null}

      {answer ? (
        <section className="card">
          <h2>回答</h2>
          <p>{answer}</p>

          <h3>引用来源</h3>
          <ul>
            {citations.map((item, idx) => (
              <li key={`${item.source_name}-${idx}`}>
                <strong>{item.source_name}</strong>：{item.snippet}
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </main>
  );
}

export default App;
