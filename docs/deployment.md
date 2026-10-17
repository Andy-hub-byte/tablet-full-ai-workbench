# Termux 部署详解

> 快速部署请直接看 [README 快速开始](../README.md#-快速开始termux-一键部署)，本文档讲解每一步的原理、前置条件和手动分步命令。

## 1. 前置条件

| 条件 | 说明 |
|---|---|
| Termux | 从 **F-Droid** 或 **GitHub Releases** 安装，勿用 Play 商店旧版 |
| 存储空间 | ≥ 6GB 可用（模型 1.1GB + Ubuntu 容器约 1.5GB + Python 依赖约 1GB） |
| 内存 | ≥ 4GB（运行 1.8B 模型） |
| 网络 | 能访问 GitHub 与 Ollama 模型仓库 |

### 1.1 强烈建议的系统设置

安装完成后，按以下步骤设置，否则 Android 可能随时杀掉后台服务：

1. 设置 → 关于平板 → 连续点击「版本号」7 次，开启开发者选项
2. 设置 → 系统 → 开发者选项 → 关闭「后台进程限制」/ 开启「禁用子进程限制」
   （不同品牌路径略有差异）
3. 在 Termux 中执行 `termux-wake-lock` 获取唤醒锁，并在通知栏常驻 Termux
4. 在系统电池设置中，将 Termux 设为「不限制电池用量」

## 2. 一键部署

```bash
pkg install -y git
git clone https://github.com/Andy-hub-byte/tablet-full-ai-workbench.git
cd tablet-full-ai-workbench
bash scripts/install.sh
```

`install.sh` 会自动完成以下 9 个步骤，每步都有中文提示，失败时会给出原因：

| 步骤 | 内容 |
|---|---|
| 1 | 检查运行环境（架构 / 存储 / 内存） |
| 2 | 安装 Termux 依赖（tur-repo、ollama、proot-distro、git、curl） |
| 3 | 配置并启动 Ollama（写入 `~/.bashrc`，等待服务就绪） |
| 4 | 拉取默认模型 `qwen:1.8b`（Qwen1.5-1.8B） |
| 5 | 安装 proot Ubuntu 容器及依赖（Python、g++、Node.js） |
| 6 | 克隆项目到容器、创建虚拟环境、安装 Open WebUI |
| 7 | 创建 Agent 人格模型 `workbench-agent` |
| 8 | 注入触屏主题、批量导入 Agent 工具 |
| 9 | 打印部署结果与访问地址 |

脚本可重复执行（幂等），用于修复或更新环境。

## 3. 手动分步部署（理解原理 / 排查问题）

如果一键脚本某步失败，可以按下面命令手动执行对应步骤。

### 3.1 安装 Ollama（Termux 原生）

```bash
pkg update -y
pkg install -y tur-repo      # tur-repo 提供 ollama 包
pkg install -y ollama
ollama --version             # 验证安装

# 配置环境变量（写入 ~/.bashrc 永久生效）
cat >> ~/.bashrc <<'EOF'
export OLLAMA_HOST=0.0.0.0:11434
export OLLAMA_MAX_LOADED_MODELS=1
export OLLAMA_KEEP_ALIVE=30m
EOF
source ~/.bashrc

ollama serve &               # 启动服务
curl http://127.0.0.1:11434/api/version   # 验证
ollama pull qwen:1.8b        # 下载默认模型（约 1.1GB）
```

### 3.2 安装 Ubuntu 容器（proot）

```bash
pkg install -y proot-distro
proot-distro install ubuntu
proot-distro login ubuntu --shared-tmp -- bash -lc '
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -y
  apt-get install -y python3 python3-venv python3-pip g++ nodejs git curl ca-certificates
'
```

### 3.3 安装 Open WebUI（容器内）

```bash
proot-distro login ubuntu --shared-tmp -- bash -lc '
  git clone --depth 1 https://github.com/Andy-hub-byte/tablet-full-ai-workbench.git /root/workbench
  cd /root/workbench
  python3 -m venv .venv
  . .venv/bin/activate
  pip install --upgrade pip
  pip install open-webui
'
```

### 3.4 创建 Agent 人格模型（Termux 侧）

```bash
ROOTFS="$PREFIX/var/lib/proot-distro/installed-rootfs/ubuntu"
ollama create workbench-agent -f "$ROOTFS/root/workbench/ollama/Modelfile.qwen15-agent"
```

### 3.5 配置与启动（容器内）

```bash
proot-distro login ubuntu --shared-tmp -- bash -lc '
  cd /root/workbench
  cp webui/env.template .env      # 按需修改端口等配置
  bash scripts/patch-ui.sh        # 注入触屏主题
  bash scripts/services-start.sh  # 启动 Open WebUI + 代码编辑器
'
```

### 3.6 导入 Agent 工具（容器内，Open WebUI 启动后）

```bash
proot-distro login ubuntu --shared-tmp -- bash -lc '
  cd /root/workbench
  . .venv/bin/activate
  python scripts/import-tools.py
'
```

## 4. 部署模式对比

| 模式 | 说明 | 适用场景 |
|---|---|---|
| **proot 容器（默认，推荐）** | Open WebUI 运行在 Ubuntu 容器中，依赖兼容性最好 | 所有用户 |
| Termux 原生 Python（实验性） | `pip install open-webui` 直接装在 Termux | 高级用户折腾，可能遇到编译问题 |

## 5. 更新项目

```bash
# Termux 侧脚本更新
cd ~/tablet-full-ai-workbench && git pull

# 容器内项目更新
proot-distro login ubuntu --shared-tmp -- bash -lc 'cd /root/workbench && git pull'
```

更新 Open WebUI 本体（会覆盖前端主题，需重新注入）：

```bash
proot-distro login ubuntu --shared-tmp -- bash -lc '
  cd /root/workbench && . .venv/bin/activate
  pip install --upgrade open-webui
  bash scripts/patch-ui.sh
'
```

## 6. 卸载

```bash
# 停止服务
bash scripts/stop.sh

# 删除容器内项目与数据
proot-distro reset ubuntu      # 或 proot-distro remove ubuntu

# 删除 Termux 侧数据
rm -rf ~/.ollama ~/.tablet-workbench ~/tablet-full-ai-workbench
```
