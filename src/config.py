"""全局配置：DeepSeek LLM 单例 + 环境变量加载。"""
from __future__ import annotations

import os
from pathlib import Path

from crewai import LLM

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"


def load_env() -> None:
    """手动加载 .env（不依赖 dotenv，仅 setdefault，已存在的环境变量优先）。"""
    if not ENV_PATH.exists():
        return
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


_LLM: LLM | None = None


def get_deepseek_llm() -> LLM:
    """返回 DeepSeek 的 CrewAI LLM 单例（OpenAI 兼容接口）。"""
    global _LLM
    if _LLM is None:
        load_env()
        _LLM = LLM(
            model="deepseek/deepseek-chat",
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            temperature=0.3,
        )
    return _LLM
