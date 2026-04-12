# Self-Agent 架构设计（RAG 全栈）

## 1. 目标与范围

- 目标：基于个人简历与项目经验构建问答 Agent，准确回答"你会什么、做过什么、如何做"等问题。
- 已实现：多轮对话、双语问答（中/英）、混合检索、RRF 排序、拒答机制、评测体系。

## 2. 总体架构

```text
React/Vite (Render Static Site)
  → FastAPI /api/chat (Render Web Service)
    → Hybrid Search (ILIKE + pgvector 余弦相似度)
    → RRF 融合排序
    → Gemini LLM 生成 (受约束 System Prompt)
    → PostgreSQL + pgvector (Render Postgres)
```

系统分层：

- 前端层：聊天交互、多轮会话管理、回答渲染。
- 接口层：请求校验、session 透传、后台异步日志落库。
- RAG 层：混合检索（ILIKE 关键词 + pgvector 向量）、RRF 排序、阈值过滤、上下文拼装。
- 模型层：Gemini Embedding（gemini-embedding-001, 3072 维）与 LLM（gemini-2.5-flash）调用封装。
- 数据层：PostgreSQL + pgvector + pg_trgm，文档/chunk/embedding/对话/日志表。

## 3. 目录设计

```text
Self-Agent/
  docs/
    architecture.md
  data/
    profile.md              # 个人概述、核心能力、职业时间线
    projects.md             # 项目经历
    skills.md               # 技术栈分组
    faq.md                  # 高频问答（教育、工作、求职状态等）
    raw/                    # 原始素材（不参与 ingest）
  backend/
    app/
      main.py               # FastAPI 入口、/health、/api/chat
      config.py              # Pydantic Settings，环境变量管理
      db.py                  # SQLAlchemy 连接池
      models.py              # ORM 模型（Document/Chunk/Embedding/QALog/ConversationTurn）
      schemas.py             # 请求/响应 schema
      services/
        rag_service.py       # RAG 主链路：检索 → 过滤 → 生成
        vector_store.py      # 混合检索：向量 + ILIKE + RRF 合并
        embedding_client.py  # Gemini Embedding REST API
        llm_client.py        # Gemini LLM REST API + System Prompt
        session_manager.py   # 多轮对话历史管理
    scripts/
      ingest.py              # 知识库导入：Markdown → 切分 → Embedding → 写库
      evaluate.py            # 自动评测脚本
    requirements.txt
  frontend/
    src/
      main.tsx
      App.tsx                # 聊天 UI、多轮会话、示例问题
      api.ts                 # API 请求封装
      styles.css
    package.json
  infra/
    docker-compose.yml       # 本地 PostgreSQL + pgvector
    init.sql                 # 建表脚本（含扩展、索引）
  render.yaml                # Render Blueprint 配置
  README.md
```

## 4. 检索与生成链路

1. 用户问题 + session_id 进入 `/api/chat`。
2. `SessionManager` 加载当前 session 的历史对话（最近 10 轮，token 截断）。
3. `hybrid_search`（top_k=8）：
   - **向量召回**：query → Gemini Embedding → pgvector 余弦相似度（`<=>` 算子）。
   - **关键词召回**：提取中文词 + 英文词 → ILIKE 匹配（pg_trgm 加速）。
4. **RRF 融合**：Reciprocal Rank Fusion 合并两路结果，按 RRF 分数排序。
5. **阈值过滤**：RRF 分数 < 0.005 的 chunk 丢弃，全部低于阈值则直接拒答。
6. 构造上下文 + 历史对话 → Gemini LLM 生成回答（System Prompt 含当前日期、时态判断规则）。
7. 异步写入 `qa_logs`（问题、命中 chunk、分数、答案、耗时）和 `conversation_turns`。

## 5. 数据模型

| 表 | 用途 |
|----|------|
| `documents` | 原始文档（source_type, source_name, content） |
| `chunks` | 切分片段 + 元数据 JSON（heading, source） |
| `embeddings` | chunk 向量（3072 维，gemini-embedding-001） |
| `qa_logs` | 问答日志（question, answer, latency_ms, hit_chunks, retrieval_scores） |
| `conversation_turns` | 多轮对话历史（session_id, role, content） |

## 6. Prompt 设计

System Prompt 核心策略：

- 角色定位为"熟悉 Ray 的个人助手"，用自己的语言综合归纳，而非搬运原文。
- 动态注入当前日期，要求 LLM 根据日期判断时态（已发生 vs 未发生）。
- 结论先行、控制篇幅，列举类问题覆盖全部再展开。
- 资料不足时标准化拒答（中英双语）。
- 指代消解：结合对话历史理解"它""这个"等指代词。
- 语言跟随：用户用什么语言提问就用什么语言回答。

## 7. API 设计

- `GET /health`：健康检查。
- `POST /api/chat`：
  - request：`question`、`session_id`
  - response：`answer`、`citations[]`、`trace_id`

## 8. 部署架构

已部署至 Render（Oregon 区域）：

| 服务 | 类型 | 说明 |
|------|------|------|
| `self-agent-web` | Static Site | React 前端，全球 CDN |
| `self-agent-api` | Web Service | FastAPI 后端 |
| PostgreSQL 16 + pgvector | Managed Database | 知识库 + 对话数据 |
| Gemini API | 外部服务 | Embedding + LLM（Render 在美国可直连） |

线上地址：[https://self-agent-web.onrender.com]

## 9. 迭代历程

- **v0.1**：项目骨架搭建，前后端 + 数据库 + RAG 占位实现。
- **v0.2**：数据入库与切分、向量化与混合检索（ILIKE + Vector + RRF）、回答链路增强、评测体系（48 条用例）。
- **v0.3**：多轮对话（SessionManager + conversation_turns）、前端聊天 UI 升级。
- **v0.4**：双语问答、知识库扩充（3 → 35+ chunk）、System Prompt 优化、Render 云端部署。
