"""评测脚本：加载 eval_questions.json，调用 RAG 链路评估命中率 / 事实准确率 / 拒答准确率。

支持单轮和多轮（type: "multi_turn"）用例。多轮用例按 turns 顺序调用，共享对话历史，
仅对最后一轮回答做断言。

用法：
    cd backend
    python -m scripts.evaluate
    python -m scripts.evaluate --report   # 同时生成 docs/eval_report.md
"""

import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.llm_client import REFUSE_ANSWER
from app.services.rag_service import RAGService

EVAL_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "eval_questions.json"
REPORT_FILE = Path(__file__).resolve().parent.parent.parent / "docs" / "eval_report.md"


def load_questions() -> list[dict]:
    with open(EVAL_FILE, encoding="utf-8") as f:
        return json.load(f)


def is_refuse(answer: str) -> bool:
    refuse_signals = ["无法回答", "未涉及", "未在当前资料中找到", "资料不足"]
    return any(s in answer for s in refuse_signals)


def check_keywords(answer: str, keywords: list[str]) -> tuple[int, int]:
    """返回 (命中数, 总数)。"""
    if not keywords:
        return 0, 0
    hits = sum(1 for kw in keywords if kw.lower() in answer.lower())
    return hits, len(keywords)


def _eval_single(q: dict, rag: RAGService) -> dict:
    """评测单轮用例。"""
    result = rag.answer(q["question"])
    answer = result.answer
    expected = q["expected_type"]
    actually_refused = is_refuse(answer)
    correct = actually_refused if expected == "refuse" else not actually_refused
    kw_hit, kw_total = check_keywords(answer, q.get("expected_keywords", []))
    return {
        "id": q["id"],
        "question": q["question"],
        "category": q["category"],
        "expected_type": expected,
        "actually_refused": actually_refused,
        "correct": correct,
        "kw_hit": kw_hit,
        "kw_total": kw_total,
        "answer_snippet": answer[:150],
        "latency_ms": result.latency_ms,
        "retrieval_scores": result.retrieval_scores,
    }


def _eval_multi_turn(q: dict, rag: RAGService) -> dict:
    """评测多轮用例：按 turns 顺序调用，累积 history，仅断言最后一轮。"""
    turns: list[dict] = q["turns"]
    history: list[dict] = []
    answer = ""
    last_result = None

    for turn in turns:
        last_result = rag.answer(turn["content"], history=history)
        answer = last_result.answer
        history.append({"role": "user", "content": turn["content"]})
        history.append({"role": "assistant", "content": answer})

    expected = q["expected_type"]
    actually_refused = is_refuse(answer)
    correct = actually_refused if expected == "refuse" else not actually_refused
    kw_hit, kw_total = check_keywords(answer, q.get("expected_keywords", []))
    last_question = turns[-1]["content"]

    return {
        "id": q["id"],
        "question": " → ".join(t["content"] for t in turns),
        "category": q["category"],
        "expected_type": expected,
        "actually_refused": actually_refused,
        "correct": correct,
        "kw_hit": kw_hit,
        "kw_total": kw_total,
        "answer_snippet": answer[:150],
        "latency_ms": last_result.latency_ms if last_result else 0,
        "retrieval_scores": last_result.retrieval_scores if last_result else [],
    }


def run_eval(questions: list[dict], rag: RAGService) -> list[dict]:
    results: list[dict] = []
    for q in questions:
        if q.get("type") == "multi_turn":
            results.append(_eval_multi_turn(q, rag))
        else:
            results.append(_eval_single(q, rag))
    return results


def compute_metrics(results: list[dict]) -> dict:
    total = len(results)
    correct = sum(1 for r in results if r["correct"])

    answer_qs = [r for r in results if r["expected_type"] == "answer"]
    refuse_qs = [r for r in results if r["expected_type"] == "refuse"]

    answer_correct = sum(1 for r in answer_qs if r["correct"])
    refuse_correct = sum(1 for r in refuse_qs if r["correct"])

    kw_hits = sum(r["kw_hit"] for r in answer_qs)
    kw_total = sum(r["kw_total"] for r in answer_qs)

    latencies = [r["latency_ms"] for r in results]
    avg_latency = round(sum(latencies) / len(latencies), 1) if latencies else 0

    return {
        "total": total,
        "overall_accuracy": round(correct / total * 100, 1) if total else 0,
        "answer_count": len(answer_qs),
        "answer_accuracy": round(answer_correct / len(answer_qs) * 100, 1) if answer_qs else 0,
        "refuse_count": len(refuse_qs),
        "refuse_accuracy": round(refuse_correct / len(refuse_qs) * 100, 1) if refuse_qs else 0,
        "keyword_hit_rate": round(kw_hits / kw_total * 100, 1) if kw_total else 0,
        "avg_latency_ms": avg_latency,
    }


def category_metrics(results: list[dict]) -> dict[str, dict]:
    cats: dict[str, list[dict]] = {}
    for r in results:
        cats.setdefault(r["category"], []).append(r)
    return {cat: compute_metrics(rs) for cat, rs in cats.items()}


def generate_report(metrics: dict, cat_metrics: dict, results: list[dict]) -> str:
    lines = [
        "# 评测报告",
        "",
        f"> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## 总体指标",
        "",
        f"| 指标 | 值 |",
        f"|------|-----|",
        f"| 评测题数 | {metrics['total']} |",
        f"| 综合准确率 | {metrics['overall_accuracy']}% |",
        f"| 事实回答准确率 | {metrics['answer_accuracy']}%（{metrics['answer_count']} 题） |",
        f"| 拒答准确率 | {metrics['refuse_accuracy']}%（{metrics['refuse_count']} 题） |",
        f"| 关键词命中率 | {metrics['keyword_hit_rate']}% |",
        f"| 平均延迟 | {metrics['avg_latency_ms']}ms |",
        "",
        "## 分类指标",
        "",
        "| 类别 | 题数 | 准确率 | 关键词命中率 | 平均延迟 |",
        "|------|------|--------|-------------|---------|",
    ]
    for cat, m in cat_metrics.items():
        lines.append(
            f"| {cat} | {m['total']} | {m['overall_accuracy']}% "
            f"| {m['keyword_hit_rate']}% | {m['avg_latency_ms']}ms |"
        )

    lines += ["", "## 详细结果", ""]
    lines.append("| ID | 问题 | 类别 | 期望 | 结果 | 关键词 | 延迟 |")
    lines.append("|-----|------|------|------|------|--------|------|")
    for r in results:
        status = "✅" if r["correct"] else "❌"
        kw = f"{r['kw_hit']}/{r['kw_total']}" if r["kw_total"] else "-"
        lines.append(
            f"| {r['id']} | {r['question']} | {r['category']} "
            f"| {r['expected_type']} | {status} | {kw} | {r['latency_ms']}ms |"
        )

    lines += ["", "## 失败用例", ""]
    failures = [r for r in results if not r["correct"]]
    if not failures:
        lines.append("无失败用例。")
    else:
        for r in failures:
            lines.append(f"### Q{r['id']}: {r['question']}")
            lines.append(f"- 期望：{r['expected_type']}，实际拒答：{r['actually_refused']}")
            lines.append(f"- 回答片段：{r['answer_snippet']}")
            lines.append("")

    return "\n".join(lines) + "\n"


def main(write_report: bool = False) -> None:
    questions = load_questions()
    print(f"加载 {len(questions)} 条评测问题\n")

    rag = RAGService()
    results = run_eval(questions, rag)

    metrics = compute_metrics(results)
    cat_metrics = category_metrics(results)

    print("=" * 50)
    print(f"综合准确率:     {metrics['overall_accuracy']}%")
    print(f"事实回答准确率: {metrics['answer_accuracy']}%（{metrics['answer_count']} 题）")
    print(f"拒答准确率:     {metrics['refuse_accuracy']}%（{metrics['refuse_count']} 题）")
    print(f"关键词命中率:   {metrics['keyword_hit_rate']}%")
    print(f"平均延迟:       {metrics['avg_latency_ms']}ms")
    print("=" * 50)

    failures = [r for r in results if not r["correct"]]
    if failures:
        print(f"\n❌ 失败用例（{len(failures)}）:")
        for r in failures:
            print(f"  Q{r['id']}: {r['question']} (期望={r['expected_type']}, 拒答={r['actually_refused']})")

    if write_report:
        report = generate_report(metrics, cat_metrics, results)
        REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
        REPORT_FILE.write_text(report, encoding="utf-8")
        print(f"\n📄 报告已写入 {REPORT_FILE}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="RAG 评测脚本")
    parser.add_argument("--report", action="store_true", help="生成 docs/eval_report.md")
    args = parser.parse_args()
    main(write_report=args.report)
