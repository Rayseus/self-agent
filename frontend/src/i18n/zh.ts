import type { Dict } from "./types";

const zh: Dict = {
  header: {
    title: "Self-Agent",
    desc: "基于个人简历与项目经验的 RAG 问答助手",
    newChat: "新对话",
  },
  empty: {
    title: "有什么想了解的？试试这些问题：",
    samples: [
      "你擅长什么技术栈？",
      "你在 RAG 项目里负责了哪些核心工作？",
      "介绍一下你的项目经历",
      "你的工作经验有多久？",
    ],
  },
  input: {
    placeholder: "输入您想问我的问题…",
    send: "发送",
    sending: "回答中…",
  },
  error: {
    request: (status: number) => `请求失败：${status}`,
    unknown: "未知错误",
  },
  coldStart: {
    tip: "服务器冷启动中，首次提问可能需 30-60 秒唤醒，请稍候。",
    dismiss: "关闭提示",
  },
};

export default zh;
