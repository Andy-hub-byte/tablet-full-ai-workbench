# title: 代码运行工具 Code Runner
# author: tablet-full-ai-workbench
# author_url: https://github.com/Andy-hub-byte/tablet-full-ai-workbench
# description: 在平板本地编译并运行 C++/Python/JavaScript/Shell 代码，返回标准输出、标准错误与退出码，让 AI 可以直接帮你编写和调试代码。
# version: 0.1.0

"""
代码运行工具（Open WebUI Tool）
================================

让 AI 可以直接在平板上编译并运行代码，特别适合学习 C++：

* cpp       ：调用 g++ 以 C++17 标准编译后运行
* python    ：调用 python3 运行
* javascript：调用 node 运行（需系统已安装 Node.js）
* shell     ：调用 /bin/sh 运行

安装方式：Open WebUI → 管理员面板 → 工作区 → 工具 → 新建工具 → 粘贴本文件内容。
（部署脚本 import-tools.py 会自动完成导入，无需手动操作。）

安全说明：代码以 Open WebUI 服务相同的权限在本地执行，属于本机单用户工具，
请勿将服务端口暴露到不可信的网络。
"""

import asyncio
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class Tools:
    """Open WebUI 工具入口类：提供 run_code 工具方法。"""

    class Valves(BaseModel):
        """管理员级配置（在 Open WebUI 工具设置中调整）。"""

        timeout_seconds: int = Field(
            default=30,
            description="单次运行超时时间（秒）。防止死循环把工作台卡死。",
        )
        max_output_chars: int = Field(
            default=4000,
            description="stdout/stderr 各自的最大返回字符数，超出部分截断，防止刷屏。",
        )
        cpp_compiler: str = Field(default="g++", description="C++ 编译器命令（部署脚本已在容器内安装 g++）")
        python_bin: str = Field(default="python3", description="Python 解释器命令")
        node_bin: str = Field(default="node", description="Node.js 命令")
        work_dir: str = Field(
            default="/tmp/workbench_run",
            description="代码运行的临时工作目录。每次运行使用独立子目录，结束自动清理。",
        )

    class UserValves(BaseModel):
        """用户级配置（每个用户可以单独设置）。"""

        show_exit_code: bool = Field(default=True, description="是否在结果中展示退出码")

    def __init__(self):
        """工具初始化（无状态，配置通过 Valves 注入）。"""
        pass

    # ------------------------------------------------------------------ 工具入口
    async def run_code(
        self,
        language: str,
        code: str,
        __event_emitter__=None,
        __user__: Optional[dict] = None,
    ) -> str:
        """编译并运行一段代码，返回运行结果（AI 通过调用此方法来运行代码）。

        :param language: 代码语言，支持 cpp / python / javascript / shell
        :param code: 需要运行的源代码全文
        :return: 包含运行状态、耗时、退出码、标准输出与标准错误的文本
        """
        # 统一语言别名，方便模型用各种常见写法调用
        aliases = {
            "c++": "cpp", "cpp": "cpp", "c": "cpp",
            "python": "python", "python3": "python", "py": "python",
            "javascript": "javascript", "js": "javascript", "node": "javascript",
            "shell": "shell", "bash": "shell", "sh": "shell",
        }
        language = aliases.get((language or "").strip().lower())
        if language is None:
            return "❌ 不支持的语言。目前仅支持：cpp（C++）、python、javascript、shell。"

        code = (code or "").strip()
        if not code:
            return "❌ 代码内容为空，请先提供需要运行的源代码。"

        await self._emit(__event_emitter__, f"⚙️ 正在准备运行 {language} 代码…")

        # 每个任务使用独立临时目录，运行结束自动清理，避免文件互相覆盖
        base = Path(self.valves.work_dir)
        base.mkdir(parents=True, exist_ok=True)
        workdir = Path(tempfile.mkdtemp(prefix="run_", dir=base))
        try:
            return await self._execute(language, code, workdir, __event_emitter__)
        finally:
            shutil.rmtree(workdir, ignore_errors=True)

    # ------------------------------------------------------------------ 内部实现
    async def _emit(self, emitter, description: str):
        """向 Open WebUI 推送运行状态（显示在对话气泡的状态行）。推送失败不影响主流程。"""
        if emitter is None:
            return
        try:
            await emitter({
                "type": "status",
                "data": {"description": description, "done": False},
            })
        except Exception:
            pass

    async def _run_process(self, cmd, cwd, timeout):
        """异步执行子进程并捕获输出，带超时保护。

        :return: (stdout, stderr, returncode)；超时返回 (None, None, None)
        """
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(cwd),
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return None, None, None
        return (
            stdout.decode("utf-8", errors="replace"),
            stderr.decode("utf-8", errors="replace"),
            proc.returncode,
        )

    def _truncate(self, text: str) -> str:
        """按配置截断过长输出，并给出截断提示。"""
        limit = self.valves.max_output_chars
        if text and len(text) > limit:
            return text[:limit] + f"\n……（输出过长，已截断，仅显示前 {limit} 字符）"
        return text or ""

    def _format_result(self, language, stdout, stderr, returncode, elapsed, compile_error=None):
        """把运行结果格式化为易读的文本，方便用户和 AI 阅读。"""
        lines = [f"▶️ 代码运行结果（语言：{language}，耗时 {elapsed:.2f}s）"]
        if returncode == 0:
            lines.append("状态：✅ 运行成功")
        else:
            lines.append(f"状态：❌ 异常退出（退出码 {returncode}）")

        if compile_error is not None:
            # 编译失败：把编译器原始报错完整展示，方便排查语法错误
            lines.append("\n【编译错误】")
            lines.append(self._truncate(compile_error) or "（编译器未输出具体错误信息）")
        else:
            lines.append("\n【标准输出 stdout】")
            lines.append(self._truncate(stdout) or "（无输出）")
            lines.append("\n【标准错误 stderr】")
            lines.append(self._truncate(stderr) or "（无输出）")
        return "\n".join(lines)

    async def _execute(self, language: str, code: str, workdir: Path, emitter) -> str:
        """按语言编译/运行代码，并格式化返回结果。"""
        timeout = self.valves.timeout_seconds
        started = time.monotonic()

        # ---------- C++：先编译，编译失败直接返回错误；成功后运行 ----------
        if language == "cpp":
            src = workdir / "main.cpp"
            exe = workdir / "main"
            src.write_text(code, encoding="utf-8")

            await self._emit(emitter, "🔨 正在使用 g++ 编译 C++ 代码…")
            _, compile_err, rc = await self._run_process(
                [self.valves.cpp_compiler, "-O2", "-std=c++17", "-o", str(exe), str(src)],
                workdir, timeout,
            )
            if rc is None:
                return f"⏰ 编译超时（超过 {timeout} 秒），已强制结束。"
            if rc != 0:
                elapsed = time.monotonic() - started
                return self._format_result(language, None, None, rc, elapsed, compile_error=compile_err)

            await self._emit(emitter, "▶️ 编译成功，正在运行程序…")
            out, err, rc = await self._run_process([str(exe)], workdir, timeout)

        # ---------- Python ----------
        elif language == "python":
            src = workdir / "main.py"
            src.write_text(code, encoding="utf-8")
            await self._emit(emitter, "▶️ 正在运行 Python 代码…")
            out, err, rc = await self._run_process([self.valves.python_bin, str(src)], workdir, timeout)

        # ---------- JavaScript ----------
        elif language == "javascript":
            src = workdir / "main.js"
            src.write_text(code, encoding="utf-8")
            await self._emit(emitter, "▶️ 正在运行 JavaScript 代码…")
            out, err, rc = await self._run_process([self.valves.node_bin, str(src)], workdir, timeout)

        # ---------- Shell ----------
        else:
            src = workdir / "main.sh"
            src.write_text(code, encoding="utf-8")
            await self._emit(emitter, "▶️ 正在运行 Shell 脚本…")
            out, err, rc = await self._run_process(["/bin/sh", str(src)], workdir, timeout)

        # ---------- 统一处理运行结果 ----------
        if rc is None:
            return (
                f"⏰ 运行超时（超过 {timeout} 秒），已强制结束。\n"
                "可能原因：死循环、等待输入（本工具不支持交互输入）、阻塞操作。"
            )
        elapsed = time.monotonic() - started
        return self._format_result(language, out, err, rc, elapsed)
