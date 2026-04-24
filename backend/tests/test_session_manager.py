"""SessionManager 纯函数单测：truncate_by_tokens。"""

from app.services.session_manager import SessionManager


class TestTruncateByTokens:
    def test_under_limit_keeps_all(self):
        history = [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好，有什么可以帮你？"},
        ]
        result = SessionManager.truncate_by_tokens(history, max_tokens=1000)
        assert len(result) == 2

    def test_over_limit_drops_oldest_first(self):
        history = [
            {"role": "user", "content": "A" * 200},
            {"role": "assistant", "content": "B" * 200},
            {"role": "user", "content": "C" * 50},
        ]
        result = SessionManager.truncate_by_tokens(history, max_tokens=100)
        assert all(h["content"][0] != "A" for h in result)

    def test_empty_history(self):
        assert SessionManager.truncate_by_tokens([], max_tokens=1000) == []

    def test_zero_max_tokens_drops_all(self):
        history = [{"role": "user", "content": "anything"}]
        result = SessionManager.truncate_by_tokens(history, max_tokens=0)
        assert result == []

    def test_returns_same_list_object(self):
        """函数当前实现是原地修改，回归测试以防意外改成 copy。"""
        history = [{"role": "user", "content": "x"}]
        result = SessionManager.truncate_by_tokens(history, max_tokens=1000)
        assert result is history

    def test_default_max_tokens_4000(self):
        """默认参数应为 4000，超过即截。"""
        big = [{"role": "user", "content": "X" * 10000}]
        result = SessionManager.truncate_by_tokens(big)
        assert result == []
