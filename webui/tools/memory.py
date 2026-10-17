# title: 长期记忆工具 Memory
# author: tablet-full-ai-workbench
# author_url: https://github.com/Andy-hub-byte/tablet-full-ai-workbench
# description: 保存和回忆重要信息（用户偏好、项目背景、常用约定），实现跨对话的长期记忆，让 AI 越用越懂你。
# version: 0.1.0

"""
长期记忆工具（Open WebUI Tool）
================================

核心能力：跨对话记忆。

* save_memory    ：保存一条记忆（内容 + 标签）
* recall_memory  ：按关键词回忆相关记忆
* list_memories  ：列出全部记忆（可按标签过滤）
* forget_memory  ：删除一条记忆

存储方式：本地 JSONL 文件（默认 /root/.tablet-workbench/data/memory/memories.jsonl），
完全本地存储，保护隐私。

说明：Open WebUI 也内置了记忆功能（设置 → 个性化 → 记忆），
本工具作为补充，提供更结构化的标签管理与关键词回忆。
"""

import json
import os
import time
from typing import Optional

from pydantic import BaseModel, Field


class Tools:
    """Open WebUI 工具入口类：提供长期记忆相关工具方法。"""

    class Valves(BaseModel):
        """管理员级配置。"""

        data_dir: str = Field(
            default="/root/.tablet-workbench/data",
            description="记忆数据存储目录（本地路径）",
        )

    class UserValves(BaseModel):
        """用户级配置。"""

        default_recall_limit: int = Field(default=5, description="回忆时默认返回的记忆条数")

    def __init__(self):
        pass

    # ------------------------------------------------------------------ 数据存取
    def _memory_file(self) -> str:
        """返回记忆文件路径（目录不存在则创建）。"""
        d = os.path.join(self.valves.data_dir, "memory")
        os.makedirs(d, exist_ok=True)
        return os.path.join(d, "memories.jsonl")

    def _load_all(self) -> list:
        path = self._memory_file()
        if not os.path.exists(path):
            return []
        items = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        items.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue  # 跳过损坏的行，保证工具鲁棒性
        return items

    def _save_all(self, items: list) -> None:
        path = self._memory_file()
        with open(path, "w", encoding="utf-8") as f:
            for it in items:
                f.write(json.dumps(it, ensure_ascii=False) + "\n")

    # ------------------------------------------------------------------ 工具方法
    async def save_memory(
        self,
        content: str,
        tag: str = "general",
        __event_emitter__=None,
        __user__: Optional[dict] = None,
    ) -> str:
        """保存一条重要信息到长期记忆（用户偏好、背景、约定等）。

        :param content: 要记住的内容，如「我在准备信息学奥赛，主攻 C++」
        :param tag: 分类标签，如 preference / project / study / general
        :return: 保存结果确认
        """
        content = (content or "").strip()
        if not content:
            return "❌ 记忆内容不能为空。"
        tag = (tag or "general").strip() or "general"

        item = {
            "id": f"mem_{int(time.time() * 1000)}",   # 毫秒时间戳 ID，保证唯一
            "content": content,
            "tag": tag,
            "saved_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        items = self._load_all()
        items.append(item)
        self._save_all(items)
        return f"🧠 已记住（标签：{tag}）：{content}\n当前共 {len(items)} 条记忆。"

    async def recall_memory(
        self,
        query: str,
        limit: int = 5,
        __event_emitter__=None,
        __user__: Optional[dict] = None,
    ) -> str:
        """按关键词回忆相关记忆（回答用户问题前先调用，获取背景信息）。

        :param query: 关键词，如「C++」「平板」「偏好」
        :param limit: 最多返回几条记忆
        :return: 相关记忆列表（按相关度排序）
        """
        items = self._load_all()
        if not items:
            return "🧠 记忆库为空。可以告诉我你的偏好和背景，我会用记忆工具保存下来。"

        query = (query or "").strip()
        if not query:
            return "❌ 请提供回忆关键词。"

        # 简单关键词匹配打分：内容中每出现一次关键词得 1 分，标签命中额外加分
        keywords = [query] + [w for w in query.replace("，", " ").split() if len(w) >= 2]
        scored = []
        for it in items:
            score = 0
            text = it.get("content", "")
            for kw in keywords:
                if kw and kw in text:
                    score += text.count(kw)
            if query in it.get("tag", ""):
                score += 2
            if score > 0:
                scored.append((score, it))

        if not scored:
            return f"🧠 没有找到与「{query}」相关的记忆。可以直接告诉我你的偏好，我会记住。"

        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[: max(1, limit)]
        lines = [f"🧠 与「{query}」相关的记忆（共 {len(scored)} 条，展示前 {len(top)} 条）："]
        for _, it in top:
            lines.append(f"  · [{it.get('tag', 'general')}] {it['content']}（{it.get('saved_at', '')}）")
        return "\n".join(lines)

    async def list_memories(
        self,
        tag: str = "",
        __event_emitter__=None,
        __user__: Optional[dict] = None,
    ) -> str:
        """列出全部长期记忆（可按标签过滤）。

        :param tag: 可选，只列出某个标签的记忆，如 preference
        """
        items = self._load_all()
        if not items:
            return "🧠 记忆库为空。"
        if tag:
            items = [it for it in items if tag.strip().lower() in it.get("tag", "").lower()]
            if not items:
                return f"🧠 没有标签为「{tag}」的记忆。"
        lines = [f"🧠 长期记忆列表（共 {len(items)} 条）："]
        for it in items:
            lines.append(f"  · [{it.get('tag', 'general')}] {it['content']}（{it.get('saved_at', '')}，ID: {it['id']}）")
        return "\n".join(lines)

    async def forget_memory(
        self,
        memory_id: str,
        __event_emitter__=None,
        __user__: Optional[dict] = None,
    ) -> str:
        """删除一条长期记忆。

        :param memory_id: 记忆 ID（列表 Memory 时展示，如 mem_1710000000000）
        """
        memory_id = (memory_id or "").strip()
        if not memory_id:
            return "❌ 请提供要删除的记忆 ID。"
        items = self._load_all()
        new_items = [it for it in items if it.get("id") != memory_id]
        if len(new_items) == len(items):
            return f"❌ 找不到 ID 为 {memory_id} 的记忆。可先「列出全部记忆」查看 ID。"
        self._save_all(new_items)
        return f"🗑️ 已删除记忆 {memory_id}，剩余 {len(new_items)} 条。"
