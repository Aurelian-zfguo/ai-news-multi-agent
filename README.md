# 每日AI热点学习 —— 基于 CrewAI 的 4 Agent + Manager 多智能体系统

一个用于**面试展示 Multi-Agent 协作机制**的 CrewAI 项目：从模拟 RSS 数据采集 AI 文章，经筛选、中文摘要，最终按主题归档为 Markdown 日报。

> 本项目是**多智能体骨架的基准实现**——底层架构（Hierarchical Process + Manager 调度 + Guardrails + Checkpointing）已复用到姊妹项目「国内AI热点解析」，体现「架构复用 + 多业务场景适配」的工程能力。

## 一、系统架构

```
                 ┌─────────────────────────┐
                 │   Manager（调度与质检）    │  ← Process.hierarchical 动态调度
                 └─────────────────────────┘
                      │ 委派 / 询问 / 回退
        ┌─────────────┼─────────────┬─────────────┐
        ▼             ▼             ▼             ▼
   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
   │ 采集专员 │→│ 筛选专员 │→│ 摘要专员 │→│ 归档专员 │
   └─────────┘  └─────────┘  └─────────┘  └─────────┘
    原始列表      相关条目      中文摘要      Markdown 日报
```

## 二、Agent 角色

| Agent | Role | 职责 | 协作能力 |
|---|---|---|---|
| 采集专员 | AI信息采集专家 | 抓取原始文章列表 | 被委派「重新获取链接」 |
| 筛选专员 | AI内容筛选专家 | 过滤 Agent/RAG/LLM 相关内容 | 主动询问来源/时间 |
| 摘要专员 | AI内容摘要专家 | 生成中文摘要 | 委派「重取链接」给采集专员 |
| 归档专员 | AI日报编辑 | 分类生成 Markdown 日报 | 验证摘要，不合格回退 |
| Manager | 调度与质检经理 | 动态调度、结果验证、按数量扩范围 | 跨 Agent 回退 |

所有专员 `allow_delegation=True`（启用 Delegate Work Tool + Ask Question Tool）。

## 三、任务流水线与协作机制

```
collect(采集) → filter(筛选) → summarize(摘要, 护栏) → archive(归档, 护栏) → 日报
```

| 机制 | 实现 |
|---|---|
| 层级调度 | `Process.hierarchical` + 自定义 `manager_agent` |
| 主动询问 | `allow_delegation=True` → Ask Question Tool |
| 任务委派 | 同上 → Delegate Work Tool |
| 护栏 + 重试 | Task `guardrail` + `guardrail_max_retries=3` |
| 跨 Agent 回退 | Manager 指令 + 护栏反馈（组合） |
| 动态扩范围 | Manager backstory（结果 < 3 条时扩源） |
| 状态快照 | `Crew(checkpoint=True)` |

详细机制说明与面试要点见 [`docs/多Agent协作与回退机制说明.md`](docs/多Agent协作与回退机制说明.md)。

> ⚠️ **关键发现（面试加分项）**：层级流程下，专员之间的 Delegate/Ask 工具是「自作用域」的，真正的跨 Agent 委派/回退由 Manager 收口。源码级原因见面试说明第 8 节。

## 四、目录结构

```
├── main.py                 # 入口
├── src/
│   ├── config.py           # DeepSeek LLM 配置 + .env 加载
│   ├── mock_data.py        # 模拟 RSS 数据
│   ├── agents.py           # 4 专员 + Manager
│   ├── guardrails.py       # 2 个护栏函数
│   ├── tasks.py            # 4 个任务（context 串联）
│   └── crew.py             # 组装 Crew
├── docs/
│   └── 多Agent协作与回退机制说明.md
├── output/                 # 生成的日报
└── requirements.txt
```

## 五、环境准备

CrewAI 要求 Python `>=3.10, <3.14`（不支持 3.14）。本机用 Python 3.13 建独立 venv：

```bash
# 1. 创建虚拟环境（用 Python 3.13）
python3.13 -m venv .venv

# 2. 激活
#    Windows (Git Bash):  source .venv/Scripts/activate
#    Windows (CMD):       .venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt
```

## 六、配置

在项目根目录 `.env` 中配置 DeepSeek Key（已加入 `.gitignore`）：

```
DEEPSEEK_API_KEY=sk-xxxx
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1   # 可选，代码默认已设
```

## 七、运行

```bash
.venv/Scripts/python.exe main.py
```

运行后会：
1. 用 `mock_data.py` 的模拟数据跑通「采集→筛选→摘要→归档」全流程；
2. 在 `output/每日AI热点日报_<日期>.md` 生成 Markdown 日报；
3. 在 `.checkpoints/` 写入状态快照（用于失败恢复）。

## 八、跨项目复用

本项目的多智能体骨架已复用到姊妹项目 **「国内AI热点解析」**（GitHub 仓库 `cn-ai-insights-multi-agent`）：

| 维度 | 每日AI热点学习（本项目） | 国内AI热点解析（姊妹项目） |
|---|---|---|
| 业务视角 | 学术 / 技术 | 国内 AI 产业 / 商业 |
| 数据源 | 模拟 RSS | 真实 RSS（feedparser）+ 模拟降级 |
| 护栏 | 通用质量校验 | 结构化业务校验 + 软提示 |
| 复用层 | —— | Hierarchical + Manager + Guardrails + Checkpointing（全复用） |

同一套多智能体骨架，通过替换 Agent 角色、Prompt 和护栏，适配了两个完全不同的业务场景——这证明了架构的**解耦性**与**复用价值**。

## 九、交付物

- ✅ 可运行的 CrewAI 项目（`src/` + `main.py`）
- ✅ Markdown 日报示例（`output/每日AI热点日报_2026-10-16.md`）
- ✅ 本项目 README（Agent 角色 / 协作 / 回退设计）
- ✅ 面试要点说明（`docs/多Agent协作与回退机制说明.md`）
