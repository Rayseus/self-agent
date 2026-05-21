# Feature Specification: 每日使用统计与问题汇总

**Feature Branch**: `001-daily-stats`  
**Created**: 2026-05-20  
**Status**: Draft  
**Input**: 统计每天使用的人/次数，汇总用户提出的问题；admin 鉴权用 ADMIN_TOKEN 环境变量；先做 API 不做前端 admin 页

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 管理员查看每日使用概览 (Priority: P1)

管理员通过 API 查询指定日期范围的使用统计数据，包括总问答量、唯一会话数（代表独立用户）、唯一 IP 数、平均响应延迟，快速掌握产品使用情况。

**Why this priority**: 核心需求——了解"有多少人在用、用了多少次"是所有后续分析的基础。

**Independent Test**: 调用 `GET /admin/stats?from=2026-05-01&to=2026-05-20` 返回 JSON 包含 total_questions、unique_sessions、unique_ips、avg_latency_ms 字段。

**Acceptance Scenarios**:

1. **Given** 存在 qa_logs 记录，**When** 管理员带合法 token 调用 `/admin/stats?from=&to=`，**Then** 返回指定范围内的聚合统计 JSON
2. **Given** 请求未携带 token 或 token 不匹配，**When** 调用任何 `/admin/*` 端点，**Then** 返回 401 Unauthorized
3. **Given** 指定日期无数据，**When** 调用统计端点，**Then** 返回零值字段而非报错

---

### User Story 2 - 管理员查看当日问题列表 (Priority: P1)

管理员查询指定日期用户提出的所有问题，以发现高频问题和用户关注趋势。

**Why this priority**: 与 US1 并列核心——"问了什么"比"问了多少"更能指导知识库优化。

**Independent Test**: 调用 `GET /admin/questions?day=2026-05-20&limit=50` 返回问题列表，含 question、trace_id、created_at。

**Acceptance Scenarios**:

1. **Given** 当日有 N 条问答记录，**When** 管理员调用 `/admin/questions?day=...&limit=50`，**Then** 返回最多 50 条，按时间倒序
2. **Given** limit 参数缺省，**When** 调用端点，**Then** 默认返回 50 条
3. **Given** 当日无记录，**When** 调用端点，**Then** 返回空列表

---

### User Story 3 - 每日自动聚合 (Priority: P2)

系统每日自动（通过 GitHub Actions cron）聚合前一天的数据到汇总表，管理员也可手动触发。

**Why this priority**: 自动化避免每次查询都实时聚合大量记录，保证查询性能。

**Independent Test**: 调用 `POST /admin/aggregate?day=2026-05-19` 后查询 `/admin/stats` 确认数据已聚合。

**Acceptance Scenarios**:

1. **Given** 前一天有 qa_logs 记录，**When** 触发聚合（cron 或手动 POST），**Then** qa_daily_summary 表写入该日汇总行
2. **Given** 已存在某日汇总，**When** 再次聚合同一天，**Then** 覆盖更新（幂等）
3. **Given** 聚合的日期无数据，**When** 触发聚合，**Then** 写入零值行（不报错）

---

### Edge Cases

- 并发聚合同一天的数据时（多次手动触发），不应出现重复行或数据不一致
- client_ip 字段为 NULL（老数据、隐私代理），统计时不计入 unique_ips 但不影响其他字段
- qa_logs 中 session_id 为空的旧记录，不计入 unique_sessions

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 系统 MUST 在 `/api/chat` 请求处理时将 client_ip 和 session_id 写入 qa_logs
- **FR-002**: 系统 MUST 提供 `GET /admin/stats` 端点，返回指定日期范围的使用统计
- **FR-003**: 系统 MUST 提供 `GET /admin/questions` 端点，返回指定日期的问题列表（分页）
- **FR-004**: 系统 MUST 提供 `POST /admin/aggregate` 端点，触发指定日期的数据聚合
- **FR-005**: 所有 `/admin/*` 端点 MUST 通过 `X-Admin-Token` header 与环境变量 `ADMIN_TOKEN` 比对做鉴权
- **FR-006**: 系统 MUST 支持通过 GitHub Actions cron 每日自动调用聚合端点
- **FR-007**: 聚合操作 MUST 是幂等的（重复执行同一天不产生重复数据）

### Key Entities

- **qa_logs（扩展）**: 原有问答日志表，新增 session_id（VARCHAR 64）、client_ip（INET）字段
- **qa_daily_summary**: 日汇总表，主键为 day（DATE），记录当日总量、唯一会话/IP 数、平均延迟、高频问题 JSONB

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 管理员可在 5 秒内获取任意日期范围的使用统计数据
- **SC-002**: 聚合操作对 1000 条日志的处理时间 < 3 秒
- **SC-003**: 所有 admin 端点在无合法 token 时 100% 返回 401
- **SC-004**: 每日 cron 聚合成功率 > 99%（排除外部网络因素）

## Assumptions

- 现有 `qa_logs` 表已有 question、answer、trace_id、latency_ms、created_at 字段，无需迁移
- 部署在 Render Free Tier，cron 触发由 GitHub Actions 承担（非服务本身）
- 当前数据量极小（日均 < 100 条），无需分区或物化视图
- client_ip 存储完整 IP，不做脱敏（个人项目，无合规要求）
- 前端 admin 页面将在后续独立 Block 中实现，本期仅提供 API
