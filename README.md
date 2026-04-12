# Self-Agent

A full-stack RAG project for personal introduction and project experience Q&A. The system retrieves relevant information from resume, projects, and FAQ documents to generate natural language answers.

**Live Demo**: [https://self-agent-web.onrender.com]

> Free tier: first visit may take 30-50 seconds to wake up the backend service.

## Tech Stack

- Frontend: React + Vite + TypeScript
- Backend: FastAPI + Pydantic
- Database: PostgreSQL + pgvector
- Retrieval: Hybrid (ILIKE + Vector) + RRF fusion ranking
- LLM / Embedding: Gemini API (gemini-2.5-flash / gemini-embedding-001)
- Deployment: Render (Static Site + Web Service + PostgreSQL)

## Project Structure

- `docs/` — Architecture and documentation
- `data/` — Knowledge base (profile / projects / skills / faq)
- `backend/` — API and RAG core logic
- `frontend/` — Chat interface
- `infra/` — Database init scripts (init.sql / docker-compose)

## Documentation

- Architecture: `docs/architecture.md`

## License

For learning and personal project demonstration only.

---

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
