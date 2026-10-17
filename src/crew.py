"""组装 Crew：Hierarchical Process + 自定义 Manager + Checkpointing。"""
from __future__ import annotations

from crewai import Crew, Process

from src.agents import (
    collector_agent,
    editor_agent,
    filter_agent,
    manager_agent,
    summarizer_agent,
)
from src.tasks import archive_task, collect_task, filter_task, summarize_task


def build_crew() -> Crew:
    """构建层级调度 Crew。

    - process=Process.hierarchical：Manager 动态调度。
    - manager_agent=manager_agent：自定义调度与质检经理。
    - checkpoint=True：在 ./checkpoints/ 写状态快照，支持失败恢复。
    """
    return Crew(
        agents=[collector_agent, filter_agent, summarizer_agent, editor_agent],
        tasks=[collect_task, filter_task, summarize_task, archive_task],
        process=Process.hierarchical,
        manager_agent=manager_agent,
        checkpoint=True,
        verbose=True,
    )
