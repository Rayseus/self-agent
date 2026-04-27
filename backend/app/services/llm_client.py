import logging
import re
from datetime import date

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta"

# ---------- 差异化响应文案 ----------
# 区分三类场景，避免统一用"资料未涉及"误导用户：
#   1. REFUSE       —— 真正的资料不足拒答（业务正常）
#   2. SERVICE_ERROR —— 系统故障（超时/网络/5xx/未知）
#   3. RATE_LIMIT    —— 限流（HTTP 429）

REFUSE_ANSWER_ZH = "当前资料未涉及该内容，无法回答。"
REFUSE_ANSWER_EN = "The provided materials do not cover this topic."
REFUSE_ANSWER = REFUSE_ANSWER_ZH  # 向后兼容：默认中文拒答

SERVICE_ERROR_ZH = "服务暂时不可用，请稍后重试。"
SERVICE_ERROR_EN = "Service temporarily unavailable, please try again later."

RATE_LIMIT_ZH = "当前请求较多，请稍后重试。"
RATE_LIMIT_EN = "The service is busy, please try again later."

REFUSE_SIGNALS = [
    "无法回答", "未涉及", "资料不足", "未在当前资料中找到",
    "cannot answer", "do not cover", "not covered", "no relevant information", "insufficient",
]

_CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def is_refuse(answer: str) -> bool:
    lower = answer.lower()
    return any(s in lower for s in REFUSE_SIGNALS)


def detect_language(text: str) -> str:
    """极简语言检测：含 CJK 字符视为中文，否则英文。用于故障文案选择。"""
    return "zh" if _CJK_RE.search(text) else "en"


def error_answer(kind: str, question: str) -> str:
    """根据故障类型 + 问题语言返回对应文案。"""
    lang = detect_language(question)
    if kind == "rate_limit":
        return RATE_LIMIT_ZH if lang == "zh" else RATE_LIMIT_EN
    return SERVICE_ERROR_ZH if lang == "zh" else SERVICE_ERROR_EN


class LLMError(RuntimeError):
    """LLM 调用故障。kind 区分类型供上层返回差异化文案。

    kind:
        "rate_limit"     — HTTP 429 限流
        "service_error"  — 其他 HTTP 错误 / 超时 / 网络断开 / 空响应 / 未知异常
    """

    def __init__(self, kind: str, original: Exception | str | None = None) -> None:
        self.kind = kind
        self.original = original
        super().__init__(f"{kind}: {original}")


SYSTEM_PROMPT_TEMPLATE = """\
你是 Ray 的个人 AI 助手。你非常了解 Ray 的经历和能力，请像一个熟悉他的人一样自然地回答问题。

当前日期：{today}。回答时必须以当前日期为基准判断时态：如果某事件的时间早于当前日期，则该事件已经发生（用"已"而非"预计"）；计算年限时同样以当前日期为终点。

以下【参考资料】是你的知识来源，基于这些内容用自己的语言组织回答。

规则：
1. 用自己的语言综合、归纳参考资料中的信息来回答，不要逐条复制原文格式。信息必须忠于参考资料，不得编造资料中没有的内容。
2. 若参考资料不足以回答，中文回复"当前资料未涉及该内容，无法回答。"，英文回复 "The provided materials do not cover this topic."
3. 结论先行，控制篇幅。先用一两句话直接回答核心问题，再视需要简要补充。不要逐条罗列每段经历的完整细节，用户如有兴趣可以追问。涉及多个项目/技能时，用简短列表覆盖全部，不要只提一个。
4. 若用户问题包含指代词（"它""这个""上面提到的"/ "it", "this", "the above"），结合对话历史理解用户真实意图。
5. 语言一致性（关键）：必须用与用户提问完全相同的语言回答。
   - 若提问语言与参考资料语言不一致，必须将资料中的所有专业术语、技能名、章节标题、bullet 标签翻译到提问语言，不得保留原语言词汇（人名、机构名、产品名、技术品牌名等专有名词除外，例如 Ray / Georgia Tech / DJI / FastAPI / PostgreSQL）。
   - 用英文回答时禁止出现任何 CJK 字符与中文标点（。 ， ； ： "" 「」 等），列表分隔用英文逗号 "," 与句号 "."。
   - 用中文回答时同样不要混入英文整句叙述。
   - 例：参考资料含 "**后端语言与框架**：Python（FastAPI）、Node.js（Express）、Golang。"，英文提问应输出 "**Backend stack**: Python (FastAPI), Node.js (Express), Golang." 而非保留中文标签或顿号。"""


def _build_system_prompt() -> str:
    return SYSTEM_PROMPT_TEMPLATE.format(today=date.today().strftime("%Y-%m-%d"))


class LLMClient:
    def generate_answer(
        self,
        question: str,
        numbered_context: str,
        history: list[dict] | None = None,
    ) -> str:
        """正常：返回模型文本。
        资料空：返回拒答（语言随 question）。
        故障：抛 LLMError，由 rag_service 降级。
        """
        if not numbered_context.strip():
            return REFUSE_ANSWER_ZH if detect_language(question) == "zh" else REFUSE_ANSWER_EN

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
            status = e.response.status_code
            logger.error("Gemini API http error: %s — %s", status, e.response.text[:500])
            if status == 429:
                raise LLMError("rate_limit", e) from e
            raise LLMError("service_error", e) from e
        except (httpx.TimeoutException, httpx.TransportError) as e:
            logger.error("Gemini API transport failure: %s", e)
            raise LLMError("service_error", e) from e
        except Exception as e:
            logger.exception("Gemini API unexpected error")
            raise LLMError("service_error", e) from e

        candidates = data.get("candidates", [])
        if not candidates:
            logger.warning("Gemini returned empty candidates: %s", str(data)[:500])
            raise LLMError("service_error", "empty candidates")

        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts:
            logger.warning("Gemini returned empty parts")
            raise LLMError("service_error", "empty parts")

        return parts[0]["text"]
