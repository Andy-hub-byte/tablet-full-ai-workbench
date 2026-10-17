#!/data/data/com.termux/files/usr/bin/bash
#===============================================================================
# 恢复脚本（Termux 侧运行）
#-------------------------------------------------------------------------------
# 功能：从备份文件恢复工作台数据（Agent 数据、Open WebUI 数据库、配置等）
# 用法：bash scripts/restore.sh <备份文件路径>
# 注意：恢复前建议先执行 bash scripts/stop.sh 停止服务，避免数据写坏
#===============================================================================
set -euo pipefail

PROOT_DISTRO="ubuntu"
PROOT_ROOTFS="${PREFIX:-/nonexistent}/var/lib/proot-distro/installed-rootfs/${PROOT_DISTRO}"
WB_TERMUX_DIR="${HOME}/.tablet-workbench"

RED=$'\e[31m'; GREEN=$'\e[32m'; YELLOW=$'\e[33m'; BOLD=$'\e[1m'; RESET=$'\e[0m'
log_info() { echo -e "${GREEN}[信息]${RESET} $*"; }
log_warn() { echo -e "${YELLOW}[提示]${RESET} $*"; }
die()     { echo -e "${RED}[错误]${RESET} $*" >&2; exit 1; }

#------------------------------------------------------------------------------
# 参数检查
#------------------------------------------------------------------------------
[ $# -ge 1 ] || die "用法：bash scripts/restore.sh <备份文件路径>"
BACKUP_FILE="$1"
[ -f "$BACKUP_FILE" ] || die "备份文件不存在：${BACKUP_FILE}"
[ -n "${PREFIX:-}" ] || die "请在 Termux 中运行本脚本。"

log_warn "恢复会覆盖当前的工作台数据，建议先备份现有数据。"
read -r -p "确认恢复？(y/N) " ans
[ "$ans" = "y" ] || [ "$ans" = "Y" ] || die "已取消恢复。"

#------------------------------------------------------------------------------
# 解压到目标位置
#   备份包内的相对路径与打包时一致：
#     data/            -> 容器 /root/.tablet-workbench/data/（Agent 数据）
#     .env webui/...   -> 容器 /root/workbench/（项目配置）
#     models_*.txt     -> Termux ~/.tablet-workbench/（模型清单）
#------------------------------------------------------------------------------
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

log_info "正在解压备份……"
tar -xzf "$BACKUP_FILE" -C "$TMP_DIR"

# 1. Agent 数据（任务计划 / 长期记忆）-> 容器内
if [ -d "${TMP_DIR}/data" ]; then
  mkdir -p "${PROOT_ROOTFS}/root/.tablet-workbench"
  cp -r "${TMP_DIR}/data" "${PROOT_ROOTFS}/root/.tablet-workbench/"
  log_info "已恢复 Agent 数据（任务计划 / 长期记忆）"
fi

# 2. 项目配置（.env 等）-> 容器内工作台目录
if [ -d "${PROOT_ROOTFS}/root/workbench" ]; then
  [ -f "${TMP_DIR}/.env" ] && cp "${TMP_DIR}/.env" "${PROOT_ROOTFS}/root/workbench/.env"
  for d in webui ollama agent; do
    [ -d "${TMP_DIR}/${d}" ] && cp -r "${TMP_DIR}/${d}" "${PROOT_ROOTFS}/root/workbench/"
  done
  log_info "已恢复项目配置（.env / webui / ollama / agent）"
fi

# 3. Open WebUI 完整数据（完整备份才有）
if [ -d "${TMP_DIR}/.open-webui" ]; then
  mkdir -p "${PROOT_ROOTFS}/root"
  cp -r "${TMP_DIR}/.open-webui" "${PROOT_ROOTFS}/root/"
  log_info "已恢复 Open WebUI 完整数据（聊天记录 / 知识库）"
fi

# 4. 模型清单 -> Termux 侧
for f in "${TMP_DIR}"/models_*.txt; do
  [ -f "$f" ] && cp "$f" "${WB_TERMUX_DIR}/" && log_info "已恢复模型清单：$(basename "$f")（可按清单用 ollama pull 重新下载模型）"
done

echo
echo -e "${BOLD}==================== 恢复完成 ====================${RESET}"
log_info "请执行 bash scripts/start.sh 重新启动服务。"
echo -e "${BOLD}===================================================${RESET}"
