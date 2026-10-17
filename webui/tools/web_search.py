# title: 联网搜索工具 Web Search
# author: tablet-full-ai-workbench
# author_url: https://github.com/Andy-hub-byte/tablet-full-ai-workbench
# description: 通过 DuckDuckGo 搜索公开网页，获取最新信息（无需 API Key，本地直连），让本地 AI 也能回答时效性问题。
# version: 0.1.0

"""
联网搜索工具（Open WebUI Tool）
================================

核心能力：联网搜索。

* web_search：输入关键词，返回网页标题、链接和摘要

实现说明：
* 使用 DuckDuckGo HTML 端点（https://html.duckduckgo.com/html/），无需 API Key
* 仅用 Python 标准库解析结果，无第三方依赖
* 需要设备能访问互联网；如失败可换用 Open WebUI 内置的搜索功能
  （管理员面板 → 设置 → 网页搜索，支持 SearXNG 等）
"""

import asyncio
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from typing import Optional

from pydantic import BaseModel, Field


class _DuckDuckGoParser(HTMLParser):
    """解析 DuckDuckGo HTML 结果页，提取搜索结果（标题 + 链接 + 摘要）。"""

    def __init__(self):
        super().__init__()
        self.results = []       # 已完成的搜索结果列表
        self._cur = None        # 正在收集的结果
        self._buf = []          # 文本缓冲

    def handle_starttag(self, tag, attrs):
        attr = dict(attrs)
        cls = attr.get("class", "") or ""
        # 每条结果以一个 result__a 链接开始
        if tag == "a" and "result__a" in cls:
            self._flush()
            self._cur = {"title": "", "url": attr.get("href", "")}
            self._buf = []
        # result__snippet 是同一结果内的摘要节点
        elif tag == "a" and "result__snippet" in cls and self._cur is not None:
            self._buf = []

    def handle_endtag(self, tag):
        # </a> 结束时把缓冲区文本写入当前结果对应字段
        if tag == "a" and self._cur is not None:
            text = "".join(self._buf).strip()
            if "result__a" in (getattr(self, "_last_cls", "") or ""):
                self._cur["title"] = text
            elif self._cur.get("title") and not self._cur.get("snippet"):
                self._cur["snippet"] = text
            self._buf = []

    def handle_data(self, data):
        if self._cur is not None:
            self._buf.append(data)

    def _flush(self):
        if self._cur and self._cur.get("title"):
            self.results.append(self._cur)
        self._cur = None

    def close(self):
        super().close()
        self._flush()


class Tools:
    """Open WebUI 工具入口类：提供联网搜索工具方法。"""

    class Valves(BaseModel):
        """管理员级配置。"""

        max_results: int = Field(default=5, description="每次搜索最多返回的结果条数")
        timeout_seconds: int = Field(default=15, description="搜索请求超时时间（秒）")

    class UserValves(BaseModel):
        """用户级配置。"""

        show_url: bool = Field(default=True, description="是否在结果中展示网页链接")

    def __init__(self):
        pass

    async def web_search(
        self,
        query: str,
        max_results: int = 5,
        __event_emitter__=None,
        __user__: Optional[dict] = None,
    ) -> str:
        """搜索互联网获取最新信息（回答时效性问题前先调用）。

        :param query: 搜索关键词，如「Qwen3 发布日期」
        :param max_results: 返回结果条数（1~10）
        :return: 搜索结果列表（标题、摘要、链接）
        """
        query = (query or "").strip()
        if not query:
            return "❌ 请提供搜索关键词。"

        count = min(max(1, max_results or self.valves.max_results), 10)

        # DuckDuckGo HTML 搜索是同步阻塞 IO，放到线程池执行，避免卡住事件循环
        try:
            results = await asyncio.to_thread(self._search, query, count)
        except Exception as e:
            return (
                f"❌ 搜索失败：{e}\n"
                "可能原因：设备未联网、DuckDuckGo 暂时不可用、请求被限流。\n"
                "建议：稍后重试，或在管理员面板配置 Open WebUI 内置搜索功能。"
            )

        if not results:
            return f"🔍 没有找到与「{query}」相关的结果，请尝试更换关键词。"

        lines = [f"🔍 「{query}」的搜索结果（共 {len(results)} 条）："]
        for i, r in enumerate(results, 1):
            lines.append(f"\n{i}. {r['title']}")
            if r.get("snippet"):
                lines.append(f"   {r['snippet']}")
            if self.UserValves().show_url and r.get("url"):
                lines.append(f"   链接：{r['url']}")
        lines.append("\n（以上为搜索摘要，回答时请核实关键信息，不要直接照搬。）")
        return "\n".join(lines)

    def _search(self, query: str, count: int) -> list:
        """同步执行 DuckDuckGo HTML 搜索并解析结果（运行在工作线程中）。"""
        url = "https://html.duckduckgo.com/html/?" + urllib.parse.urlencode({"q": query})
        req = urllib.request.Request(
            url,
            headers={
                # 伪装常规浏览器 User-Agent，避免被拒绝
                "User-Agent": "Mozilla/5.0 (Linux; Android 13; Tablet) AppleWebKit/537.36 "
                              "(KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36",
            },
        )
        with urllib.request.urlopen(req, timeout=self.valves.timeout_seconds) as resp:
            html = resp.read().decode("utf-8", errors="replace")

        parser = _DuckDuckGoParser()
        try:
            parser.feed(html)
        finally:
            parser.close()
        return parser.results[:count]
