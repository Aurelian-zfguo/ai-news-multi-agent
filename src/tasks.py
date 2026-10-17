"""Task 定义：采集 → 筛选 → 摘要 → 归档，通过 context 串联。"""
from __future__ import annotations

from crewai import Task

from src.agents import collector_agent, editor_agent, filter_agent, summarizer_agent
from src.guardrails import validate_report_completeness, validate_summary_quality

# 1. 采集任务：把模拟 RSS 数据整理成原始条目列表
collect_task = Task(
    description=(
        "以下是模拟 RSS 数据源返回的最新 AI 文章列表（第一轮为模拟数据，不连接真实 API）。\n\n"
        "模拟 RSS 数据：\n{raw_feed}\n\n"
        "请将这些数据整理成结构化的原始条目列表，每条包含：标题、来源、URL、发布时间、一句话简介。"
        "不要遗漏任何一条，也不要篡改信息。"
    ),
    expected_output="一个结构化的文章条目列表，每条含标题 / 来源 / URL / 发布时间 / 简介",
    agent=collector_agent,
)

# 2. 筛选任务：过滤 Agent/RAG/LLM 相关内容，可向采集专员询问来源
filter_task = Task(
    description=(
        "基于采集专员提供的原始条目列表，筛选出与「Agent / RAG / LLM」高度相关的内容。\n\n"
        "筛选标准：\n"
        "1. 标题或简介涉及 AI Agent、多智能体、RAG（检索增强生成）、LLM / 大语言模型、Agent 记忆、任务规划等；\n"
        "2. 排除纯硬件、芯片制造、量子计算、机器人等与上述主题无关的内容。\n\n"
        "对来源或发布时间不明确的条目，可用 Ask Question Tool 主动向采集专员询问来源与发布时间。\n"
        "输出筛选后的条目列表，并为每条标注相关度判断理由。"
    ),
    expected_output="筛选后的相关条目列表，每条含相关度判断理由",
    agent=filter_agent,
    context=[collect_task],
)

# 3. 摘要任务：生成中文摘要，带护栏验证摘要质量
summarize_task = Task(
    description=(
        "基于筛选专员输出的相关条目，为每一条内容生成简洁、准确的中文摘要。\n\n"
        "要求：\n"
        "1. 每条摘要 60~120 字，使用中文；\n"
        "2. 提炼核心信息：讲清楚这条内容是什么、为什么重要、关键结论；\n"
        "3. 每条摘要后保留原始链接。\n\n"
        "如果某条内容的原始链接缺失或不完整，用 Delegate Work Tool 把「重新获取原始链接」委派给采集专员，"
        "拿到链接后再补全，不要自行编造。"
    ),
    expected_output="每条内容的中文摘要列表，含标题 / 中文摘要 / 原始链接",
    agent=summarizer_agent,
    context=[filter_task],
    guardrail=validate_summary_quality,
    guardrail_max_retries=3,
)

# 4. 归档任务：生成 Markdown 日报，带护栏验证完整性
archive_task = Task(
    description=(
        "基于摘要专员输出的中文摘要，按主题分类，生成一份结构清晰的 Markdown 中文日报。\n\n"
        "要求：\n"
        "1. 日报标题包含今天日期（今天是 {today}）；\n"
        "2. 按主题分类（例如：AI Agent、RAG、LLM 基础、多智能体协作等）；\n"
        "3. 每个分类下按「标题 + 中文摘要 + 链接」列出条目；\n"
        "4. 日报末尾附一段「今日概览」小结。\n\n"
        "验证每条摘要是否完整；若发现摘要缺失或质量不合格，不要自行编造内容，"
        "应把问题反馈给 Manager，由 Manager 回退给摘要专员重新生成。"
    ),
    expected_output="一份完整、按主题分类清晰、可读性强的 Markdown 格式中文日报",
    agent=editor_agent,
    context=[summarize_task],
    guardrail=validate_report_completeness,
    guardrail_max_retries=3,
)
