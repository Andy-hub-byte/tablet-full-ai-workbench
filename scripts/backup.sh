#!/data/data/com.termux/files/usr/bin/bash
#===============================================================================
# 备份脚本（Termux 侧运行）
#-------------------------------------------------------------------------------
# 功能：备份工作台数据 —— Agent 数据（任务计划/长期记忆）、Open WebUI 数据库、
#       环境配置与 LoRA 导入记录
# 用法：bash scripts/backup.sh              # 标准备份
#       bash scripts/backup.sh --full       # 完整备份（含 Open WebUI 全部数据）
#       bash scripts/backup.sh --output ~/storage/downloads/   # 指定输出目录
#===============================================================================
set -euo pipefail

PROOT_DISTRO="ubuntu"
PROOT_WORKDIR="/root/workbench"
WB_TERMUX_DIR="${HOME}/.tablet-workbench"
STAMP="$(date +%Y%m%d_%H%M%S)"

RED=$'\e[31m'; GREEN=$'\e[32m'; YELLOW=$'\e[33m'; BOLD=$'\e[1m'; RESET=$'\e[0m'
log_info() { echo -e "${GREEN}[信息]${RESET} $*"; }
log_warn() { echo -e "${YELLOW}[提示]${RESET} $*"; }
die()     { echo -e "${RED}[错误]${RESET} $*" >&2; exit 1; }

#------------------------------------------------------------------------------
# 参数解析
#------------------------------------------------------------------------------
FULL=false
OUTPUT_DIR="${HOME}/storage/downloads"
[ -d "$OUTPUT_DIR" ] || OUTPUT_DIR="${HOME}"   # 存储未授权时退回 HOME

while [ $# -gt 0 ]; do
  case "$1" in
    --full)   FULL=true; shift ;;
    --output) OUTPUT_DIR="$2"; shift 2 ;;
    *) die "未知参数：$1（支持 --full / --output <目录>）" ;;
  esac
done

[ -n "${PREFIX:-}" ] || die "请在 Termux 中运行本脚本。"
mkdir -p "$OUTPUT_DIR"
BACKUP_FILE="${OUTPUT_DIR}/workbench-backup-${STAMP}.tar.gz"

#------------------------------------------------------------------------------
# 组装备份内容
#   说明：容器内路径通过 proot rootfs 直接从 Termux 侧打包
#   （rootfs 就在 Termux 文件系统内，路径见 PROOT_ROOTFS）
#------------------------------------------------------------------------------
PROOT_ROOTFS="${PREFIX}/var/lib/proot-distro/installed-rootfs/${PROOT_DISTRO}"

log_info "正在创建备份：${BACKUP_FILE}"

# 基础备份项（始终包含）
ITEMS=()
# 1. Agent 数据：任务计划、长期记忆
[ -d "${PROOT_ROOTFS}/root/.tablet-workbench/data" ] && ITEMS+=("-C" "${PROOT_ROOTFS}/root/.tablet-workbench" "data")
# 2. 工作台配置：.env、Modelfile 等（不含 .venv 大目录）
[ -d "${PROOT_ROOTFS}/root/workbench" ] && ITEMS+=("-C" "${PROOT_ROOTFS}/root/workbench" ".env" "webui" "ollama" "agent")
# 3. Termux 侧 Ollama 配置与日志目录结构
[ -d "${WB_TERMUX_DIR}" ] && ITEMS+=("-C" "${WB_TERMUX_DIR}" "run")

# 完整备份：追加 Open WebUI 数据库与上传文件（含聊天记录、知识库）
if [ "$FULL" = true ] && [ -d "${PROOT_ROOTFS}/root/.open-webui" ]; then
  ITEMS+=("-C" "${PROOT_ROOTFS}/root" ".open-webui")
  log_info "完整备份模式：包含 Open WebUI 全部数据（聊天记录 / 知识库）"
fi

[ ${#ITEMS[@]} -gt 0 ] || die "没有找到可备份的数据（是否尚未执行 install.sh？）"

# 模型清单也备份一份（恢复时可按清单重新拉取模型，模型文件本身太大不打包）
ollama list > "${WB_TERMUX_DIR}/models_${STAMP}.txt" 2>/dev/null || true
ITEMS+=("-C" "${WB_TERMUX_DIR}" "models_${STAMP}.txt")

# shellcheck disable=SC2068  # ITEMS 需要分词展开
tar -czf "$BACKUP_FILE" ${ITEMS[@]} 2>/dev/null || tar -czf "$BACKUP_FILE" -C /tmp 2>/dev/null || die "打包失败"

SIZE_MB=$(( $(stat -c%s "$BACKUP_FILE" 2>/dev/null || stat -f%z "$BACKUP_FILE") / 1024 / 1024 ))
echo
echo -e "${BOLD}==================== 备份完成 ====================${RESET}"
echo "  文件：${BACKUP_FILE}"
echo "  大小：约 ${SIZE_MB}MB"
echo
echo "  恢复命令：bash scripts/restore.sh ${BACKUP_FILE}"
log_warn "建议定期把备份文件拷贝到电脑或网盘保存。"
echo -e "${BOLD}===================================================${RESET}"
