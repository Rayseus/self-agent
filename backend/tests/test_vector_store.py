"""vector_store 纯函数单测：_extract_keywords / _rrf_merge。"""

from app.services.vector_store import RetrievedChunk, VectorStore, _extract_keywords


class TestExtractKeywords:
    def test_chinese_only(self):
        kws = _extract_keywords("你做过哪些项目？")
        assert "你做过哪些项目" in kws

    def test_english_only(self):
        kws = _extract_keywords("Which framework do you use?")
        assert "which" in kws
        assert "framework" in kws

    def test_single_letter_word_filtered(self):
        kws = _extract_keywords("I am a developer")
        assert "i" not in kws
        assert "a" not in kws
        assert "am" in kws
        assert "developer" in kws

    def test_english_lowercased(self):
        kws = _extract_keywords("Use FastAPI")
        assert all(w == w.lower() for w in kws)

    def test_mixed_zh_en(self):
        kws = _extract_keywords("你会用 React 吗？")
        assert "react" in kws

    def test_single_chinese_char_filtered(self):
        kws = _extract_keywords("你 我 他")
        assert kws == []

    def test_empty(self):
        assert _extract_keywords("") == []
        assert _extract_keywords("！？，。") == []

    def test_numbers_in_word(self):
        kws = _extract_keywords("Python3 is good")
        assert "python3" in kws


class TestRRFMerge:
    @staticmethod
    def _chunk(content: str, score: float = 0.0) -> RetrievedChunk:
        return RetrievedChunk(source_name="test.md", content=content, score=score)

    def test_both_lists_share_top_doc_ranks_first(self):
        c_a = self._chunk("A")
        c_b = self._chunk("B")
        c_c = self._chunk("C")
        vec = [c_a, c_b, c_c]
        kw = [c_a, c_c, c_b]
        merged = VectorStore._rrf_merge(vec, kw, top_k=3)
        assert merged[0].content == "A"

    def test_dedup_by_content(self):
        c_a = self._chunk("A")
        merged = VectorStore._rrf_merge([c_a], [c_a], top_k=5)
        assert len(merged) == 1

    def test_empty_inputs(self):
        assert VectorStore._rrf_merge([], [], top_k=5) == []

    def test_only_vector_results(self):
        c_a = self._chunk("A")
        merged = VectorStore._rrf_merge([c_a], [], top_k=5)
        assert len(merged) == 1
        assert merged[0].content == "A"

    def test_only_keyword_results(self):
        c_a = self._chunk("A")
        merged = VectorStore._rrf_merge([], [c_a], top_k=5)
        assert len(merged) == 1
        assert merged[0].content == "A"

    def test_top_k_truncation(self):
        chunks = [self._chunk(f"C{i}") for i in range(10)]
        merged = VectorStore._rrf_merge(chunks, [], top_k=3)
        assert len(merged) == 3

    def test_score_is_rrf_not_original(self):
        """RRF 分数 = 1/(k+rank+1)，与原始 score 字段无关。"""
        c_a = RetrievedChunk(source_name="x", content="A", score=999.0)
        merged = VectorStore._rrf_merge([c_a], [], top_k=1)
        assert merged[0].score < 1.0
        assert merged[0].score > 0
