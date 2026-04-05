import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta"

REFUSE_ANSWER = "当前资料未涉及该内容，无法回答。"

SYSTEM_PROMPT = """\
你是 Ray 的个人 AI 助手，只能根据以下【参考资料】回答用户问题。

规则：
1. 仅使用参考资料中明确提及的信息，不允许推测或补充资料之外的内容。
2. 回答时标注引用来源编号，如 [1]、[2]。
3. 若参考资料不足以回答该问题，直接回复"当前资料未涉及该内容，无法回答。"
4. 回答应简洁、量化，优先给出结论、职责、技术方案与结果指标。"""


class LLMClient:
    def generate_answer(self, question: str, numbered_context: str) -> str:
        if not numbered_context.strip():
            return REFUSE_ANSWER

        prompt = f"【参考资料】\n{numbered_context}\n\n用户问题：{question}"
        url = f"{GEMINI_BASE}/{settings.llm_model}:generateContent?key={settings.gemini_api_key}"
        proxy = settings.proxy_url or None
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
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
