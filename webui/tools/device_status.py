# title: 设备状态工具 Device Status
# author: tablet-full-ai-workbench
# author_url: https://github.com/Andy-hub-byte/tablet-full-ai-workbench
# description: 查看平板的实时运行状态：内存、存储、CPU 核心数以及 Ollama 已安装的模型列表，方便 AI 根据设备情况给出建议。
# version: 0.1.0

"""
设备状态工具（Open WebUI Tool）
================================

核心能力：了解平板当前状态。

* device_status：一次性查看内存 / 存储 / CPU / 模型列表

典型用途：
* 「现在内存还剩多少？能跑 7B 模型吗？」
* 「平板上都装了哪些模型？」
* AI 在推荐模型前，先了解设备实际情况，避免推荐跑不动的模型
"""

import shutil
import urllib.request
from typing import Optional

from pydantic import BaseModel, Field


class Tools:
    """Open WebUI 工具入口类：提供设备状态查询工具方法。"""

    class Valves(BaseModel):
        """管理员级配置。"""

        ollama_base_url: str = Field(
            default="http://127.0.0.1:11434",
            description="Ollama API 地址（Termux 原生服务）",
        )

    class UserValves(BaseModel):
        """用户级配置。"""

        show_cpu_detail: bool = Field(default=False, description="是否展示每个 CPU 核心的频率")

    def __init__(self):
        pass

    async def device_status(
        self,
        __event_emitter__=None,
        __user__: Optional[dict] = None,
    ) -> str:
        """查看平板当前运行状态：内存、存储、CPU 与已安装模型。"""
        lines = ["📊 平板设备状态："]

        # ---------- 内存（/proc/meminfo 与容器共享内核，读数准确） ----------
        mem_total, mem_avail = self._read_memory()
        if mem_total:
            used = mem_total - mem_avail
            lines.append(
                f"  · 内存：已用 {used / 1024:.1f}GB / 共 {mem_total / 1024:.1f}GB"
                f"（可用 {mem_avail / 1024:.1f}GB）"
            )

        # ---------- 存储 ----------
        try:
            usage = shutil.disk_usage("/")
            lines.append(
                f"  · 存储：已用 {usage.used / 1024**3:.1f}GB / 共 {usage.total / 1024**3:.1f}GB"
                f"（剩余 {usage.free / 1024**3:.1f}GB）"
            )
        except OSError:
            pass

        # ---------- CPU ----------
        cpu = self._read_cpu()
        if cpu:
            lines.append(f"  · CPU：{cpu['count']} 核心")

        # ---------- Ollama 模型列表 ----------
        models = self._list_models()
        if models is not None:
            if models:
                lines.append(f"  · 已安装模型（{len(models)} 个）：")
                for name, size in models:
                    size_str = f"（{size / 1024**3:.1f}GB）" if size else ""
                    lines.append(f"      - {name} {size_str}")
            else:
                lines.append("  · 已安装模型：无（可用 ollama pull 下载）")

        return "\n".join(lines)

    # ------------------------------------------------------------------ 内部实现
    @staticmethod
    def _read_memory():
        """读取 /proc/meminfo，返回 (总内存KB, 可用内存KB)。"""
        try:
            info = {}
            with open("/proc/meminfo", encoding="utf-8") as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 2:
                        info[parts[0].rstrip(":")] = int(parts[1])
            return info.get("MemTotal", 0), info.get("MemAvailable", 0)
        except OSError:
            return 0, 0

    @staticmethod
    def _read_cpu():
        """统计 CPU 核心数（读取 /proc/cpuinfo）。"""
        try:
            count = 0
            with open("/proc/cpuinfo", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("processor"):
                        count += 1
            return {"count": count} if count else None
        except OSError:
            return None

    def _list_models(self):
        """调用 Ollama API 获取已安装模型列表，返回 [(name, size_bytes)]；失败返回 None。"""
        import json
        import urllib.error
        try:
            url = self.valves.ollama_base_url.rstrip("/") + "/api/tags"
            with urllib.request.urlopen(url, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return [(m.get("name", "?"), m.get("size", 0)) for m in data.get("models", [])]
        except (urllib.error.URLError, OSError, ValueError):
            return None  # Ollama 未运行时不报错，静默跳过
