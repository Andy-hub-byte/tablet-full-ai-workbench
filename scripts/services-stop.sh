#!/usr/bin/env bash
#===============================================================================
# 服务停止脚本（proot Ubuntu 容器内部运行）
#-------------------------------------------------------------------------------
# 由 Termux 侧 scripts/stop.sh 自动调用，请勿在 Termux 中直接执行
# 功能：通过 PID 文件停止 Open WebUI 与代码编辑器，带兜底进程清理
#===============================================================================
set -uo pipefail

RUN_DIR="/root/.tablet-workbench/run"

GREEN=$'\e[32m'; RESET=$'\e[0m'
log_info() { echo -e "${GREEN}[容器内]${RESET} $*"; }

#------------------------------------------------------------------------------
# 按 PID 文件停止服务
#------------------------------------------------------------------------------
stop_by_pidfile() {
  local name="$1"
  local pidfile="${RUN_DIR}/${name}.pid"
  if [ -f "$pidfile" ]; then
    local pid; pid="$(cat "$pidfile")"
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
      # 等待最多 5 秒优雅退出，超时则强杀
      local i
      for i in 1 2 3 4 5; do
        kill -0 "$pid" 2>/dev/null || break
        sleep 1
      done
      kill -0 "$pid" 2>/dev/null && kill -9 "$pid" 2>/dev/null || true
      log_info "${name} 已停止（PID ${pid}）"
    else
      log_info "${name} 未在运行（PID ${pid} 已失效）"
    fi
    rm -f "$pidfile"
  else
    log_info "${name} 没有 PID 文件，跳过"
  fi
}

stop_by_pidfile "open-webui"
stop_by_pidfile "editor"

#------------------------------------------------------------------------------
# 兜底清理：防止没有 PID 文件时残留进程
#------------------------------------------------------------------------------
pkill -f "open-webui serve" 2>/dev/null && log_info "已兜底清理残留的 Open WebUI 进程" || true
pkill -f "editor/server.py" 2>/dev/null && log_info "已兜底清理残留的代码编辑器进程" || true

log_info "容器内服务已全部停止。"
