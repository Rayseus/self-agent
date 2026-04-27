"""llm_client 纯函数单测：is_refuse / detect_language / error_answer / system prompt 契约。"""

from app.services import llm_client
from app.services.llm_client import (
    RATE_LIMIT_EN,
    RATE_LIMIT_ZH,
    REFUSE_ANSWER_EN,
    REFUSE_ANSWER_ZH,
    SERVICE_ERROR_EN,
    SERVICE_ERROR_ZH,
    detect_language,
    error_answer,
    is_refuse,
)


class TestIsRefuse:
    def test_chinese_refuse(self):
        assert is_refuse(REFUSE_ANSWER_ZH)
        assert is_refuse("当前资料未涉及该内容，无法回答。")
        assert is_refuse("资料不足，无法给出答案")

    def test_english_refuse(self):
        assert is_refuse(REFUSE_ANSWER_EN)
        assert is_refuse("The provided materials do not cover this topic.")
        assert is_refuse("This is not covered in the provided context.")
        assert is_refuse("Sorry, I cannot answer that.")
        assert is_refuse("There is no relevant information.")

    def test_normal_answer_not_refuse(self):
        assert not is_refuse("我擅长 RAG 与全栈工程，主导过多个 LLM 应用项目。")
        assert not is_refuse("I am skilled in RAG and full-stack engineering.")

    def test_service_error_not_refuse(self):
        """故障文案不应被误判为拒答。"""
        assert not is_refuse(SERVICE_ERROR_ZH)
        assert not is_refuse(SERVICE_ERROR_EN)

    def test_rate_limit_not_refuse(self):
        assert not is_refuse(RATE_LIMIT_ZH)
        assert not is_refuse(RATE_LIMIT_EN)

    def test_case_insensitive(self):
        assert is_refuse("CANNOT ANSWER this question")
        assert is_refuse("DO NOT COVER")

    def test_empty(self):
        assert not is_refuse("")


class TestDetectLanguage:
    def test_chinese(self):
        assert detect_language("你好") == "zh"
        assert detect_language("你的角色是什么？") == "zh"

    def test_english(self):
        assert detect_language("Hello") == "en"
        assert detect_language("What can you do?") == "en"

    def test_mixed_treated_as_chinese(self):
        """含 CJK 即视为中文。"""
        assert detect_language("你会 React 吗？") == "zh"

    def test_empty_treated_as_english(self):
        assert detect_language("") == "en"

    def test_punctuation_only(self):
        assert detect_language("?!.") == "en"


class TestErrorAnswer:
    def test_rate_limit_chinese(self):
        assert error_answer("rate_limit", "你好吗？") == RATE_LIMIT_ZH

    def test_rate_limit_english(self):
        assert error_answer("rate_limit", "How are you?") == RATE_LIMIT_EN

    def test_service_error_chinese(self):
        assert error_answer("service_error", "你好吗？") == SERVICE_ERROR_ZH

    def test_service_error_english(self):
        assert error_answer("service_error", "How are you?") == SERVICE_ERROR_EN

    def test_unknown_kind_falls_back_to_service_error(self):
        """未知 kind 兜底回 service_error 文案。"""
        assert error_answer("weird_kind", "你好吗？") == SERVICE_ERROR_ZH
        assert error_answer("", "Hi") == SERVICE_ERROR_EN


class TestSystemPromptContract:
    """System Prompt 契约测试：防止后续迭代误删跨语言翻译指令。"""

    def test_contains_today(self):
        prompt = llm_client._build_system_prompt()
        assert "当前日期" in prompt

    def test_contains_translation_directive(self):
        """方案 A 强制翻译指令必须存在，否则英文提问会出现中文 bullet 标签。"""
        prompt = llm_client._build_system_prompt()
        assert "语言一致性" in prompt
        assert "翻译" in prompt
        assert "CJK" in prompt

    def test_contains_proper_noun_whitelist(self):
        """专有名词白名单避免把 FastAPI/Georgia Tech 误译。"""
        prompt = llm_client._build_system_prompt()
        assert "FastAPI" in prompt
        assert "Georgia Tech" in prompt
