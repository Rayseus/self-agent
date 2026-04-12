# 版本变更记录

## v0.4 — 双语支持 + 知识库充实 + 检索增强（进行中）

### 已完成

- **双语问答支持**：系统支持中英文提问与回答
  - System Prompt 增加语言跟随指令（用与用户提问相同的语言回答）
  - 拒答文案双语化（中文/英文各一套标准拒答）
  - 拒答判断从字符串精确匹配改为 `is_refuse()` 语义检测（中英信号词通吃）
  - 指代消解指令补充英文指代词（"it"/"this"/"the above"）
  - 评测脚本 `is_refuse()` 同步支持英文信号词

### 变更文件

| 文件 | 变更 |
|------|------|
| `app/services/llm_client.py` | 新增 `REFUSE_SIGNALS` / `is_refuse()`；Prompt 增加语言跟随 + 双语拒答 + 英文指代词 |
| `app/services/rag_service.py` | 拒答判断改用 `is_refuse()` 语义检测，保留 LLM 原始回答文本 |
| `scripts/evaluate.py` | `is_refuse()` 补充英文信号词 + `.lower()` 统一比较 |

---

## v0.3 — 多轮对话 + UI 升级

### 新增功能

- **多轮对话**：支持基于 `session_id` 的多轮上下文对话，后端自动管理对话历史
  - 新增 `conversation_turns` 表持久化对话轮次
  - `SessionManager` 服务：历史获取、存储、token 截断（上限 4000）
  - LLM 调用采用 Gemini `contents[]` 多轮消息格式
  - 系统 Prompt 增加指代消解能力（"它"/"这个"/"上面提到的"）
- **聊天 UI 重构**：从单问单答升级为消息流聊天界面
  - user / assistant 气泡样式
  - 自动滚底
  - 引用来源折叠展示（`<details>`）
  - 空状态引导（4 个示例问题可点击）
  - 加载态 typing dots 脉冲动画
  - "新对话" 按钮重置 session
  - Enter 发送 / Shift+Enter 换行
- **多轮评测**：新增 8 条多轮评测用例（id 41-48）
  - 覆盖追问、指代消解、上下文切换、多轮后拒答
  - `evaluate.py` 支持 `type: "multi_turn"` 用例，按 turns 顺序累积 history

### 变更文件

| 模块 | 文件 | 变更 |
|------|------|------|
| 数据库 | `infra/init.sql` | 新增 `conversation_turns` 表 + 索引 |
| 后端 | `app/models.py` | 新增 `ConversationTurn` ORM |
| 后端 | `app/schemas.py` | `session_id` 改为自动生成 UUID |
| 后端 | `app/services/session_manager.py` | **新建** — 对话历史管理 |
| 后端 | `app/services/llm_client.py` | 支持 `history` 参数 + 多轮 `contents[]` |
| 后端 | `app/services/rag_service.py` | 透传 `history` 至 LLM |
| 后端 | `app/main.py` | 注入 SessionManager，异步存对话轮次 |
| 前端 | `frontend/src/api.ts` | `chat()` 新增 `sessionId` 参数 |
| 前端 | `frontend/src/App.tsx` | 聊天消息流 UI 重构 |
| 前端 | `frontend/src/styles.css` | 气泡 / 布局 / 动画样式 |
| 评测 | `data/eval_questions.json` | 新增 8 条多轮用例 |
| 评测 | `scripts/evaluate.py` | 支持多轮评测模式 |

---

## v0.2 — RAG 完整链路 + 评测体系

### 新增功能

- **数据入库**：`scripts/ingest.py` 读取 `data/*.md`，按标题分段 + token 二次切分（max 600, overlap 80），调 Gemini Embedding API 生成 3072 维向量写入数据库
- **混合检索**：pgvector 余弦相似度 + 关键词 ILIKE，RRF（Reciprocal Rank Fusion）合并排序
- **LLM 回答**：接入 Gemini `generateContent` REST API，受约束系统 Prompt（仅基于资料回答、标注引用、资料不足拒答），API 异常优雅降级
- **RAG 编排**：编号 context 传入 LLM，RRF 分数阈值过滤，端到端耗时统计
- **观测日志**：`qa_logs` 表记录问答详情（`BackgroundTasks` 异步落库）
- **评测体系**：40 条评测问题 + `evaluate.py` 脚本，支持命中率 / 事实准确率 / 拒答准确率 / 关键词命中率，可生成 `docs/eval_report.md`

### 关键配置

- Embedding 模型：`gemini-embedding-001`（3072 维）
- LLM 模型：`gemini-2.5-flash`
- 向量索引：因 3072 维超出 pgvector 默认编译限制，暂用顺序扫描

---

## v0.1 — 项目初始化

### 新增功能

- **前端**：React + Vite + TypeScript，聊天页 + API 请求封装
- **后端**：FastAPI，`GET /health` + `POST /api/chat`，RAG 服务骨架
- **数据库**：Docker Compose（Postgres + pgvector），初始表结构（documents / chunks / embeddings / qa_logs）
- **知识库**：`data/profile.md` + `data/faq.md` 示例数据
- **文档**：`docs/architecture.md` 架构文档 + `README.md`
