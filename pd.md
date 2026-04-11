## 项目目标

这是一个个人介绍型 RAG Agent 项目，目标是：用户提问后，系统基于我的简历与项目经验做检索增强回答，准确说明我的能力与经历。

## 当前已完成（v0.1 初版）

### 1) 架构与文档
- 已输出架构文档：`docs/architecture.md`
- 已补充项目说明：`README.md`
- 已明确系统分层：前端 / 后端 / RAG / 数据库 / 部署

### 2) 项目框架搭建
- 前端（React + Vite + TS）：
  - 聊天页、请求封装、基础样式
  - 可调用后端 `/api/chat`
- 后端（FastAPI）：
  - `GET /health`
  - `POST /api/chat`
  - RAG 服务骨架（检索与生成为可替换占位实现）
- 数据库与基础设施：
  - `infra/docker-compose.yml`（Postgres + pgvector）
  - `infra/init.sql`（documents/chunks/embeddings/qa_logs 初始表）
- 知识库示例数据：
  - `data/profile.md`
  - `data/faq.md`

### 3) Git 与远程仓库
- 已在 `Seft-Agent` 初始化 Git 仓库并完成初次提交
- 首次提交：
  - commit: `49e315f`
  - message: `feat(init): scaffold initial RAG full-stack project`
- 已推送到远程：
  - `https://github.com/Rayseus/self-agent.git`
  - 分支：`main`

## 当前已完成（v0.2 进行中）

### 1) 数据入库与切分 ✅
- 新建 `app/db.py`：SQLAlchemy 连接池 + `SessionLocal`
- 新建 `app/models.py`：`Document` / `Chunk` / `Embedding` / `QALog` 四张表的 ORM 模型
- 新建 `scripts/ingest.py`：文档导入脚本
  - 读取 `data/*.md` → 按标题分段 → token 限制二次切分（max 600, overlap 80）
  - 调 Gemini Embedding API 生成向量 → 写入 `embeddings` 表
  - 支持 `--dry-run` 模式验证切分逻辑
- 验证结果：2 个文档 → 3 段 → 3 条 chunk + embedding（3072 维）

### 2) 向量化与检索 ✅
- 新建 `app/services/embedding_client.py`：Gemini REST API 封装（httpx），支持代理
- 改造 `app/services/vector_store.py`：
  - pgvector 余弦相似度检索（`<=>` 算子）
  - 关键词 ILIKE 检索（中文词 + 英文词提取）
  - RRF（Reciprocal Rank Fusion）合并两路结果
- 验证结果：查询"你擅长什么技术"正确召回 3 条相关 chunk，排序合理

### 3) 配置与基础设施更新
- `config.py`：切换至 Gemini API（`gemini-embedding-001` / `gemini-2.5-flash`），新增 `proxy_url`，`extra="ignore"` 兼容代理环境变量
- `init.sql`：向量维度 `1024 → 3072`，增加 `pg_trgm` 扩展及 `gin_trgm_ops` 索引；ivfflat/hnsw 索引因 3072 维超出 pgvector 编译限制暂注释
- `requirements.txt`：增加 `google-generativeai`
- `.env.example`：同步新增 `PROXY_URL` 等配置项

### 4) 回答链路增强 ✅
- 改造 `app/services/llm_client.py`：
  - 接入 Gemini `generateContent` REST API（httpx + 代理，与 embedding_client 一致）
  - 设计受约束系统 Prompt：仅基于检索资料回答、标注引用编号 `[1][2]`、资料不足时标准化拒答
  - API 异常（429/5xx）优雅降级为拒答，日志记录错误详情
- 改造 `app/services/rag_service.py`：
  - 构建编号 context（`[1] 来源: xxx\n内容`）传入 LLM
  - RRF 分数阈值过滤（`MIN_RRF_SCORE = 0.005`），低于阈值直接拒答不调 LLM
  - LLM 拒答时清空引用列表
  - 端到端耗时统计（`time.perf_counter()`），返回 `latency_ms`
- 改造 `app/main.py`：解构 `latency_ms`，日志输出 `trace_id` / 耗时 / 引用数
- 验证结果：
  - 正常问题（"你擅长什么技术"）→ 基于资料回答 + 引用标注 `[2]`
  - 无关问题（"你会弹钢琴吗"）→ 正确拒答，引用为空

### 5) 观测与评测 ✅
- `QALog` 模型补充字段（`latency_ms`、`hit_chunks`、`retrieval_scores`）
- `chat` 端点写入 `qa_logs`（`BackgroundTasks` 异步落库）
- 制作 40 条评测问题（能力类/项目类/边界拒答类/FAQ 类）→ `data/eval_questions.json`
- 评估脚本 `scripts/evaluate.py`：命中率、事实准确率、拒答准确率
- 输出评测报告 `docs/eval_report.md`（`--report` 参数自动生成）
- `rag_service.py` 返回值重构为 `AnswerResult` dataclass，携带检索详情
- `init.sql` 同步更新 `qa_logs` 表结构

## 当前状态
- v0.2 全部任务已完成
- 完整链路：`data/*.md → chunks → embedding → hybrid_search → 编号 context → Gemini LLM → 结构化回答 + 引用 → qa_logs 落库`
- LLM 模型：`gemini-2.5-flash`（`gemini-2.0-flash` 免费配额已耗尽）
- 评测体系就绪：40 条评测样例，支持命中率/事实准确率/拒答准确率/关键词命中率自动评估

## 当前已完成（v0.3 多轮对话 + UI 升级）

### 1) 多轮对话基础设施 ✅
- `infra/init.sql` 新增 `conversation_turns` 表 + `idx_turns_session` 复合索引
- `app/models.py` 新增 `ConversationTurn` ORM 模型
- `app/schemas.py`：`ChatRequest.session_id` 改为 `str = Field(default_factory=uuid4)`，保证每次请求都有 session_id
- 新建 `app/services/session_manager.py`：
  - `get_history(session_id, max_turns=10)`：按 `created_at ASC` 取最近 N 轮，自动 token 截断
  - `save_turn(session_id, role, content)`：持久化单轮对话
  - `truncate_by_tokens(history, max_tokens=4000)`：从最早一轮开始丢弃，粗估 token 不超限

### 2) RAG 链路注入对话历史 ✅
- 改造 `app/services/llm_client.py`：
  - `generate_answer()` 新增 `history` 参数
  - 构建 Gemini `contents[]` 多轮消息格式，历史轮次前置于当前 prompt
  - 系统 Prompt 增加第 5 条指代消解指令
- 改造 `app/services/rag_service.py`：`answer()` 新增 `history` 参数，透传至 LLM Client
- 改造 `app/main.py`：
  - 注入 `SessionManager` 实例
  - `chat()` 先取历史 → 带上下文生成回答 → 异步保存 user/assistant turn
  - 日志增加 `session` 和 `history_turns` 字段

### 3) 前端多轮对话 + UI 升级 ✅
- `frontend/src/api.ts`：`chat()` 新增 `sessionId` 参数，请求体携带 `session_id`
- `frontend/src/App.tsx` 全面重构：
  - `sessionId` + `messages` state 管理多轮对话
  - "新对话" 按钮重置 session
  - 空状态引导：4 个示例问题可点击填充
  - 加载态：typing dots 脉冲动画
  - Enter 发送 / Shift+Enter 换行
- `frontend/src/styles.css` 聊天 UI 样式：
  - 全屏 flex 布局（header / message-list / input-bar）
  - user 蓝色气泡 / assistant 白色气泡
  - 自动滚底（`useRef` + `scrollIntoView`）
  - 引用来源 `<details>` 折叠展示
  - 响应式 `max-width: 720px`

### 4) 集成验证与评测 ✅
- `data/eval_questions.json` 新增 8 条多轮用例（id 41-48）：
  - 追问、指代消解（"它"/"这个项目"/"上面提到的"）、多轮后拒答、举例追问
- `scripts/evaluate.py` 升级：
  - 新增 `_eval_single()` / `_eval_multi_turn()` 分别处理两种用例
  - 多轮模式按 `turns` 顺序调用，累积 history，仅断言最后一轮
  - 报告中多轮用例以 ` → ` 连接各轮问题
- 评测体系：48 条评测样例（40 单轮 + 8 多轮）
