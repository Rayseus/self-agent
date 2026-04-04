# Seft-Agent

一个面向“个人介绍与项目经历问答”的 RAG 全栈项目。用户提问后，系统基于简历、项目与 FAQ 资料进行检索增强生成，并返回答案与引用来源。

## 技术栈

- 前端：React + Vite + TypeScript
- 后端：FastAPI + Pydantic
- 数据库：PostgreSQL + pgvector
- 检索策略：Hybrid（BM25 + Vector）+ Rerank（预留）

## 项目结构

- `docs/`：架构与说明文档
- `data/`：知识库样例数据
- `backend/`：API 与 RAG 核心逻辑
- `frontend/`：聊天界面
- `infra/`：本地基础设施（docker-compose）

## 快速开始

1. 启动数据库（可选）

```bash
cd infra
docker compose up -d
```

2. 启动后端

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

4. 访问

- Web: `http://localhost:5173`
- API: `http://localhost:8000`

## 文档

- 架构文档：`docs/architecture.md`

## 许可证

仅用于学习与个人项目演示。
