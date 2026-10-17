# 版权声明
本项目基于 Open WebUI（原作者Open WebUI团队）和 Ollama（原作者Ollama团队）二次开发。
两个原项目都使用 MIT License。衍生项目同样遵循 MIT License，保留原作者版权。
Ollama原仓库地址：https://github.com/ollama/ollama
Open WebUI原仓库地址：https://github.com/open-webui/open-webui

> ⭐ 如果本项目对你有帮助，欢迎点 Star 支持本项目！

---

# 平板本地 AI 工作台 · tablet-full-ai-workbench

一个**完整部署在安卓平板 Termux 里**的本地 AI 工作台，功能对标 WorkBuddy：
不依赖任何云端服务，数据全部留在自己的平板上；打开浏览器就能聊天、写代码、跑代码、做任务规划、多人协作。

- 🤖 **完整 Agent 智能代理**：工具调用、任务拆解规划、长对话记忆
- 💻 **网页代码编辑器**：手动敲代码；AI 生成 / 解释 / 修复代码；一键运行看输出
- 🌐 **本地大模型**：默认 Qwen1.5-1.8B，支持切换 qwen2.5 / qwen3 / gemma3 等各类开源模型
- 🧩 **LoRA 自定义模型**：一键导入 LoRA 微调适配器，生成你的专属模型
- 👥 **多人对话房间**：Open WebUI Channels 团队实时聊天 + 多用户权限管理
- 👆 **平板触屏适配**：大按钮、大字体、适合单手操作的触屏优化主题
- 🚀 **一键部署**：Termux 里一条命令装好整套环境

## 🏗️ 系统架构

```
┌──────────────────────────────── 安卓平板 ────────────────────────────────┐
│                                                                          │
│  ┌──────────── Termux（原生）──────────┐   ┌──────── proot Ubuntu 容器 ────────┐
│  │                                     │   │                                    │
│  │   Ollama 服务        :11434         │   │   Open WebUI          :8080       │
│  │   ├─ qwen:1.8b       默认基础模型   │◄──┤   ├─ 网页聊天 / 多人房间 Channels  │
│  │   ├─ workbench-agent Agent 人格模型 │ HTTP │   ├─ Agent 工具（代码运行/      │
│  │   └─ 你的 LoRA 自定义模型            │ API │   │    任务规划/记忆/搜索/状态） │
│  │                                     │   │   └─ 触屏适配主题 custom.css      │
│  └─────────────────────────────────────┘   │                                    │
│                                            │   代码编辑器 Code Studio :8899    │
│                                            │   ├─ CodeMirror 网页编辑器        │
│                                            │   ├─ AI 生成 / 解释 / 修复代码    │
│                                            │   └─ C++/Python/JS 一键运行       │
│                                            └────────────────────────────────────┘
│                                                                          │
│   平板浏览器访问：                                                         │
│     · 聊天与 Agent  →  http://localhost:8080                              │
│     · 代码编辑器    →  http://localhost:8899                              │
└──────────────────────────────────────────────────────────────────────────┘
```

## 📁 目录结构

```
tablet-full-ai-workbench/
├── README.md                  # 项目说明（含版权声明）
├── LICENSE                    # MIT 许可证（保留上游版权）
├── docs/                      # 详细文档
│   ├── architecture.md        #   架构与数据流说明
│   ├── deployment.md          #   Termux 部署详解
│   ├── user-guide.md          #   使用指南
│   └── troubleshooting.md     #   常见问题排障
├── scripts/                   # 部署与服务管理脚本
│   ├── install.sh             #   一键部署（Termux 入口）
│   ├── start.sh / stop.sh / status.sh      # 服务管理（Termux 入口）
│   ├── services-start.sh / services-stop.sh# 容器内服务管理
│   ├── patch-ui.sh            #   注入触屏主题
│   ├── import-tools.py        #   批量导入 Agent 工具
│   └── backup.sh / restore.sh #   备份与恢复
├── ollama/                    # Ollama 模型配置
│   ├── Modelfile.qwen15-agent #   Qwen1.5-1.8B Agent 人格模型
│   ├── Modelfile.lora-template#   LoRA 导入模板
│   ├── import-lora.sh         #   LoRA 一键导入脚本
│   └── models.json            #   推荐模型清单
├── webui/                     # Open WebUI 定制
│   ├── env.template           #   环境变量模板
│   ├── custom.css             #   平板触屏适配主题
│   └── tools/                 #   Agent 工具（Python）
│       ├── run_code.py        #   代码运行（C++/Python/JS/Shell）
│       ├── task_planner.py    #   任务拆解规划
│       ├── memory.py          #   长期记忆
│       ├── web_search.py      #   联网搜索（无需 API Key）
│       └── device_status.py   #   设备状态查询
├── editor/                    # 网页代码编辑器 Code Studio
│   ├── server.py              #   后端服务（纯 Python 标准库）
│   └── static/index.html      #   前端页面（CodeMirror）
└── agent/                     # Agent 配置
    ├── system-prompt.txt      #   Agent 系统提示词
    └── config.json            #   Agent 能力配置
```

## 📋 硬件要求

| 项目 | 最低要求 | 推荐配置 |
|---|---|---|
| 内存 | 4GB | 6GB 及以上 |
| 存储空间 | 6GB 可用 | 10GB 及以上 |
| 系统 | Android 9+ | Android 12+ |
| 架构 | aarch64（64 位 ARM） | aarch64 |
| 软件 | Termux（F-Droid / GitHub Releases 版） | 最新版 Termux |

> ⚠️ 请从 F-Droid 或 Termux GitHub Releases 安装 Termux，**不要用 Google Play 商店的旧版**（版本过旧，包管理器不兼容）。

## 🚀 快速开始（Termux 一键部署）

```bash
# 1. 平板安装 Termux 后打开，克隆本项目
pkg install -y git
git clone https://github.com/Andy-hub-byte/tablet-full-ai-workbench.git
cd tablet-full-ai-workbench

# 2. 一键部署（自动安装 Ollama + Ubuntu 容器 + Open WebUI + 代码编辑器 + Agent 工具）
bash scripts/install.sh
```

部署过程约 15~30 分钟（取决于网速），全程中文提示。完成后：

| 服务 | 地址 | 说明 |
|---|---|---|
| 聊天与 Agent | http://localhost:8080 | Open WebUI，首次使用请注册管理员账号 |
| 代码编辑器 | http://localhost:8899 | Code Studio，AI 生成/解释/一键运行 |

## 🎮 服务管理

```bash
bash scripts/start.sh     # 启动全部服务（Ollama + Open WebUI + 代码编辑器）
bash scripts/stop.sh      # 停止全部服务
bash scripts/status.sh    # 查看运行状态、模型列表、局域网访问地址
```

## 📖 使用指南

### 1. 开始对话

浏览器打开 http://localhost:8080 ，注册第一个账号（自动成为管理员）。
在顶部模型选择器中切换模型：

- `workbench-agent`：默认的 Agent 人格模型（基于 Qwen1.5-1.8B 定制）
- `qwen:1.8b`：原始基础模型
- 其他：用 `ollama pull <模型名>` 下载后自动出现在列表里

### 2. 使用 Agent 工具

部署脚本会自动导入 5 个 Agent 工具（管理员面板 → 工作区 → 工具 可查看）：

| 工具 | 作用 |
|---|---|
| 代码运行 | 让 AI 直接在平板上编译运行 C++/Python/JS/Shell 代码 |
| 任务规划 | 把复杂任务拆解成步骤清单，逐步执行、更新进度 |
| 长期记忆 | 保存你的偏好和背景信息，跨对话记忆 |
| 联网搜索 | DuckDuckGo 搜索最新信息（无需 API Key） |
| 设备状态 | 查看平板内存、存储、已加载模型 |

在对话界面点击右上角「集成」图标，勾选需要启用的工具，即可让 AI 调用。

> 💡 小模型（1.8B）的工具调用能力有限，如需更强的 Agent 能力，
> 建议切换 `qwen2.5:3b` 或 `qwen2.5:7b`（内存允许时），工具调用稳定性会明显提升。

### 3. 代码编辑器（Code Studio）

打开 http://localhost:8899 ：

- **手动敲代码**：CodeMirror 编辑器，支持 C++ / Python / JavaScript / HTML / Shell
- **AI 生成**：输入需求，AI 生成完整代码并填入编辑器
- **AI 解释 / AI 修复**：一键让 AI 讲解代码或修复错误
- **一键运行**：点击「运行」或按 `Ctrl+Enter`，下方即时显示输出、错误和退出码
- **HTML 预览**：语言选 HTML 时，运行后会生成可实时预览的页面

### 4. 切换 / 下载模型

```bash
ollama pull qwen2.5:3b        # 下载模型
ollama list                   # 查看已安装模型
ollama rm <模型名>            # 删除模型
```

常用模型选择见 [ollama/models.json](ollama/models.json)。

### 5. 导入 LoRA 微调模型

```bash
# 交互式导入：按提示输入适配器路径即可
bash ollama/import-lora.sh
```

手动方式：编辑 `ollama/Modelfile.lora-template`，然后

```bash
ollama create my-lora-model -f Modelfile.lora-template
```

详见 [docs/user-guide.md](docs/user-guide.md#5-导入-lora-微调模型)。

### 6. 多人对话房间

1. 管理员登录后进入 管理员面板 → 用户，创建家庭成员账号
2. 左侧菜单进入「频道 / Channels」，创建聊天房间并邀请成员
3. 同一 Wi-Fi 下，其他设备浏览器访问 `http://<平板IP>:8080` 即可加入

## 👆 触屏适配说明

项目内置平板触屏主题 `webui/custom.css`（部署时自动注入），包括：

- 所有按钮最小 48px 触控区域，符合移动端触屏规范
- 聊天消息、代码块更大字号，长时间阅读不费力
- 输入框底部固定，配合平板键盘单手可达
- 侧边栏加宽，房间/模型列表更易点选
- 横屏平板自动切换双栏布局

## 💾 备份与恢复

```bash
bash scripts/backup.sh                    # 备份对话数据、记忆、任务计划、配置
bash scripts/backup.sh --full             # 额外备份 Open WebUI 全部数据（含知识库）
bash scripts/restore.sh <备份文件路径>     # 恢复
```

## 📚 详细文档

- [架构说明](docs/architecture.md)
- [Termux 部署详解](docs/deployment.md)
- [使用指南](docs/user-guide.md)
- [常见问题排障](docs/troubleshooting.md)

## 📄 许可证

本项目以 MIT License 开源，保留 Ollama 与 Open WebUI 上游项目的版权声明，详见 [LICENSE](LICENSE)。
