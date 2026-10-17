"""Agent 定义：4 个专员 + 1 个自定义 Manager。"""
from __future__ import annotations

from crewai import Agent

from src.config import get_deepseek_llm

_llm = get_deepseek_llm()

# ---------------------------------------------------------------------------
# 四个专员 Agent
# ---------------------------------------------------------------------------
collector_agent = Agent(
    role="AI信息采集专家",
    goal="从 RSS/API 数据源中高效抓取最新的 AI 相关文章，整理成结构化的原始条目列表",
    backstory=(
        "你熟悉各类 AI 信息源（ArXiv、技术博客、科技媒体等），擅长高效抓取与规范化数据。"
        "你负责产出最原始的文章条目，供下游筛选专员使用。"
    ),
    allow_delegation=True,
    max_retry_limit=3,
    llm=_llm,
    verbose=True,
)

filter_agent = Agent(
    role="AI内容筛选专家",
    goal="从采集专员提供的原始列表中，过滤出与 Agent / RAG / LLM 高度相关的内容，并给出判断理由",
    backstory=(
        "你对 AI 技术趋势敏感，能快速判断一条内容的主题与价值。"
        "当某条内容的来源或发布时间不明确时，你会主动向采集专员询问，而不是凭空猜测。"
    ),
    allow_delegation=True,
    max_retry_limit=3,
    llm=_llm,
    verbose=True,
)

summarizer_agent = Agent(
    role="AI内容摘要专家",
    goal="为筛选后的每一条内容生成简洁、准确的中文摘要，并保留原始链接",
    backstory=(
        "你擅长技术写作，能从原文中提炼核心信息（是什么、为什么重要、关键结论）。"
        "当某条内容的原始链接缺失时，你会把『重新获取原始链接』委派给采集专员，而不是自己编造。"
    ),
    allow_delegation=True,
    max_retry_limit=3,
    llm=_llm,
    verbose=True,
)

editor_agent = Agent(
    role="AI日报编辑",
    goal="按主题把摘要分类，生成一份结构清晰、可读性强的 Markdown 中文日报",
    backstory=(
        "你具备编辑经验，注重内容结构与可读性。"
        "归档时你会验证每条摘要是否完整；若发现摘要缺失或质量不合格，你不会自行编造，"
        "而是把问题反馈给 Manager，由 Manager 回退给摘要专员重新生成。"
    ),
    allow_delegation=True,
    max_retry_limit=3,
    llm=_llm,
    verbose=True,
)

# ---------------------------------------------------------------------------
# 自定义 Manager Agent（层级调度核心）
# 约束：Manager 不能挂自定义 tools，否则 CrewAI 会抛「Manager agent should not have tools」。
# allow_delegation 会被框架强制为 True，这里显式声明以表意。
# ---------------------------------------------------------------------------
manager_agent = Agent(
    role="调度与质检经理",
    goal=(
        "动态调度四个专员协作，验证每一步的输出质量，确保最终产出一份完整、准确、"
        "按主题分类清晰的中文 AI 热点日报"
    ),
    backstory=(
        "你是一名资深的多智能体工作流调度经理，负责编排「采集 → 筛选 → 摘要 → 归档」流水线。你的工作准则：\n"
        "1) 根据任务类型，把工作分配给具备对应能力的专员；\n"
        "2) 检查每一步的输出质量，不合格就把任务退回给对应专员重做，而不是自己代劳；\n"
        "3) 如果筛选后的相关条目数量不足（少于 3 条），要求采集专员扩大采集范围重新抓取；\n"
        "4) 发现下游（归档）环节判定上游（摘要）输出不合格时，把任务回退给摘要专员重新生成；\n"
        "5) 最终把关日报的完整性与可读性。"
    ),
    allow_delegation=True,
    llm=_llm,
    verbose=True,
)
