#!/usr/bin/env bash
#===============================================================================
# 服务启动脚本（proot Ubuntu 容器内部运行）
#-------------------------------------------------------------------------------
# 由 Termux 侧 scripts/start.sh 自动调用，请勿在 Termux 中直接执行
# 功能：启动 Open WebUI 与代码编辑器，写入 PID 文件，等待端口就绪
#===============================================================================
set -euo pipefail

WORKDIR="/root/workbench"
RUN_DIR="/root/.tablet-workbench/run"
LOG_DIR="/root/.tablet-workbench/logs"

GREEN=$'\e[32m'; YELLOW=$'\e[33m'; RED=$'\e[31m'; RESET=$'\e[0m'
log_info() { echo -e "${GREEN}[容器内]${RESET} $*"; }
log_warn() { echo -e "${YELLOW}[容器内]${RESET} $*"; }

#------------------------------------------------------------------------------
# 前置检查
#------------------------------------------------------------------------------
[ -d "$WORKDIR/.venv" ] || { echo -e "${RED}[错误]${RESET} 未找到虚拟环境 $WORKDIR/.venv，请先执行安装脚本。" >&2; exit 1; }
mkdir -p "$RUN_DIR" "$LOG_DIR"
cd "$WORKDIR"

# 加载 .env 配置（端口、AI 接口令牌等）
set -a; [ -f ./.env ] && . ./.env; set +a
PORT="${PORT:-8080}"
EDITOR_PORT="${EDITOR_PORT:-8899}"

#------------------------------------------------------------------------------
# 启动单个服务的通用函数
#------------------------------------------------------------------------------
start_service() {
  local name="$1" cmd="$2"
  local pidfile="${RUN_DIR}/${name}.pid"
  local logfile="${LOG_DIR}/${name}.log"

  # 已在运行则跳过（幂等）
  if [ -f "$pidfile" ] && kill -0 "$(cat "$pidfile")" 2>/dev/null; then
    log_info "${name} 已在运行（PID $(cat "$pidfile")）"
    return 0
  fi

  # nohup 后台启动，输出重定向到日志
  # shellcheck disable=SC2086  # $cmd 需要分词展开为完整命令
  nohup $cmd > "$logfile" 2>&1 &
  echo $! > "$pidfile"
  log_info "${name} 已启动（PID $(cat "$pidfile")），日志：${logfile}"
}

#------------------------------------------------------------------------------
# 等待端口就绪（最多 40 秒，Open WebUI 首次启动要建数据库，稍慢）
#------------------------------------------------------------------------------
wait_port() {
  local port="$1" name="$2" i
  for i in $(seq 1 40); do
    if curl -s --max-time 2 "http://127.0.0.1:${port}" >/dev/null 2>&1; then
      log_info "${name} 端口 ${port} 已就绪 ✅"
      return 0
    fi
    sleep 1
  done
  log_warn "${name} 端口 ${port} 未就绪，请查看日志：${LOG_DIR}/${name}.log"
  return 0  # 不阻塞启动流程
}

#------------------------------------------------------------------------------
# 启动两个服务
#------------------------------------------------------------------------------
start_service "open-webui" ".venv/bin/open-webui serve --host 0.0.0.0 --port ${PORT}"
start_service "editor"     ".venv/bin/python editor/server.py --host ${EDITOR_HOST:-127.0.0.1} --port ${EDITOR_PORT}"

wait_port "$PORT" "Open WebUI"
wait_port "$EDITOR_PORT" "代码编辑器"

log_info "容器内服务启动完成。"
