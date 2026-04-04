class LLMClient:
    def generate_answer(self, question: str, context_blocks: list[str]) -> str:
        if not context_blocks:
            return "未在当前资料中找到可支撑的内容。"

        merged_context = "\n".join(context_blocks[:3])
        return (
            "基于你的资料，当前问题可从以下经验支撑：\n"
            f"{merged_context}\n"
            "如果你愿意，我可以继续展开具体项目职责、技术方案与结果指标。"
        )
