#!/data/data/com.termux/files/usr/bin/bash
#===============================================================================
# 服务状态查看脚本（Termux 侧）
#-------------------------------------------------------------------------------
# 功能：查看各服务运行状态、已安装模型、存储占用与局域网访问地址
# 用法：bash scripts/status.sh
#===============================================================================
set -uo pipefail   # 注意：不使用 -e，状态查看允许单项失败

PROOT_DISTRO="ubuntu"
PROOT_WORKDIR="/root/workbench"
OWUI_PORT="${OWUI_PORT:-8080}"
EDITOR_PORT="${EDITOR_PORT:-8899}"

GREEN=$'\e[32m'; RED=$'\e[31m'; YELLOW=$'\e[33m'; BLUE=$'\e[34m'; BOLD=$'\e[1m'; RESET=$'\e[0m'

# 检查端口是否可访问：返回 0 表示正常
check_port() { curl -s --max-time 3 "http://127.0.0.1:$1" >/dev/null 2>&1; }

echo -e "${BOLD}${BLUE}==================== 平板 AI 工作台状态 ====================${RESET}"
echo "时间：$(date '+%Y-%m-%d %H:%M:%S')"

#------------------------------------------------------------------------------
# 1. Ollama 服务
#------------------------------------------------------------------------------
if curl -s --max-time 3 "http://127.0.0.1:11434/api/version" >/dev/null 2>&1; then
  VERSION="$(curl -s --max-time 3 http://127.0.0.1:11434/api/version | grep -o '"version":"[^"]*"' | cut -d'"' -f4)"
  echo -e "  Ollama        : ${GREEN}● 运行中${RESET}（版本 ${VERSION:-未知}，端口 11434）"
else
  echo -e "  Ollama        : ${RED}○ 未运行${RESET}（执行 bash scripts/start.sh 启动）"
fi

#------------------------------------------------------------------------------
# 2. Open WebUI
#------------------------------------------------------------------------------
if check_port "$OWUI_PORT"; then
  echo -e "  Open WebUI    : ${GREEN}● 运行中${RESET}（端口 ${OWUI_PORT}，http://localhost:${OWUI_PORT}）"
else
  echo -e "  Open WebUI    : ${RED}○ 未运行${RESET}"
fi

#------------------------------------------------------------------------------
# 3. 代码编辑器
#------------------------------------------------------------------------------
if check_port "$EDITOR_PORT"; then
  echo -e "  代码编辑器    : ${GREEN}● 运行中${RESET}（端口 ${EDITOR_PORT}，http://localhost:${EDITOR_PORT}）"
else
  echo -e "  代码编辑器    : ${RED}○ 未运行${RESET}"
fi

#------------------------------------------------------------------------------
# 4. 已安装模型
#------------------------------------------------------------------------------
if command -v ollama >/dev/null 2>&1; then
  MODELS="$(ollama list 2>/dev/null | tail -n +2 | awk '{printf "%-28s %s\n", $1, $3}')"
  if [ -n "$MODELS" ]; then
    echo
    echo "  已安装模型："
    echo "$MODELS" | while read -r line; do echo "    · $line"; done
  else
    echo
    echo -e "  已安装模型：${YELLOW}（无，可用 ollama pull qwen:1.8b 下载）${RESET}"
  fi
fi

#------------------------------------------------------------------------------
# 5. 存储与内存
#------------------------------------------------------------------------------
echo
MEM_TOTAL="$(awk '/MemTotal/{print int($2/1024)}' /proc/meminfo)"
MEM_AVAIL="$(awk '/MemAvailable/{print int($2/1024)}' /proc/meminfo)"
DISK_AVAIL=$(( $(df -k "$HOME" | awk 'NR==2{print $4}') / 1024 ))
echo "  内存：已用 $((MEM_TOTAL - MEM_AVAIL))MB / 共 ${MEM_TOTAL}MB"
echo "  存储：剩余约 ${DISK_AVAIL}MB"

#------------------------------------------------------------------------------
# 6. 局域网访问地址
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
echo "  局域网访问（多人房间）：http://${LAN_IP}:${OWUI_PORT}"

#------------------------------------------------------------------------------
# 7. 日志位置提示
#------------------------------------------------------------------------------
echo
echo "  日志位置："
echo "    · Ollama       : ~/.tablet-workbench/logs/ollama.log"
echo "    · Open WebUI   : 容器内 /root/.tablet-workbench/logs/open-webui.log"
echo "    · 代码编辑器   : 容器内 /root/.tablet-workbench/logs/editor.log"
echo -e "${BOLD}${BLUE}=========================================================${RESET}"
