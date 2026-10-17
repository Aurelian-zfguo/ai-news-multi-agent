# 每日AI热点学习 — CrewAI 多智能体系统设计规格

- 日期：2026-10-16
- 状态：已批准
- 目标：基于 CrewAI 构建一个 4 Agent + Manager 的多智能体系统，用于面试展示 Multi-Agent 协作的完整机制。

---

## 1. 目标与范围

构建「每日AI热点学习」系统：从 RSS/API 采集 AI 文章 → 筛选 Agent/RAG/LLM 相关内容 → 生成中文摘要 → 按主题归档为 Markdown 日报。

本项目的核心不是「跑通」，而是**体现 Multi-Agent 协作的完整机制**，用于面试展示。重点能力：

1. Hierarchical Process（Manager 动态调度）
2. Agent 间委派（Delegate Work Tool）
3. Agent 间提问（Ask Question Tool）
4. 任务护栏与重试（Guardrail + Retry）
5. 跨 Agent 回退（Fallback / Rework Loop）
6. Checkpointing（状态快照与失败恢复）

---

## 2. 关键技术决策

| 决策点 | 选择 | 理由 |
|---|---|---|
| LLM 服务 | DeepSeek（`deepseek/deepseek-chat`） | 便宜、中文摘要质量好、OpenAI 兼容 |
| base_url | `https://api.deepseek.com/v1` | CrewAI DeepSeek provider 标准端点 |
| API Key | `DEEPSEEK_API_KEY`（已写入 `.env`） | 独立 .env，加入 .gitignore |
| Python | 3.13（winget 安装） | CrewAI 要求 `>=3.10, <3.14`，当前机器只有 3.14 |
| 数据源 | 第一轮使用模拟 RSS 数据（`mock_data.py`） | 不连接真实 API |
| 运行策略 | 单次真实 `crew.kickoff()` | 用一次运行既验证机制又产出日报，避免重复消耗 token |
| 错误策略 | API 错误（401/超时/余额不足）立即暂停汇报 | 不自动重试 |

---

## 3. 项目结构

```
每日AI热点学习/
├── .env                     # DEEPSEEK_API_KEY（用户提供）+ 可选 DEEPSEEK_BASE_URL
├── .gitignore               # .env / venv / .checkpoints/ / __pycache__ / output
├── requirements.txt         # crewai[tools]
├── README.md                # 项目说明（Agent 角色 / 协作 / 回退）
├── docs/
│   └── 多Agent协作与回退机制说明.md   # 面试要点（每个机制 → 知识点）
├── output/
│   └── 每日AI热点日报_2026-10-16.md  # 真实生成的示例日报
├── src/
│   ├── __init__.py
│   ├── config.py            # DeepSeek LLM 单例、路径常量
│   ├── mock_data.py         # 模拟 RSS 数据（约 12 条，含相关 + 不相关）
│   ├── agents.py            # 4 个 Agent + 自定义 Manager
│   ├── guardrails.py        # 2 个护栏函数
│   ├── tasks.py             # 4 个 Task + context 链 + 护栏
│   └── crew.py              # 组装 Crew(hierarchical, checkpoint=True)
└── main.py                  # 入口：kickoff → 保存日报 → 打印机制日志摘要
```

---

## 4. Agent 定义

所有 Agent `allow_delegation=True`（Manager 天然开启且不能挂自定义工具）。

| Agent | Role | Goal 要点 | Backstory 要点 | 协作用途 |
|---|---|---|---|---|
| 采集专员 collector | AI信息采集专家 | 从 RSS/API 获取最新 AI 文章列表 | 熟悉各类 AI 信息源，高效抓取 | 被委派「重新抓取原始链接」 |
| 筛选专员 filter | AI内容筛选专家 | 过滤 Agent/RAG/LLM 高度相关内容 | 对技术趋势敏感，判断内容价值 | 主动向采集专员询问来源/时间 |
| 摘要专员 summarizer | AI内容摘要专家 | 生成简洁准确的中文摘要 | 技术写作，提炼核心信息 | 把「重取链接」委派回采集专员 |
| 归档专员 editor | AI日报编辑 | 按主题分类生成 Markdown 日报 | 编辑经验，重结构与可读性 | 验证摘要，不合格回退 |
| Manager manager | 调度与质检经理 | 动态分配、验证结果、按数量扩范围 | 熟悉工作流编排与质量控制 | 核心调度 |

---

## 5. Task 定义与护栏

Task 链（`context` 串联）：

```
collect(采集) → filter(筛选, context=[collect]) → summarize(摘要, context=[filter])
            → archive(归档, context=[summarize])  → 输出 Markdown 日报
```

| Task | Agent | context | guardrail |
|---|---|---|---|
| collect | 采集专员 | — | — |
| filter | 筛选专员 | [collect] | — |
| summarize | 摘要专员 | [filter] | `validate_summary_quality`, `guardrail_max_retries=3` |
| archive | 归档专员 | [summarize] | `validate_report_completeness`, `guardrail_max_retries=3` |

**护栏函数**（返回 `(bool, data)`）：

- `validate_summary_quality(result)`：检查每条摘要非空、是中文、长度达标、含关键要素；失败返回 `(False, 具体反馈)` 让摘要专员重写。
- `validate_report_completeness(result)`：检查日报含全部 N 条、按主题分类、有日期标题；失败返回 `(False, 缺哪些)`。

**重试参数两处覆盖**：
- Task 级 `guardrail_max_retries`（护栏验证失败重试）
- Agent 级 `max_retry_limit`（技术性失败重试上限）

---

## 6. 协作机制 → CrewAI API 映射

| 机制 | 落地方式 | Multi-Agent 知识点 |
|---|---|---|
| 层级调度 | `process=Process.hierarchical` + 自定义 `manager_agent` | Hierarchical Process / Manager Orchestration |
| 主动询问 | `allow_delegation=True` → Ask Question Tool | Ask Question Tool / Inter-Agent Communication |
| 任务委派 | 同上 → Delegate Work Tool | Task Delegation |
| 护栏 + 重试 | Task `guardrail` + `guardrail_max_retries` | Guardrails / Validation & Retry |
| 跨 Agent 回退 | Manager 指令（检测下游不合格 → 重新分派上游）+ 护栏反馈 | Cross-Agent Fallback / Rework Loop |
| 动态扩范围 | Manager 指令「若筛选结果 < N 条，令采集专员扩源」 | Dynamic Task Planning |
| 状态快照 | `Crew(checkpoint=True)`（写 `./.checkpoints/`，支持 `from_checkpoint` 恢复） | Checkpointing / State Persistence |

**关键区分（面试要点）**：护栏重试是「同 Agent 重做」（失败原因注入上下文）；真正的跨 Agent 回退通过 Manager 的动态重新分派实现。护栏返回的失败信息进 Manager 上下文，Manager 据此把活退回正确 Agent。

---

## 7. 运行计划

1. winget 装 Python 3.13 → 建 venv → `pip install 'crewai[tools]'`
2. 全程使用 `mock_data.py` 模拟 RSS（约 12 条，含相关 + 不相关项）
3. 一次真实 `crew.kickoff()`：产出日报，同时通过 verbose 日志 + `.checkpoints/` 验证机制
4. API 错误立即暂停汇报，不自动重试

---

## 8. 交付物

1. 可运行 CrewAI 项目（上述结构）
2. `output/每日AI热点日报_2026-10-16.md`（真实生成）
3. `README.md`
4. `docs/多Agent协作与回退机制说明.md`（面试要点）

---

## 9. API 校正记录

- 用户 spec 中的 `max_retry_limit` → 护栏重试用 Task `guardrail_max_retries`（默认 3）；另有 `Task.max_retries`（技术失败）与 `Agent.max_retry_limit`（Agent 级）。
- 自定义 `manager_agent` 不能挂 tools（否则抛 `Manager agent should not have tools`），其 `allow_delegation` 被框架强制 True。
- DeepSeek 模型名用 `deepseek/deepseek-chat`（provider 前缀），base_url 用 `https://api.deepseek.com/v1`。
