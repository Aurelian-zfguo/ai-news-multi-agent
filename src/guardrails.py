"""任务护栏函数。

护栏签名约定（CrewAI 1.15.x）：`guardrail(task_output) -> Tuple[bool, Any]`
- 返回 (True, 结果) 表示通过，data 会作为（可能被转换后的）任务输出继续流转。
- 返回 (False, 反馈文案) 表示不通过，失败原因会被注入 Agent 上下文，触发重试。

注意：返回类型注解必须是 `typing.Tuple[bool, Any]`（大写 Tuple），
否则 CrewAI 的护栏校验会抛 ValueError。
"""
import re
from typing import Any, Tuple

_CJK = re.compile(r"[一-鿿]")


def validate_summary_quality(result: Any) -> Tuple[bool, Any]:
    """摘要任务护栏：验证摘要是否完整、为中文、覆盖足够内容。"""
    text = str(result).strip()
    problems: list[str] = []

    if not text:
        return (False, "输出为空，请为每条内容生成中文摘要。")
    if len(text) < 100:
        problems.append("总长度不足 100 字，疑似未覆盖全部条目")
    if not _CJK.search(text):
        problems.append("未包含中文摘要内容")
    if "http" not in text:
        problems.append("摘要未保留原始链接")

    if problems:
        return (False, "摘要质量不合格：" + "；".join(problems) + "。请重新生成。")
    return (True, text)


def validate_report_completeness(result: Any) -> Tuple[bool, Any]:
    """归档任务护栏：验证 Markdown 日报结构完整、按主题分类。"""
    text = str(result).strip()
    problems: list[str] = []

    if not text:
        return (False, "输出为空，请生成完整日报。")
    if "#" not in text:
        problems.append("缺少 Markdown 标题（#）")
    if "## " not in text:
        problems.append("缺少按主题分类的二级标题（## 分类）")
    if not _CJK.search(text):
        problems.append("日报未包含中文内容")
    if "20" not in text:
        problems.append("缺少日期信息")

    if problems:
        return (False, "日报不完整：" + "；".join(problems) + "。请补全。")
    return (True, text)
