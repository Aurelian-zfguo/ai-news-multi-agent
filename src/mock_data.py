"""模拟 RSS 数据（第一轮不连接真实 API）。

设计意图：
- 8 条与 Agent / RAG / LLM 强相关，4 条无关（硬件/机器人/芯片/量子），让筛选专员有真实的过滤工作。
- 第 5 条刻意把 url 置空，为「摘要专员把『重新获取原始链接』委派回采集专员」制造触发条件。
"""
from __future__ import annotations

ARTICLES: list[dict] = [
    {
        "id": 1,
        "title": "A Survey of Multi-Agent Collaboration Frameworks",
        "source": "ArXiv",
        "url": "https://arxiv.org/abs/2601.12345",
        "published_at": "2026-10-15",
        "brief": "综述多智能体协作框架的设计模式与工程权衡",
        "tags": ["Agent", "多智能体"],
    },
    {
        "id": 2,
        "title": "RAG 2.0: Graph-based Retrieval for Long-context LLMs",
        "source": "Hugging Face Blog",
        "url": "https://huggingface.co/blog/rag-2.0",
        "published_at": "2026-10-15",
        "brief": "图检索增强生成在长上下文场景的性能提升",
        "tags": ["RAG"],
    },
    {
        "id": 3,
        "title": "Llama 4 系列开源：长上下文与工具调用能力升级",
        "source": "Meta AI Blog",
        "url": "https://ai.meta.com/blog/llama-4",
        "published_at": "2026-10-14",
        "brief": "Meta 开源 Llama 4，主打长上下文和 agentic 能力",
        "tags": ["LLM"],
    },
    {
        "id": 4,
        "title": "OpenAI Swarm 2.0：轻量级多智能体编排与交接",
        "source": "OpenAI Blog",
        "url": "https://openai.com/blog/swarm-2",
        "published_at": "2026-10-14",
        "brief": "Swarm 2.0 聚焦 Agent 间任务交接与动态路由",
        "tags": ["Agent", "多智能体"],
    },
    {
        "id": 5,
        "title": "向量检索的稀疏-稠密混合：生产环境最佳实践",
        "source": "Zilliz Blog",
        "url": "",  # 刻意缺失，制造委派「重新获取原始链接」的触发条件
        "published_at": "2026-10-13",
        "brief": "稀疏 + 稠密混合检索在 RAG 中的落地经验",
        "tags": ["RAG"],
    },
    {
        "id": 6,
        "title": "LLM 推理成本优化：Prompt 缓存与批处理调度",
        "source": "Anthropic Engineering",
        "url": "https://www.anthropic.com/engineering/prompt-caching",
        "published_at": "2026-10-13",
        "brief": "降低 LLM 推理成本的工程手段",
        "tags": ["LLM"],
    },
    {
        "id": 7,
        "title": "多智能体系统的动态任务规划：从静态流水线到调度器",
        "source": "机器之心",
        "url": "https://www.jiqizhixin.com/articles/2026-10-12-1",
        "published_at": "2026-10-12",
        "brief": "多智能体任务规划的技术演进",
        "tags": ["Agent", "多智能体"],
    },
    {
        "id": 8,
        "title": "Agent 记忆机制：跨会话上下文保持的三种方案",
        "source": "Lilian Weng's Blog",
        "url": "https://lilianweng.github.io/posts/agent-memory",
        "published_at": "2026-10-12",
        "brief": "智能体长期记忆的工程实现",
        "tags": ["Agent"],
    },
    {
        "id": 9,
        "title": "NVIDIA Blackwell Ultra 架构发布：算力再翻倍",
        "source": "AnandTech",
        "url": "https://www.anandtech.com/blackwell-ultra",
        "published_at": "2026-10-15",
        "brief": "新一代 GPU 架构，与 AI 应用无直接关系",
        "tags": ["硬件", "芯片"],
    },
    {
        "id": 10,
        "title": "特斯拉 Optimus 人形机器人量产进度",
        "source": "TechCrunch",
        "url": "https://techcrunch.com/optimus",
        "published_at": "2026-10-14",
        "brief": "人形机器人量产进度，与 Agent/LLM 无关",
        "tags": ["机器人"],
    },
    {
        "id": 11,
        "title": "台积电 2nm 制程良率爬坡，2027 年量产",
        "source": "DigiTimes",
        "url": "https://www.digitimes.com/2nm",
        "published_at": "2026-10-13",
        "brief": "半导体制程进展，与 AI 软件栈无关",
        "tags": ["芯片"],
    },
    {
        "id": 12,
        "title": "量子计算 1000 量子比特处理器新突破",
        "source": "Nature",
        "url": "https://www.nature.com/quantum-1000",
        "published_at": "2026-10-12",
        "brief": "量子计算硬件进展，与 Agent/RAG/LLM 无关",
        "tags": ["量子计算"],
    },
]


def format_mock_feed() -> str:
    """把模拟数据格式化成一段可注入采集任务描述的可读文本。"""
    blocks = []
    for a in ARTICLES:
        url = a["url"] if a["url"] else "(链接缺失，需重新获取)"
        blocks.append(
            f"[{a['id']}] {a['title']}\n"
            f"    来源: {a['source']} | 发布时间: {a['published_at']}\n"
            f"    链接: {url}\n"
            f"    简介: {a['brief']}\n"
            f"    标签: {', '.join(a['tags'])}"
        )
    return "\n\n".join(blocks)
