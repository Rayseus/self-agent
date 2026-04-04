# Seft-Agent 架构设计（RAG 全栈）

## 1. 目标与范围

- 目标：基于个人简历与项目经验构建问答 Agent，稳定回答“你会什么、做过什么、如何做”的问题。
- 范围：MVP 覆盖单轮问答、来源引用、基础日志；后续再扩展多轮记忆与评测体系。

## 2. 总体架构

```text
Web(React/Vite)
   -> FastAPI(/api/chat)
      -> Retrieval(BM25 + Vector + Rerank)
      -> LLM Generation(受约束 Prompt)
      -> Postgres(pgvector) + 文档库
```

系统分层：

- 前端层：聊天交互、回答渲染、引用展示。
- 接口层：请求校验、会话透传、错误处理。
- RAG 层：文档切分、向量检索、重排、上下文拼装。
- 模型层：Embedding 与 LLM 调用封装。
- 数据层：Postgres + pgvector、原始文档与日志表。

## 3. 目录设计

```text
Seft-Agent/
  docs/
    architecture.md
  data/
    profile.md
    faq.md
  backend/
    app/
      main.py
      config.py
      schemas.py
      services/
        rag_service.py
        vector_store.py
        llm_client.py
    requirements.txt
    .env.example
  frontend/
    src/
      main.tsx
      App.tsx
      api.ts
      styles.css
    package.json
    index.html
    tsconfig.json
    vite.config.ts
  infra/
    docker-compose.yml
    init.sql
  README.md
```

## 4. 检索与生成链路

请求链路：

1. 用户问题进入 `/api/chat`。
2. 对 query 做标准化（大小写、空白、基础同义词映射）。
3. `hybrid_search`：
   - BM25 召回（关键词精准匹配）
   - 向量召回（语义匹配）
4. Rerank：按相关性重排，截取 TopN。
5. 构造受约束 Prompt（仅允许引用上下文回答）。
6. LLM 生成答案，附带来源引用。
7. 写入 `qa_logs`（问题、召回片段、答案、耗时）。

## 5. 数据模型（MVP）

- `documents`：原始文档（简历、项目、FAQ）。
- `chunks`：切分片段 + 元数据（项目名、时间、标签）。
- `embeddings`：chunk 向量。
- `qa_logs`：问答日志与反馈。

推荐元数据：

- `source_type`: resume | project | faq
- `source_name`: 文档名/项目名
- `tags`: 技术栈关键词数组
- `period`: 时间区间（如 2023-2025）

## 6. Prompt 约束

系统提示词原则：

- 只基于检索到的上下文回答，不编造经历。
- 如果资料不足，明确说明“未在当前资料中找到”。
- 回答尽量量化，优先给结果、职责、技术方案。
- 输出结构：结论 + 证据点 + 引用来源。

## 7. API 设计（MVP）

- `GET /health`：健康检查。
- `POST /api/chat`：
  - request: `question`, `session_id(optional)`
  - response: `answer`, `citations[]`, `trace_id`

## 8. 部署建议

- 本地开发：`docker-compose` 启动 Postgres（含 pgvector）。
- 后端：Python 3.11 + FastAPI。
- 前端：React + Vite。
- 生产部署：
  - web/api 分离部署。
  - 数据库托管（带备份策略）。
  - 日志接入监控（响应时间、失败率、空召回率）。

## 9. 迭代路线图

- v0.1：单轮 RAG + 引用 + 日志（当前框架）。
- v0.2：评测集与自动评估（命中率、事实准确率、拒答准确率）。
- v0.3：多轮上下文记忆、用户画像问答策略。
- v0.4：管理后台（文档上传、重建索引、反馈分析）。
