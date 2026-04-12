import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta"

REFUSE_ANSWER = "当前资料未涉及该内容，无法回答。"

REFUSE_SIGNALS = [
    "无法回答", "未涉及", "资料不足", "未在当前资料中找到",
    "cannot answer", "not covered", "no relevant information", "insufficient",
]


def is_refuse(answer: str) -> bool:
    lower = answer.lower()
    return any(s in lower for s in REFUSE_SIGNALS)


SYSTEM_PROMPT = """\
你是 Ray 的个人 AI 助手，只能根据以下【参考资料】回答用户问题。

规则：
1. 仅使用参考资料中明确提及的信息，不允许推测或补充资料之外的内容。
2. 回答时标注引用来源编号，如 [1]、[2]。
3. 若参考资料不足以回答该问题，中文场景回复"当前资料未涉及该内容，无法回答。"，英文场景回复 "The provided materials do not cover this topic."
4. 回答应简洁、量化，优先给出结论、职责、技术方案与结果指标。
5. 若用户问题包含指代词（"它""这个""上面提到的"/ "it", "this", "the above"），结合对话历史理解用户真实意图。
6. 用与用户提问相同的语言回答。若用户用英文提问则用英文回答，用中文提问则用中文回答。"""


class LLMClient:
    def generate_answer(
        self,
        question: str,
        numbered_context: str,
        history: list[dict] | None = None,
    ) -> str:
        if not numbered_context.strip():
            return REFUSE_ANSWER

        prompt = f"【参考资料】\n{numbered_context}\n\n用户问题：{question}"
        url = f"{GEMINI_BASE}/{settings.llm_model}:generateContent?key={settings.gemini_api_key}"
        proxy = settings.proxy_url or None

        contents: list[dict] = []
        for turn in history or []:
            role = "model" if turn["role"] in ("assistant", "model") else "user"
            contents.append({"role": role, "parts": [{"text": turn["content"]}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        payload = {
            "contents": contents,
            "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "generationConfig": {"temperature": 0.3, "maxOutputTokens": 1024},
        }

        try:
            with httpx.Client(proxy=proxy, timeout=30) as client:
                resp = client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPStatusError as e:
            logger.error("Gemini API error: %s — %s", e.response.status_code, e.response.text[:500])
            return REFUSE_ANSWER

        candidates = data.get("candidates", [])
        if not candidates:
            return REFUSE_ANSWER

        parts = candidates[0].get("content", {}).get("parts", [])
        return parts[0]["text"] if parts else REFUSE_ANSWER
