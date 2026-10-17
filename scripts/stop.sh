#!/data/data/com.termux/files/usr/bin/bash
#===============================================================================
# 服务停止脚本（Termux 侧总入口）
#-------------------------------------------------------------------------------
# 功能：停止全部服务 —— Ollama + 容器内 Open WebUI / 代码编辑器
# 用法：bash scripts/stop.sh
#===============================================================================
set -euo pipefail

PROOT_DISTRO="ubuntu"
PROOT_WORKDIR="/root/workbench"
WB_TERMUX_DIR="${HOME}/.tablet-workbench"
RUN_DIR="${WB_TERMUX_DIR}/run"

RED=$'\e[31m'; GREEN=$'\e[32m'; BOLD=$'\e[1m'; RESET=$'\e[0m'
log_info() { echo -e "${GREEN}[信息]${RESET} $*"; }

[ -n "${PREFIX:-}" ] || { echo -e "${RED}[错误]${RESET} 请在 Termux 中运行本脚本。" >&2; exit 1; }

#------------------------------------------------------------------------------
# 1. 停止容器内服务（Open WebUI + 代码编辑器）
#------------------------------------------------------------------------------
log_info "停止容器内 Web 服务……"
proot-distro login "${PROOT_DISTRO}" --shared-tmp -- bash -lc "bash ${PROOT_WORKDIR}/scripts/services-stop.sh" \
  || log_info "容器内没有需要停止的服务（或容器未安装）"

#------------------------------------------------------------------------------
# 2. 停止 Ollama（Termux 原生）
#------------------------------------------------------------------------------
if [ -f "${RUN_DIR}/ollama.pid" ]; then
  PID="$(cat "${RUN_DIR}/ollama.pid")"
  if kill -0 "$PID" 2>/dev/null; then
    kill "$PID" 2>/dev/null || true
    log_info "Ollama 已停止（PID ${PID}）"
  fi
  rm -f "${RUN_DIR}/ollama.pid"
else
  # PID 文件丢失时，按进程名兜底清理
  pkill -f "ollama serve" 2>/dev/null && log_info "已按进程名停止 Ollama" || log_info "Ollama 未在运行"
fi

#------------------------------------------------------------------------------
# 3. 兜底：清理容器内可能残留的进程
#------------------------------------------------------------------------------
proot-distro login "${PROOT_DISTRO}" --shared-tmp -- bash -lc "
  pkill -f 'open-webui serve' 2>/dev/null || true
  pkill -f 'editor/server.py' 2>/dev/null || true
" || true

echo
echo -e "${BOLD}==================== 全部服务已停止 ====================${RESET}"
