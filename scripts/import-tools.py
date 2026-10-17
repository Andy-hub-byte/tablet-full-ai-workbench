#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量导入 Open WebUI Agent 工具脚本
==================================

功能：把 webui/tools/ 目录下的 5 个 Python 工具，通过 Open WebUI REST API
自动创建并激活，免去在网页里逐个粘贴的麻烦。

用法（在 proot 容器内、Open WebUI 已启动时执行）：
    cd /root/workbench
    . .venv/bin/activate
    python scripts/import-tools.py

参数：
    --base-url   Open WebUI 地址，默认 http://127.0.0.1:8080
    --email      管理员账号，默认 admin@workbench.local
    --password   管理员密码，默认 workbench123

说明：
    · 首次运行会自动注册管理员账号（要求 .env 中 ENABLE_SIGNUP=True；
      若为 False，请先在网页注册第一个账号，再用同样账号密码运行本脚本）
    · 导入只是自动化手段，失败可完全手动导入：
      Open WebUI → 管理员面板 → 工作区 → 工具 → 新建工具 → 粘贴代码
"""

import argparse
import glob
import os
import sys
import uuid

try:
    import requests
except ImportError:
    sys.exit("缺少 requests 库，请先在虚拟环境中执行：pip install requests")

# 工具目录：本项目 webui/tools/
TOOLS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "webui", "tools"
)


def parse_meta(content: str) -> dict:
    """从 Python 文件头部注释中解析元信息（title / description / author / version）。"""
    meta = {}
    for line in content.splitlines()[:40]:
        s = line.strip().lstrip("#").strip()
        for key in ("title", "description", "author", "version"):
            if s.startswith(key + ":") and key not in meta:
                meta[key] = s.split(":", 1)[1].strip()
    return meta


def get_token(base_url: str, email: str, password: str) -> str:
    """登录 Open WebUI 获取 Token；账号不存在时自动注册（首个账号即管理员）。"""
    # 先尝试登录
    try:
        resp = requests.post(
            f"{base_url}/api/v1/auths/signin",
            json={"email": email, "password": password},
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            token = data.get("token") or data.get("id_token") or data.get("access_token")
            if token:
                print(f"  ✓ 已登录：{email}")
                return token
    except requests.RequestException as e:
        sys.exit(f"无法连接 Open WebUI（{base_url}）：{e}")

    # 登录失败：尝试注册新账号
    resp = requests.post(
        f"{base_url}/api/v1/auths/signup",
        json={"email": email, "password": password, "name": "工作台管理员"},
        timeout=15,
    )
    if resp.status_code == 200:
        data = resp.json()
        token = data.get("token") or data.get("id_token") or data.get("access_token")
        if token:
            print(f"  ✓ 已注册管理员账号：{email}")
            return token

    sys.exit(
        "登录/注册失败。\n"
        f"  · 如已关闭注册（ENABLE_SIGNUP=False），请先在浏览器注册第一个账号，\n"
        f"    然后用该账号密码重跑：python scripts/import-tools.py --email 你的邮箱 --password 你的密码\n"
        f"  · 服务端返回：{resp.status_code} {resp.text[:200]}"
    )


def import_tool(base_url: str, headers: dict, path: str) -> bool:
    """导入单个工具文件：创建函数 + 激活。"""
    with open(path, encoding="utf-8") as f:
        content = f.read()

    meta = parse_meta(content)
    name = meta.get("title") or os.path.basename(path)
    function_id = str(uuid.uuid4())

    payload = {
        "id": function_id,
        "name": name,
        "content": content,
        "meta": {
            "description": meta.get("description", ""),
            "author": meta.get("author", ""),
            "version": meta.get("version", "0.1.0"),
        },
    }
    resp = requests.post(
        f"{base_url}/api/v1/functions/create", json=payload, headers=headers, timeout=30
    )
    if resp.status_code not in (200, 201):
        print(f"  ✗ 导入失败：{name} -> {resp.status_code} {resp.text[:150]}")
        return False

    # 激活工具（部分版本无此端点，失败不影响导入结果）
    try:
        requests.post(
            f"{base_url}/api/v1/functions/id/{function_id}/activate",
            headers=headers,
            timeout=15,
        )
    except requests.RequestException:
        pass

    print(f"  ✓ 已导入并激活：{name}")
    return True


def main():
    parser = argparse.ArgumentParser(description="批量导入 Open WebUI Agent 工具")
    parser.add_argument("--base-url", default=os.environ.get("OWUI_BASE_URL", "http://127.0.0.1:8080"))
    parser.add_argument("--email", default=os.environ.get("OWUI_ADMIN_EMAIL", "admin@workbench.local"))
    parser.add_argument("--password", default=os.environ.get("OWUI_ADMIN_PASSWORD", "workbench123"))
    args = parser.parse_args()

    tool_files = sorted(glob.glob(os.path.join(TOOLS_DIR, "*.py")))
    if not tool_files:
        sys.exit(f"未找到工具文件：{TOOLS_DIR}")

    print(f"准备导入 {len(tool_files)} 个 Agent 工具到 {args.base_url} ……")
    token = get_token(args.base_url, args.email, args.password)
    headers = {"Authorization": f"Bearer {token}"}

    ok, fail = 0, 0
    for path in tool_files:
        if import_tool(args.base_url, headers, path):
            ok += 1
        else:
            fail += 1

    print(f"\n导入完成：成功 {ok} 个，失败 {fail} 个")
    if fail:
        print("失败的工具可手动导入：Open WebUI → 管理员面板 → 工作区 → 工具 → 新建工具 → 粘贴代码")
    print("提示：在对话界面点击「集成」图标，勾选需要启用的工具后即可使用。")


if __name__ == "__main__":
    main()
