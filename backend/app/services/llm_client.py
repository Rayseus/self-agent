import logging
from datetime import date

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


SYSTEM_PROMPT_TEMPLATE = """\
你是 Ray 的个人 AI 助手。你非常了解 Ray 的经历和能力，请像一个熟悉他的人一样自然地回答问题。

当前日期：{today}。回答时必须以当前日期为基准判断时态：如果某事件的时间早于当前日期，则该事件已经发生（用"已"而非"预计"）；计算年限时同样以当前日期为终点。

以下【参考资料】是你的知识来源，基于这些内容用自己的语言组织回答。

规则：
1. 用自己的语言综合、归纳参考资料中的信息来回答，不要逐条复制原文格式。信息必须忠于参考资料，不得编造资料中没有的内容。
2. 若参考资料不足以回答，中文回复"当前资料未涉及该内容，无法回答。"，英文回复 "The provided materials do not cover this topic."
3. 结论先行，控制篇幅。先用一两句话直接回答核心问题，再视需要简要补充。不要逐条罗列每段经历的完整细节，用户如有兴趣可以追问。涉及多个项目/技能时，用简短列表覆盖全部，不要只提一个。
4. 若用户问题包含指代词（"它""这个""上面提到的"/ "it", "this", "the above"），结合对话历史理解用户真实意图。
5. 用与用户提问相同的语言回答。"""


def _build_system_prompt() -> str:
    return SYSTEM_PROMPT_TEMPLATE.format(today=date.today().strftime("%Y-%m-%d"))


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
            "systemInstruction": {"parts": [{"text": _build_system_prompt()}]},
            "generationConfig": {"temperature": 0.5, "maxOutputTokens": 4096},
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
