# title: 任务规划工具 Task Planner
# author: tablet-full-ai-workbench
# author_url: https://github.com/Andy-hub-byte/tablet-full-ai-workbench
# description: 把复杂任务拆解为可执行的步骤清单，支持创建、查看、更新与删除计划，让 Agent 一步步完成长任务，进度一目了然。
# version: 0.1.0

"""
任务规划工具（Open WebUI Tool）
================================

核心能力：任务拆解与进度跟踪。

* create_plan ：创建任务计划（标题 + 步骤列表）
* list_plans  ：列出所有计划
* get_plan    ：查看某个计划的详细内容与进度
* update_step ：更新某个步骤的状态（待办 / 进行中 / 已完成 / 失败）
* delete_plan ：删除计划

计划数据保存在本地 JSON 文件中（默认 /root/.tablet-workbench/data/plans/），
完全本地存储，不上传任何服务器。
"""

import json
import os
import time
import uuid
from typing import Optional

from pydantic import BaseModel, Field

# 步骤状态常量
STATUS_PENDING = "pending"   # 待办
STATUS_DOING = "doing"       # 进行中
STATUS_DONE = "done"         # 已完成
STATUS_FAILED = "failed"     # 失败

# 状态 -> 展示图标（中文界面更直观）
STATUS_ICONS = {
    STATUS_PENDING: "⬜",
    STATUS_DOING: "🔵",
    STATUS_DONE: "✅",
    STATUS_FAILED: "❌",
}

# 中文状态名（AI 可以用中文或英文传入，统一映射）
STATUS_ALIASES = {
    "待办": STATUS_PENDING, "未开始": STATUS_PENDING, "pending": STATUS_PENDING, "todo": STATUS_PENDING,
    "进行中": STATUS_DOING, "doing": STATUS_DOING, "in_progress": STATUS_DOING,
    "已完成": STATUS_DONE, "完成": STATUS_DONE, "done": STATUS_DONE, "finished": STATUS_DONE,
    "失败": STATUS_FAILED, "failed": STATUS_FAILED, "error": STATUS_FAILED,
}


class Tools:
    """Open WebUI 工具入口类：提供任务规划相关工具方法。"""

    class Valves(BaseModel):
        """管理员级配置。"""

        data_dir: str = Field(
            default="/root/.tablet-workbench/data",
            description="计划数据存储目录（本地路径）",
        )

    class UserValves(BaseModel):
        """用户级配置。"""

        max_list_count: int = Field(default=10, description="列表一次最多展示的计划数量")

    def __init__(self):
        pass

    # ------------------------------------------------------------------ 数据存取
    def _plans_dir(self) -> str:
        """返回计划存储目录（不存在则创建）。"""
        d = os.path.join(self.valves.data_dir, "plans")
        os.makedirs(d, exist_ok=True)
        return d

    def _plan_path(self, plan_id: str) -> str:
        # 防御路径穿越：plan_id 只允许字母数字和短横线
        safe_id = "".join(c for c in plan_id if c.isalnum() or c == "-")
        return os.path.join(self._plans_dir(), f"{safe_id}.json")

    def _load_plan(self, plan_id: str) -> Optional[dict]:
        path = self._plan_path(plan_id)
        if not os.path.exists(path):
            return None
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def _save_plan(self, plan: dict) -> None:
        path = self._plan_path(plan["id"])
        with open(path, "w", encoding="utf-8") as f:
            json.dump(plan, f, ensure_ascii=False, indent=2)

    @staticmethod
    def _normalize_status(status: str) -> str:
        return STATUS_ALIASES.get((status or "").strip().lower(), STATUS_PENDING)

    # ------------------------------------------------------------------ 工具方法
    async def create_plan(
        self,
        title: str,
        steps: str,
        __event_emitter__=None,
        __user__: Optional[dict] = None,
    ) -> str:
        """创建一个新的任务计划（把复杂任务拆解成步骤清单）。

        :param title: 计划标题，如「用 C++ 写记事本程序」
        :param steps: 步骤内容，每一步一行，例如「1. 设计菜单界面\\n2. 实现存储结构\\n3. 编写功能代码」
        :return: 创建成功的计划详情
        """
        title = (title or "").strip()
        if not title:
            return "❌ 计划标题不能为空。"

        # 支持换行 / 分号 / 顿号分隔的多种写法，逐行解析成步骤
        raw = (steps or "").replace("；", "\n").replace(";", "\n")
        step_list = []
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            # 去掉行首的 "1." "1、" "1)" 等编号
            for sep in (".", "、", ")", "．"):
                if line[:2].endswith(sep) and line[0].isdigit():
                    line = line[2:].strip()
                    break
            if line:
                step_list.append(line)

        if not step_list:
            return "❌ 步骤内容为空。请每一步写一行，例如：\n1. 设计菜单界面\n2. 实现存储结构"

        plan = {
            "id": uuid.uuid4().hex[:8],          # 8 位短 ID，方便口头引用
            "title": title,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "steps": [
                {"index": i + 1, "content": s, "status": STATUS_PENDING}
                for i, s in enumerate(step_list)
            ],
        }
        self._save_plan(plan)
        return self._render_plan(plan) + f"\n\n💾 计划已保存（ID: {plan['id']}），之后可以说「更新计划 {plan['id']} 的第2步为已完成」。"

    async def list_plans(
        self,
        __event_emitter__=None,
        __user__: Optional[dict] = None,
    ) -> str:
        """列出所有已保存的任务计划及进度摘要。"""
        plans_dir = self._plans_dir()
        files = sorted(
            [f for f in os.listdir(plans_dir) if f.endswith(".json")],
            key=lambda f: os.path.getmtime(os.path.join(plans_dir, f)),
            reverse=True,
        )
        if not files:
            return "📋 当前没有任何任务计划。可以对我说「帮我把xxx拆解成步骤」来创建第一个计划。"

        limit = self.UserValves().max_list_count
        lines = ["📋 任务计划列表："]
        for f in files[:limit]:
            with open(os.path.join(plans_dir, f), encoding="utf-8") as fp:
                p = json.load(fp)
            done = sum(1 for s in p["steps"] if s["status"] == STATUS_DONE)
            total = len(p["steps"])
            bar = self._progress_bar(done, total)
            lines.append(f"  · [{p['id']}] {p['title']}  {bar} ({done}/{total})")
        return "\n".join(lines)

    async def get_plan(
        self,
        plan_id: str,
        __event_emitter__=None,
        __user__: Optional[dict] = None,
    ) -> str:
        """查看指定任务计划的详细内容和当前进度。

        :param plan_id: 计划 ID（创建时返回的 8 位编号）
        """
        plan = self._load_plan(plan_id)
        if plan is None:
            return f"❌ 找不到计划 {plan_id}。可先说「列出所有计划」查看已有计划。"
        return self._render_plan(plan)

    async def update_step(
        self,
        plan_id: str,
        step_index: int,
        status: str,
        __event_emitter__=None,
        __user__: Optional[dict] = None,
    ) -> str:
        """更新任务计划中某个步骤的状态。

        :param plan_id: 计划 ID
        :param step_index: 步骤序号（从 1 开始）
        :param status: 新状态，支持：待办 / 进行中 / 已完成 / 失败
        """
        plan = self._load_plan(plan_id)
        if plan is None:
            return f"❌ 找不到计划 {plan_id}。"

        new_status = self._normalize_status(status)
        for step in plan["steps"]:
            if step["index"] == step_index:
                step["status"] = new_status
                plan["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                self._save_plan(plan)
                done = sum(1 for s in plan["steps"] if s["status"] == STATUS_DONE)
                return (
                    f"✅ 已更新「{plan['title']}」第 {step_index} 步为「{status}」\n"
                    f"当前进度：{self._progress_bar(done, len(plan['steps']))} ({done}/{len(plan['steps'])})"
                )
        return f"❌ 计划 {plan_id} 中没有第 {step_index} 步（共 {len(plan['steps'])} 步）。"

    async def delete_plan(
        self,
        plan_id: str,
        __event_emitter__=None,
        __user__: Optional[dict] = None,
    ) -> str:
        """删除一个任务计划。

        :param plan_id: 计划 ID
        """
        path = self._plan_path(plan_id)
        if not os.path.exists(path):
            return f"❌ 找不到计划 {plan_id}。"
        os.remove(path)
        return f"🗑️ 计划 {plan_id} 已删除。"

    # ------------------------------------------------------------------ 展示辅助
    @staticmethod
    def _progress_bar(done: int, total: int) -> str:
        """生成文本进度条，如 ██████░░░░ 60%。"""
        if total == 0:
            return ""
        filled = round(done / total * 10)
        percent = round(done / total * 100)
        return f"{'█' * filled}{'░' * (10 - filled)} {percent}%"

    def _render_plan(self, plan: dict) -> str:
        """把计划渲染成带图标和进度条的文本。"""
        done = sum(1 for s in plan["steps"] if s["status"] == STATUS_DONE)
        lines = [
            f"📋 计划「{plan['title']}」（ID: {plan['id']}）",
            f"进度：{self._progress_bar(done, len(plan['steps']))} ({done}/{len(plan['steps'])})",
            "",
        ]
        for s in plan["steps"]:
            icon = STATUS_ICONS.get(s["status"], "⬜")
            lines.append(f"  {icon} {s['index']}. {s['content']}")
        return "\n".join(lines)
