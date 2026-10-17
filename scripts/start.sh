#!/data/data/com.termux/files/usr/bin/bash
#===============================================================================
# 服务启动脚本（Termux 侧总入口）
#-------------------------------------------------------------------------------
# 功能：启动全部服务 —— Ollama（Termux 原生）+ Open WebUI / 代码编辑器（proot 容器内）
# 用法：bash scripts/start.sh
#===============================================================================
set -euo pipefail

#------------------------------------------------------------------------------
# 配置
#------------------------------------------------------------------------------
PROOT_DISTRO="ubuntu"
PROOT_WORKDIR="/root/workbench"
WB_TERMUX_DIR="${HOME}/.tablet-workbench"
RUN_DIR="${WB_TERMUX_DIR}/run"
LOG_DIR="${WB_TERMUX_DIR}/logs"
OWUI_PORT="${OWUI_PORT:-8080}"
EDITOR_PORT="${EDITOR_PORT:-8899}"

RED=$'\e[31m'; GREEN=$'\e[32m'; YELLOW=$'\e[33m'; BLUE=$'\e[34m'; BOLD=$'\e[1m'; RESET=$'\e[0m'
log_info() { echo -e "${GREEN}[信息]${RESET} $*"; }
log_warn() { echo -e "${YELLOW}[提示]${RESET} $*"; }
log_err()  { echo -e "${RED}[错误]${RESET} $*" >&2; }
die()     { log_err "$*"; exit 1; }

#------------------------------------------------------------------------------
# 前置检查
#------------------------------------------------------------------------------
[ -n "${PREFIX:-}" ] || die "请在 Termux 中运行本脚本。"
command -v proot-distro >/dev/null 2>&1 || die "未安装 proot-distro，请先执行 bash scripts/install.sh"
mkdir -p "$RUN_DIR" "$LOG_DIR"

#------------------------------------------------------------------------------
# 1. 启动 Ollama（Termux 原生服务）
#------------------------------------------------------------------------------
log_info "启动 Ollama 服务……"
export OLLAMA_HOST="${OLLAMA_HOST:-0.0.0.0:11434}"
export OLLAMA_MAX_LOADED_MODELS="${OLLAMA_MAX_LOADED_MODELS:-1}"
export OLLAMA_KEEP_ALIVE="${OLLAMA_KEEP_ALIVE:-30m}"

if curl -s --max-time 2 "http://127.0.0.1:11434/api/version" >/dev/null 2>&1; then
  log_info "Ollama 已在运行"
else
  nohup ollama serve > "${LOG_DIR}/ollama.log" 2>&1 &
  echo $! > "${RUN_DIR}/ollama.pid"
  local_i=0
  while [ $local_i -lt 30 ]; do
    curl -s --max-time 2 "http://127.0.0.1:11434/api/version" >/dev/null 2>&1 && break
    sleep 1
    local_i=$((local_i + 1))
  done
  curl -s --max-time 2 "http://127.0.0.1:11434/api/version" >/dev/null 2>&1 \
    || die "Ollama 启动失败，查看 ${LOG_DIR}/ollama.log"
  log_info "Ollama 启动成功（PID $(cat "${RUN_DIR}/ollama.pid")）"
fi

#------------------------------------------------------------------------------
# 2. 启动容器内 Web 服务（Open WebUI + 代码编辑器）
#------------------------------------------------------------------------------
log_info "启动 Open WebUI 与代码编辑器（proot 容器内）……"
proot-distro login "${PROOT_DISTRO}" --shared-tmp -- bash -lc "bash ${PROOT_WORKDIR}/scripts/services-start.sh" \
  || die "容器内服务启动失败。进入容器查看日志：proot-distro login ubuntu -- tail -50 /root/.tablet-workbench/logs/open-webui.log"

#------------------------------------------------------------------------------
# 3. 打印访问地址
#------------------------------------------------------------------------------
LAN_IP="$(python3 -c '
import socket
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80)); print(s.getsockname()[0]); s.close()
except Exception:
    print("未知")
' 2>/dev/null || echo "未知")"

echo
echo -e "${BOLD}==================== 服务已启动 ====================${RESET}"
echo "   · 聊天与 Agent  ： http://localhost:${OWUI_PORT}"
echo "   · 代码编辑器    ： http://localhost:${EDITOR_PORT}"
echo "   · 局域网访问    ： http://${LAN_IP}:${OWUI_PORT}（多人房间用）"
echo -e "${BOLD}====================================================${RESET}"
log_warn "提示：执行 termux-wake-lock 可防止 Android 清理后台服务。"
