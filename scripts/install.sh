#!/data/data/com.termux/files/usr/bin/bash
#===============================================================================
# 平板本地 AI 工作台 · 一键部署脚本
#-------------------------------------------------------------------------------
# 适用环境：Android 平板 / 手机 + Termux（aarch64 架构）
# 功能    ：自动安装 Ollama + Open WebUI + 代码编辑器 + Agent 工具全家桶
# 用法    ：bash scripts/install.sh
#           REPO_URL=<仓库地址> bash scripts/install.sh   # 使用 fork 后的仓库
# 特点    ：幂等可重复执行；每步中文提示；失败时给出排查建议
#===============================================================================
set -euo pipefail

#------------------------------------------------------------------------------
# 基础配置（可通过环境变量覆盖）
#------------------------------------------------------------------------------
REPO_URL="${REPO_URL:-https://github.com/Andy-hub-byte/tablet-full-ai-workbench.git}"
DEFAULT_MODEL="qwen:1.8b"              # 默认基础模型：Qwen1.5-1.8B（约 1.1GB）
AGENT_MODEL_NAME="workbench-agent"     # Agent 人格模型名（由 Modelfile 生成）
PROOT_DISTRO="ubuntu"                  # proot 容器发行版名称
PROOT_ROOTFS="${PREFIX:-/nonexistent}/var/lib/proot-distro/installed-rootfs/${PROOT_DISTRO}"
PROOT_WORKDIR="/root/workbench"        # 项目在容器内的安装目录
OWUI_PORT="${OWUI_PORT:-8080}"         # Open WebUI 端口
EDITOR_PORT="${EDITOR_PORT:-8899}"     # 代码编辑器端口
WB_TERMUX_DIR="${HOME}/.tablet-workbench"   # Termux 侧运行数据目录（日志/PID）

#------------------------------------------------------------------------------
# 日志与颜色输出
#------------------------------------------------------------------------------
RED=$'\e[31m'; GREEN=$'\e[32m'; YELLOW=$'\e[33m'; BLUE=$'\e[34m'; BOLD=$'\e[1m'; RESET=$'\e[0m'
log_info() { echo -e "${GREEN}[信息]${RESET} $*"; }
log_warn() { echo -e "${YELLOW}[提示]${RESET} $*"; }
log_err()  { echo -e "${RED}[错误]${RESET} $*" >&2; }
log_step() { echo -e "\n${BOLD}${BLUE}========== $* ==========${RESET}"; }
die()     { log_err "$*"; exit 1; }

#==============================================================================
# 步骤 1：环境检查
#==============================================================================
check_environment() {
  log_step "步骤 1/9：检查运行环境"

  # 必须在 Termux 中运行（PREFIX 是 Termux 特有的环境变量）
  if [ -z "${PREFIX:-}" ] || [ ! -d "/data/data/com.termux/files" ]; then
    die "本脚本只能在 Termux 中运行。请先在平板安装 Termux（F-Droid 或 GitHub Releases 下载）。"
  fi

  # 目前仅适配 aarch64（64 位 ARM，覆盖几乎所有主流平板）
  local arch; arch="$(uname -m)"
  [ "$arch" = "aarch64" ] || die "检测到架构 ${arch}，本项目仅适配 aarch64（64 位 ARM）平板。"
  log_info "架构检查通过：${arch}"

  # 存储空间检查（模型 1.1GB + Ubuntu 容器约 1.5GB + Python 依赖约 1GB）
  local avail_gb; avail_gb=$(( $(df -k "$HOME" | awk 'NR==2{print $4}') / 1024 / 1024 ))
  if [ "$avail_gb" -lt 6 ]; then
    log_warn "当前可用存储约 ${avail_gb}GB，建议至少 6GB，否则可能无法容纳模型和依赖。"
    read -r -p "是否继续？(y/N) " ans
    [ "$ans" = "y" ] || [ "$ans" = "Y" ] || die "已取消安装。"
  else
    log_info "可用存储约 ${avail_gb}GB，空间充足。"
  fi

  # 内存检查（运行 1.8B 模型建议 4GB 以上）
  local mem_mb; mem_mb="$(awk '/MemTotal/{print int($2/1024)}' /proc/meminfo)"
  log_info "平板总内存约 ${mem_mb}MB"
  [ "$mem_mb" -ge 3500 ] || log_warn "内存低于 3.5GB，运行 1.8B 模型会比较吃力，建议改用更小的模型（qwen:0.5b）。"

  # 提醒 Android 系统设置（防止后台被杀，这是最常见的坑）
  log_warn "请确保已完成：开发者选项 → 关闭后台进程限制；系统电池设置 → Termux 设为不限制。"
  log_warn "详见 docs/deployment.md 第 1.1 节。"
}

#==============================================================================
# 步骤 2：安装 Termux 基础依赖
#==============================================================================
install_termux_packages() {
  log_step "步骤 2/9：安装 Termux 基础依赖（ollama / proot-distro / git 等）"
  pkg update -y || true
  # tur-repo 提供 ollama 包；proot-distro 用于运行 Ubuntu 容器
  pkg install -y tur-repo || log_warn "tur-repo 安装失败，尝试直接安装 ollama（多数情况也可用）"
  pkg install -y ollama proot-distro git curl wget || die "Termux 依赖安装失败，请检查网络后重试。"
  log_info "Ollama 版本：$(ollama --version 2>/dev/null || echo '未知')"
}

#==============================================================================
# 步骤 3：配置并启动 Ollama
#==============================================================================
configure_ollama() {
  log_step "步骤 3/9：配置并启动 Ollama 服务"

  # 把 Ollama 配置写入 ~/.bashrc（幂等：已存在则跳过）
  if ! grep -q "平板AI工作台-Ollama配置" "${HOME}/.bashrc" 2>/dev/null; then
    cat >> "${HOME}/.bashrc" <<'EOF'

# ===== 平板AI工作台-Ollama配置（由 install.sh 添加）=====
export OLLAMA_HOST=0.0.0.0:11434        # 监听所有网卡：局域网其他设备可调用 API
export OLLAMA_MAX_LOADED_MODELS=1       # 平板内存有限，同时只保留 1 个模型在内存
export OLLAMA_KEEP_ALIVE=30m            # 模型空闲 30 分钟后自动卸载，节省内存
EOF
    log_info "已向 ~/.bashrc 写入 Ollama 配置（重开 Termux 或执行 source ~/.bashrc 后永久生效）"
  fi

  # 当前会话立即生效
  export OLLAMA_HOST="0.0.0.0:11434"
  export OLLAMA_MAX_LOADED_MODELS=1
  export OLLAMA_KEEP_ALIVE="30m"

  mkdir -p "${WB_TERMUX_DIR}/run" "${WB_TERMUX_DIR}/logs"

  # 启动 Ollama（已在运行则跳过）
  if curl -s --max-time 2 "http://127.0.0.1:11434/api/version" >/dev/null 2>&1; then
    log_info "Ollama 服务已在运行"
    return 0
  fi
  log_info "正在启动 Ollama 服务……"
  nohup ollama serve > "${WB_TERMUX_DIR}/logs/ollama.log" 2>&1 &
  echo $! > "${WB_TERMUX_DIR}/run/ollama.pid"

  # 等待服务就绪（最多 30 秒）
  local i
  for i in $(seq 1 30); do
    curl -s --max-time 2 "http://127.0.0.1:11434/api/version" >/dev/null 2>&1 && break
    sleep 1
  done
  curl -s --max-time 2 "http://127.0.0.1:11434/api/version" >/dev/null 2>&1 \
    || die "Ollama 启动失败，请查看日志：${WB_TERMUX_DIR}/logs/ollama.log"
  log_info "Ollama 服务启动成功（http://127.0.0.1:11434）"
}

#==============================================================================
# 步骤 4：拉取默认模型 Qwen1.5-1.8B
#==============================================================================
pull_default_model() {
  log_step "步骤 4/9：拉取默认基础模型 Qwen1.5-1.8B（约 1.1GB，耗时视网速而定）"
  if ollama list 2>/dev/null | awk '{print $1}' | grep -qx "${DEFAULT_MODEL}"; then
    log_info "模型 ${DEFAULT_MODEL} 已存在，跳过下载"
  else
    ollama pull "${DEFAULT_MODEL}" || die "模型下载失败，请检查网络后重试。"
  fi
}

#==============================================================================
# 步骤 5：安装 proot Ubuntu 容器及依赖
#==============================================================================
setup_proot_ubuntu() {
  log_step "步骤 5/9：安装 proot Ubuntu 容器（Open WebUI 的运行环境）"

  # 通过 rootfs 目录判断容器是否已安装（比解析 list 输出更可靠）
  if [ -d "${PROOT_ROOTFS}/root" ]; then
    log_info "Ubuntu 容器已安装"
  else
    log_info "正在下载安装 Ubuntu rootfs（约 100MB）……"
    proot-distro install "${PROOT_DISTRO}" || die "Ubuntu 容器安装失败，请重试。"
  fi

  # 容器内依赖：Python 运行环境 + g++（C++ 编译器）+ Node.js（运行 JS）
  log_info "在容器内安装 Python / g++ / Node.js（首次约需 3~8 分钟）……"
  proot-distro login "${PROOT_DISTRO}" --shared-tmp -- bash -lc '
    set -e
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -y
    apt-get install -y python3 python3-venv python3-pip g++ nodejs git curl ca-certificates
  ' || die "容器内依赖安装失败。可进入容器手动执行：proot-distro login ubuntu"
  log_info "容器内依赖安装完成"
}

#==============================================================================
# 步骤 6：部署项目 + 安装 Open WebUI
#==============================================================================
deploy_project() {
  log_step "步骤 6/9：部署项目并安装 Open WebUI（约需 5~15 分钟）"

  proot-distro login "${PROOT_DISTRO}" --shared-tmp -- bash -lc "
    set -e
    # 克隆或更新项目（容器内固定路径，与 Termux 侧相互独立）
    if [ -d ${PROOT_WORKDIR}/.git ]; then
      echo '项目已存在，执行 git pull 更新'
      cd ${PROOT_WORKDIR} && git pull --ff-only || true
    else
      git clone --depth 1 ${REPO_URL} ${PROOT_WORKDIR}
    fi
    cd ${PROOT_WORKDIR}

    # 创建虚拟环境并安装 Open WebUI（仅首次执行）
    if [ ! -d .venv ]; then
      python3 -m venv .venv
    fi
    . .venv/bin/activate
    pip install --upgrade pip
    pip install open-webui
  " || die "项目部署或 Open WebUI 安装失败。可参考 docs/troubleshooting.md Q3。"

  # 生成 .env 配置文件（已存在则不覆盖，保留用户修改）
  if [ -f "${PROOT_ROOTFS}/root/workbench/.env" ]; then
    log_info ".env 已存在，保留现有配置"
  else
    proot-distro login "${PROOT_DISTRO}" --shared-tmp -- bash -lc "
      cd ${PROOT_WORKDIR}
      cp webui/env.template .env
      sed -i 's/^PORT=.*/PORT=${OWUI_PORT}/; s/^EDITOR_PORT=.*/EDITOR_PORT=${EDITOR_PORT}/' .env
    "
    log_info "已生成 .env（端口：Open WebUI ${OWUI_PORT} / 代码编辑器 ${EDITOR_PORT}）"
  fi
}

#==============================================================================
# 步骤 7：创建 Agent 人格模型
#==============================================================================
create_agent_model() {
  log_step "步骤 7/9：创建 Agent 人格模型「${AGENT_MODEL_NAME}」"
  local modelfile="${PROOT_ROOTFS}/root/workbench/ollama/Modelfile.qwen15-agent"
  if [ ! -f "$modelfile" ]; then
    die "找不到 Modelfile：$modelfile（请确认项目文件完整）"
  fi
  if ollama list 2>/dev/null | awk '{print $1}' | grep -qx "${AGENT_MODEL_NAME}"; then
    log_info "模型 ${AGENT_MODEL_NAME} 已存在，重新创建以应用最新提示词"
  fi
  # ollama 运行在 Termux 侧，直接读取 proot rootfs 中的 Modelfile 路径
  ollama create "${AGENT_MODEL_NAME}" -f "$modelfile" || die "Agent 模型创建失败。"
  log_info "Agent 人格模型创建成功"
}

#==============================================================================
# 步骤 8：注入触屏主题 + 导入 Agent 工具
#==============================================================================
apply_customizations() {
  log_step "步骤 8/9：注入触屏主题并导入 Agent 工具"

  # 触屏主题：把 custom.css 内联进 Open WebUI 前端
  proot-distro login "${PROOT_DISTRO}" --shared-tmp -- bash -lc "cd ${PROOT_WORKDIR} && bash scripts/patch-ui.sh" \
    || log_warn "主题注入失败，可稍后手动执行：proot-distro login ubuntu -- bash -lc 'cd /root/workbench && bash scripts/patch-ui.sh'"

  # 先启动 Web 服务，供 import-tools.py 连接
  proot-distro login "${PROOT_DISTRO}" --shared-tmp -- bash -lc "bash ${PROOT_WORKDIR}/scripts/services-start.sh" \
    || die "服务启动失败，请查看容器内日志 /root/.tablet-workbench/logs/"

  # 导入 5 个 Agent 工具（尽力而为：失败不影响部署，可手动导入）
  proot-distro login "${PROOT_DISTRO}" --shared-tmp -- bash -lc "
    cd ${PROOT_WORKDIR} && . .venv/bin/activate
    python scripts/import-tools.py
  " || log_warn "工具自动导入失败。可手动导入：Open WebUI → 管理员面板 → 工作区 → 工具 → 粘贴 webui/tools/*.py"
}

#==============================================================================
# 步骤 9：输出部署结果
#==============================================================================
print_summary() {
  log_step "步骤 9/9：部署完成 🎉"

  # 获取平板局域网 IP（用 python 读取，避免依赖 ifconfig）
  local lan_ip
  lan_ip="$(python3 -c '
import socket
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    print(s.getsockname()[0])
    s.close()
except Exception:
    print("未知")
' 2>/dev/null || echo "未知")"

  echo
  echo -e "${BOLD}==================== 部署成功 ====================${RESET}"
  echo
  echo "📡 服务地址（平板浏览器直接访问）："
  echo "   · 聊天与 Agent 智能体 ： http://localhost:${OWUI_PORT}"
  echo "   · 网页代码编辑器      ： http://localhost:${EDITOR_PORT}"
  echo
  echo "👥 多人房间（同一 Wi-Fi 其他设备访问）："
  echo "   · http://${lan_ip}:${OWUI_PORT}"
  echo
  echo "🚀 服务管理命令："
  echo "   bash scripts/start.sh    启动全部服务"
  echo "   bash scripts/stop.sh     停止全部服务"
  echo "   bash scripts/status.sh   查看运行状态"
  echo
  echo "📖 下一步："
  echo "   1. 浏览器打开 http://localhost:${OWUI_PORT} ，注册第一个账号（自动成为管理员）"
  echo "   2. 在对话界面「集成」中勾选需要使用的 Agent 工具"
  echo "   3. 详细使用说明见 docs/user-guide.md"
  echo
  log_warn "记得执行 termux-wake-lock 防止 Android 杀后台，并保持 Termux 通知常驻！"
  echo -e "${BOLD}==================================================${RESET}"
}

#==============================================================================
# 主流程
#==============================================================================
main() {
  echo -e "${BOLD}${BLUE}"
  echo "╔══════════════════════════════════════════════╗"
  echo "║        平板本地 AI 工作台 · 一键部署          ║"
  echo "║   Ollama + Open WebUI + 代码编辑器 + Agent   ║"
  echo "╚══════════════════════════════════════════════╝"
  echo -e "${RESET}"
  log_info "开始时间：$(date '+%Y-%m-%d %H:%M:%S')"

  check_environment
  install_termux_packages
  configure_ollama
  pull_default_model
  setup_proot_ubuntu
  deploy_project
  create_agent_model
  apply_customizations
  print_summary

  log_info "全部完成！总耗时与网速有关，祝使用愉快 🎉"
}

# 允许从任意目录调用（脚本内路径均使用相对本项目的位置）
cd "$(dirname "$(readlink -f "$0")")/.." || die "无法进入项目目录"

main "$@"
