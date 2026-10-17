# 架构说明

## 1. 总体架构

本项目由两大部分组成，全部运行在一台安卓平板上：

```
                    ┌─────────────────────────────────────────────┐
                    │                安卓平板                      │
                    │                                             │
  平板浏览器 ──────►│  ┌───────────────┐    ┌──────────────────┐  │
  (触摸操作)        │  │  Termux 原生层 │    │ proot Ubuntu 容器 │  │
                    │  │               │    │                  │  │
                    │  │  Ollama :11434│◄──►│  Open WebUI:8080 │  │
                    │  │  · 模型推理    │HTTP│  · 网页聊天界面   │  │
                    │  │  · llama.cpp  │API │  · 多人房间       │  │
                    │  │  · 模型管理    │    │  · Agent 工具     │  │
                    │  │               │    │  · 触屏主题       │  │
                    │  └───────────────┘    │                  │  │
                    │                       │  Code Studio:8899│  │
                    │                       │  · 代码编辑器     │  │
                    │                       │  · AI 生成/解释   │  │
                    │                       │  · 代码编译运行   │  │
                    │                       └──────────────────┘  │
                    └─────────────────────────────────────────────┘
```

### 1.1 Termux 原生层：Ollama 后端

- **职责**：大模型推理、模型下载与管理、提供 OpenAI 兼容 API
- **安装方式**：Termux 官方软件源（`pkg install ollama`）
- **监听地址**：`0.0.0.0:11434`（局域网内其他设备也可调用）
- **关键配置**：
  - `OLLAMA_MAX_LOADED_MODELS=1`：平板内存有限，同时只在内存保留 1 个模型
  - `OLLAMA_KEEP_ALIVE=30m`：模型空闲 30 分钟后自动卸载，释放内存

### 1.2 proot Ubuntu 容器：Web 服务层

- **职责**：Open WebUI 网页界面 + 代码编辑器 + Agent 工具运行环境
- **为什么用 proot 容器**：Open WebUI 的 Python 依赖（fastapi、uvicorn、bcrypt 等）
  在 glibc 的 Ubuntu 环境中最稳定，Termux 原生 Python 直接安装容易遇到编译问题
- **网络互通**：proot 不隔离网络，容器内访问 `127.0.0.1:11434` 即 Termux 的 Ollama
- **数据存放**：容器内 `/root/.tablet-workbench/`（运行数据、日志、PID）
  和 `/root/.open-webui/`（Open WebUI 数据库、上传文件）

## 2. 数据流

### 2.1 一次普通对话

```
用户输入
  → Open WebUI 前端（浏览器）
  → Open WebUI 后端（FastAPI，容器内 :8080）
  → Ollama API（Termux :11434，/api/chat）
  → llama.cpp 推理（CPU）
  → 流式返回 Token
  → 浏览器逐字显示
```

### 2.2 Agent 工具调用

```
用户提问「帮我写个 C++ 冒泡排序并运行」
  → Open WebUI 判断需要调用工具
  → 调用「代码运行工具」（容器内 Python 进程）
  → 工具内 g++ 编译 + 运行，捕获 stdout/stderr
  → 结果作为工具返回内容喂回模型
  → 模型基于运行结果组织最终回答
```

### 2.3 代码编辑器的 AI 功能

```
Code Studio 页面（:8899）
  → POST /api/run   → 本地 g++/python3/node 执行，返回输出
  → POST /api/ai    → 转发到 Open WebUI /api/chat/completions（OpenAI 兼容接口）
                     → Ollama 推理 → 返回 AI 生成/解释的代码
  → GET  /api/models→ 查询 Ollama 已安装模型，填充页面模型下拉框
```

## 3. 端口规划

| 端口 | 服务 | 绑定地址 | 说明 |
|---|---|---|---|
| 11434 | Ollama API | 0.0.0.0 | 模型推理接口 |
| 8080 | Open WebUI | 0.0.0.0 | 网页聊天（局域网可访问，方便多人使用） |
| 8899 | Code Studio | 127.0.0.1 | 代码编辑器（默认仅本机；改 `EDITOR_HOST=0.0.0.0` 可开放局域网） |

## 4. 存储布局

| 路径 | 位置 | 内容 |
|---|---|---|
| `~/.ollama/` | Termux | 模型权重文件（默认模型约 1.1GB） |
| `/root/workbench/` | Ubuntu 容器 | 项目代码、虚拟环境 `.venv` |
| `/root/.tablet-workbench/data/` | Ubuntu 容器 | Agent 数据：任务计划、长期记忆 |
| `/root/.open-webui/` | Ubuntu 容器 | Open WebUI 数据库、用户、知识库 |
| `~/.tablet-workbench/` | Termux | Ollama 运行日志与 PID |

## 5. 模型体系

```
qwen:1.8b（Qwen1.5-1.8B 基础模型，默认下载）
   │
   ├── workbench-agent（叠加 Agent 系统提示词，默认对话模型）
   │
   └── 你的 LoRA 模型（FROM qwen:1.8b + ADAPTER 适配器）
```

可选升级模型（内存允许时）：`qwen2.5:3b`、`qwen2.5:7b`、`qwen3:4b`、`gemma3:4b`，
模型越大，Agent 工具调用与代码能力越强。完整清单见 `ollama/models.json`。

## 6. 安全说明

- 所有数据（对话、代码、模型）均保存在平板本地，不上传任何云端
- Open WebUI 默认开启认证（`WEBUI_AUTH=True`）、关闭公开注册（`ENABLE_SIGNUP=False`），
  账号由管理员在后台创建
- 代码运行工具以服务权限执行本机代码，属于单用户本地工具；
  请勿在不可信网络中开放端口，或为 Open WebUI 设置强密码
