# Self-Agent

一个面向"个人介绍与项目经历问答"的 RAG 全栈项目。用户提问后，系统基于简历、项目与 FAQ 资料进行检索增强生成，返回自然语言回答。

**在线体验**：[https://self-agent-web.onrender.com]

> Free tier 首次访问需等待 30-50 秒唤醒后端服务。

## 技术栈

- 前端：React + Vite + TypeScript
- 后端：FastAPI + Pydantic
- 数据库：PostgreSQL + pgvector
- 检索策略：Hybrid（ILIKE + Vector）+ RRF 融合排序
- LLM / Embedding：Gemini API（gemini-2.5-flash / gemini-embedding-001）
- 部署：Render（前端 Static Site + 后端 Web Service + PostgreSQL）

## 项目结构

- `docs/`：架构与说明文档
- `data/`：知识库数据（profile / projects / skills / faq）
- `backend/`：API 与 RAG 核心逻辑
- `frontend/`：聊天界面
- `infra/`：数据库初始化脚本（init.sql / docker-compose）

## 文档

- 架构文档：`docs/architecture.md`

## 许可证

仅用于学习与个人项目演示。
