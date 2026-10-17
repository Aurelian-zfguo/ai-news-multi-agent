"""入口：单次 kickoff，产出每日 AI 热点日报。

用法（在项目根目录，已激活 .venv）：
    .venv/Scripts/python.exe main.py
"""
from __future__ import annotations

import datetime
from pathlib import Path

from src.crew import build_crew
from src.mock_data import format_mock_feed

PROJECT_ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_ROOT / "output"


def main() -> None:
    raw_feed = format_mock_feed()
    date_str = datetime.date.today().strftime("%Y-%m-%d")

    crew = build_crew()
    result = crew.kickoff(inputs={"raw_feed": raw_feed, "today": date_str})

    # 取最终任务的原始输出作为日报正文
    report = getattr(result, "raw", None) or str(result)

    OUTPUT_DIR.mkdir(exist_ok=True)
    out_path = OUTPUT_DIR / f"每日AI热点日报_{date_str}.md"
    out_path.write_text(report, encoding="utf-8")

    print("\n" + "=" * 60)
    print(f"日报已保存：{out_path}")
    print("=" * 60)
    print("Token 用量：", getattr(result, "token_usage", "N/A"))
    print("检查点目录：.checkpoints/（用于失败恢复与回放）")


if __name__ == "__main__":
    main()
