#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码工作台 Code Studio · 后端服务
================================

仅使用 Python 标准库实现，无需安装任何第三方依赖。

功能：
  GET  /              代码编辑器页面
  GET  /static/*      静态资源
  POST /api/run       运行代码（C++/Python/JavaScript/Shell），返回输出
  POST /api/ai        AI 生成 / 解释 / 修复代码（转发到 Open WebUI）
  GET  /api/models    获取 Ollama 已安装模型列表
  GET  /preview/*     HTML 代码的实时预览页面

配置（环境变量）：
  EDITOR_HOST   监听地址，默认 127.0.0.1（仅本机；改 0.0.0.0 开放局域网）
  EDITOR_PORT   监听端口，默认 8899
  OWUI_BASE_URL Open WebUI 地址，默认 http://127.0.0.1:8080
  OWUI_TOKEN    Open WebUI API Key（AI 功能需要，见 .env 配置）

安全说明：本服务会在本地编译并执行用户提交的代码，属于单用户本地工具，
默认仅监听 127.0.0.1；如需开放局域网请自行评估风险。
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

# ---------------------------------------------------------------------------
# 路径与常量
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent            # editor/ 目录
PROJECT_DIR = BASE_DIR.parent                          # 项目根目录
STATIC_DIR = BASE_DIR / "static"                       # 前端静态文件
PREVIEW_DIR = PROJECT_DIR / ".runtime" / "previews"    # HTML 预览文件
CONFIG_PATH = PROJECT_DIR / "agent" / "config.json"    # Agent 配置（AI 提示词等）

INDEX_HTML = "index.html"

# 各语言的源码文件名与运行方式
LANGUAGES = {
    "cpp":        {"file": "main.cpp", "runner": "compiler"},
    "python":     {"file": "main.py",  "runner": "python"},
    "javascript": {"file": "main.js",  "runner": "node"},
    "shell":      {"file": "main.sh",  "runner": "shell"},
    "html":       {"file": "index.html", "runner": "html"},
}

# 用户在前端选择的语言名 -> 内部语言键
LANGUAGE_ALIASES = {
    "cpp": "cpp", "c++": "cpp", "c": "cpp",
    "python": "python", "py": "python", "python3": "python",
    "javascript": "javascript", "js": "javascript", "node": "javascript",
    "shell": "shell", "bash": "shell", "sh": "shell",
    "html": "html",
}

RUN_TIMEOUT = 30  # 代码运行超时（秒）


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------
def load_config() -> dict:
    """读取 agent/config.json，失败时返回内置默认配置。"""
    default = {
        "agent": {"default_model": "qwen:1.8b"},
        "ai_actions": {
            "generate": {
                "system": "你是一名经验丰富的程序员，擅长编写规范、易读、带详细中文注释的教学级代码。",
                "user_template": "请根据需求编写完整的{language}代码，只输出代码本身：\n\n{prompt}",
            },
            "explain": {
                "system": "你是一名耐心的编程老师，擅长用通俗易懂的中文讲解代码。",
                "user_template": "请详细解释下面这段{language}代码：\n\n```\n{code}\n```",
            },
            "fix": {
                "system": "你是一名严谨的代码审查专家，擅长定位 bug。",
                "user_template": "请找出下面这段{language}代码的问题并给出修复版本：\n\n```\n{code}\n```",
            },
        },
    }
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            cfg = json.load(f)
        # 与默认配置合并，保证缺字段时也能工作
        default["agent"].update(cfg.get("agent", {}))
        default["ai_actions"].update(cfg.get("ai_actions", {}))
        return default
    except (OSError, ValueError):
        return default


def run_code(language: str, code: str, stdin_text: str = "") -> dict:
    """在独立临时目录中编译/运行代码，返回结果字典。

    :param language: 内部语言键（cpp/python/javascript/shell/html）
    :param code: 源代码
    :param stdin_text: 可选的标准输入
    :return: {"ok", "stdout", "stderr", "exit_code", "duration_ms", "compile_error", "preview_url"}
    """
    lang = LANGUAGES.get(language)
    if lang is None:
        return {"ok": False, "error": f"不支持的语言：{language}"}

    started = time.monotonic()

    # HTML 语言：保存为预览文件，返回访问地址（不执行）
    if lang["runner"] == "html":
        PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
        name = f"preview_{int(time.time() * 1000)}.html"
        (PREVIEW_DIR / name).write_text(code, encoding="utf-8")
        return {
            "ok": True,
            "stdout": "HTML 页面已生成",
            "stderr": "",
            "exit_code": 0,
            "duration_ms": int((time.monotonic() - started) * 1000),
            "compile_error": None,
            "preview_url": f"/preview/{name}",
        }

    # 其他语言：在临时目录中执行
    with tempfile.TemporaryDirectory(prefix="code_studio_") as tmp:
        src = Path(tmp) / lang["file"]
        src.write_text(code, encoding="utf-8")

        # ---------- 构建执行命令 ----------
        if lang["runner"] == "compiler":
            # C++：先用 g++ 编译，编译失败直接返回编译错误
            exe = Path(tmp) / "main"
            compile_proc = subprocess.run(
                ["g++", "-O2", "-std=c++17", "-o", str(exe), str(src)],
                capture_output=True, text=True, timeout=RUN_TIMEOUT,
            )
            if compile_proc.returncode != 0:
                return {
                    "ok": False,
                    "stdout": "",
                    "stderr": "",
                    "exit_code": compile_proc.returncode,
                    "duration_ms": int((time.monotonic() - started) * 1000),
                    "compile_error": compile_proc.stderr,
                    "error": "编译失败",
                }
            cmd = [str(exe)]
        elif lang["runner"] == "python":
            cmd = ["python3", str(src)]
        elif lang["runner"] == "node":
            cmd = ["node", str(src)]
        else:  # shell
            cmd = ["/bin/sh", str(src)]

        # ---------- 执行 ----------
        try:
            proc = subprocess.run(
                cmd, input=stdin_text, capture_output=True, text=True,
                timeout=RUN_TIMEOUT, cwd=tmp,
            )
        except subprocess.TimeoutExpired:
            return {
                "ok": False, "stdout": "", "stderr": "",
                "exit_code": None,
                "duration_ms": RUN_TIMEOUT * 1000,
                "error": f"运行超时（{RUN_TIMEOUT} 秒），已强制结束。请检查死循环或阻塞输入。",
            }
        except FileNotFoundError as e:
            return {"ok": False, "error": f"找不到执行程序：{e}（请确认已安装对应运行时）"}

        return {
            "ok": proc.returncode == 0,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "exit_code": proc.returncode,
            "duration_ms": int((time.monotonic() - started) * 1000),
            "compile_error": None,
        }


def call_openwebui_ai(action: str, language: str, code: str, prompt: str, model: str) -> dict:
    """调用 Open WebUI 的 OpenAI 兼容接口，让 AI 生成/解释/修复代码。"""
    config = load_config()
    action_cfg = config["ai_actions"].get(action)
    if action_cfg is None:
        return {"ok": False, "error": f"未知的 AI 动作：{action}"}

    # 用配置里的提示词模板填充用户输入
    user_content = action_cfg.get("user_template", "{code}").format(
        language=language, code=code, prompt=prompt
    )
    model_name = model or config["agent"].get("default_model", "qwen:1.8b")

    base_url = os.environ.get("OWUI_BASE_URL", "http://127.0.0.1:8080").rstrip("/")
    token = os.environ.get("OWUI_TOKEN", "").strip()

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": action_cfg.get("system", "")},
            {"role": "user", "content": user_content},
        ],
        "stream": False,
        "temperature": 0.3,
    }
    req = urllib.request.Request(
        f"{base_url}/api/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            **({"Authorization": f"Bearer {token}"} if token else {}),
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"]
        return {"ok": True, "content": content, "model": model_name}
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = e.read().decode("utf-8", errors="replace")[:200]
        except Exception:
            pass
        return {
            "ok": False,
            "error": f"Open WebUI 返回错误 {e.code}：{detail}\n"
                     "请确认：1) Open WebUI 正在运行；2) 模型已下载；3) 如开启了认证，请在 .env 配置 OWUI_TOKEN。",
        }
    except urllib.error.URLError as e:
        return {"ok": False, "error": f"无法连接 Open WebUI（{base_url}）：{e.reason}\n请确认 Open WebUI 已启动。"}


def get_ollama_models() -> list:
    """从 Ollama API 获取已安装模型列表。"""
    url = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/") + "/api/tags"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return [m.get("name", "") for m in data.get("models", []) if m.get("name")]
    except (urllib.error.URLError, OSError, ValueError):
        return []


def extract_code(text: str) -> str:
    """从 AI 返回的文本中提取代码块内容（去掉 ``` 围栏）。"""
    # 优先提取第一个代码块
    m = re.search(r"```(?:\w+)?\s*\n(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return text.strip()


# ---------------------------------------------------------------------------
# HTTP 请求处理器
# ---------------------------------------------------------------------------
class CodeStudioHandler(BaseHTTPRequestHandler):
    """处理浏览器请求：静态页面 + API。"""

    server_version = "CodeStudio/1.0"

    # ---------- 工具方法 ----------
    def _send_json(self, obj: dict, status: int = 200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: Path, content_type: str):
        if not path.is_file():
            self._send_json({"error": "文件不存在"}, status=404)
            return
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> dict:
        """读取并解析 POST 的 JSON 请求体。"""
        length = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(length) if length > 0 else b""
        try:
            return json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return {}

    def log_message(self, fmt, *args):  # noqa: N802（父类方法名）
        """简化访问日志，避免刷屏。"""
        sys.stderr.write("[CodeStudio] %s - %s\n" % (self.address_string(), fmt % args))

    # ---------- GET 请求 ----------
    def do_GET(self):  # noqa: N802
        path = urlparse(self.path).path

        # 首页
        if path in ("/", f"/{INDEX_HTML}"):
            self._send_file(STATIC_DIR / INDEX_HTML, "text/html; charset=utf-8")
            return

        # 静态资源（带路径穿越防护）
        if path.startswith("/static/"):
            rel = path[len("/static/"):]
            target = (STATIC_DIR / rel).resolve()
            # 解析后的路径必须仍在 STATIC_DIR 内，防止 ../ 穿越
            if not str(target).startswith(str(STATIC_DIR.resolve())):
                self._send_json({"error": "非法路径"}, status=403)
                return
            ctype = {
                ".css": "text/css; charset=utf-8",
                ".js": "application/javascript; charset=utf-8",
                ".png": "image/png", ".jpg": "image/jpeg",
                ".svg": "image/svg+xml", ".ico": "image/x-icon",
            }.get(target.suffix.lower(), "application/octet-stream")
            self._send_file(target, ctype)
            return

        # HTML 预览页面
        if path.startswith("/preview/"):
            name = os.path.basename(path[len("/preview/"):])
            # 仅允许字母数字、点、短横线、下划线，防止路径穿越
            if not re.fullmatch(r"[\w.-]+", name):
                self._send_json({"error": "非法文件名"}, status=403)
                return
            self._send_file(PREVIEW_DIR / name, "text/html; charset=utf-8")
            return

        # API：模型列表
        if path == "/api/models":
            models = get_ollama_models()
            default_model = load_config()["agent"].get("default_model", "qwen:1.8b")
            # 默认模型不一定在已安装列表里，补到最前面
            if default_model and default_model not in models:
                models.insert(0, default_model)
            self._send_json({"ok": True, "models": models})
            return

        self._send_json({"error": "接口不存在"}, status=404)

    # ---------- POST 请求 ----------
    def do_POST(self):  # noqa: N802
        path = urlparse(self.path).path
        body = self._read_json_body()

        # API：运行代码
        if path == "/api/run":
            language = LANGUAGE_ALIASES.get(str(body.get("language", "")).strip().lower())
            if language is None:
                self._send_json({"ok": False, "error": "不支持的语言"}, status=400)
                return
            result = run_code(language, str(body.get("code", "")), str(body.get("stdin", "")))
            self._send_json(result)
            return

        # API：AI 生成 / 解释 / 修复
        if path == "/api/ai":
            action = str(body.get("action", "")).strip().lower()
            if action not in ("generate", "explain", "fix"):
                self._send_json({"ok": False, "error": "未知的 AI 动作"}, status=400)
                return
            result = call_openwebui_ai(
                action=action,
                language=str(body.get("language", "C++")),
                code=str(body.get("code", "")),
                prompt=str(body.get("prompt", "")),
                model=str(body.get("model", "")),
            )
            # AI 生成的代码：提取代码块部分，方便直接填入编辑器
            if result.get("ok"):
                result["code"] = extract_code(result["content"])
            self._send_json(result)
            return

        self._send_json({"error": "接口不存在"}, status=404)


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="代码工作台 Code Studio 服务")
    parser.add_argument("--host", default=os.environ.get("EDITOR_HOST", "127.0.0.1"),
                        help="监听地址，默认 127.0.0.1")
    parser.add_argument("--port", type=int, default=int(os.environ.get("EDITOR_PORT", "8899")),
                        help="监听端口，默认 8899")
    args = parser.parse_args()

    # 启动时确保预览目录存在
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)

    server = ThreadingHTTPServer((args.host, args.port), CodeStudioHandler)
    print("=" * 56)
    print(" 代码工作台 Code Studio 已启动")
    print(f" 本机访问   : http://127.0.0.1:{args.port}")
    print(f" 配置文件   : {CONFIG_PATH}")
    print(f" AI 接口    : {os.environ.get('OWUI_BASE_URL', 'http://127.0.0.1:8080')}")
    print(" 按 Ctrl+C 停止服务")
    print("=" * 56)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n正在停止服务……")
        server.shutdown()


if __name__ == "__main__":
    main()
