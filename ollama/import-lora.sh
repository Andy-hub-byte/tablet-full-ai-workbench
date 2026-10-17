#!/data/data/com.termux/files/usr/bin/bash
#===============================================================================
# LoRA 微调模型一键导入脚本（Termux 侧运行）
#-------------------------------------------------------------------------------
# 功能：交互式引导用户导入 LoRA 适配器，自动生成 Modelfile 并创建 Ollama 模型
# 用法：bash ollama/import-lora.sh
#===============================================================================
set -euo pipefail

#------------------------------------------------------------------------------ 颜色与日志
GREEN=$'\e[32m'; YELLOW=$'\e[33m'; RED=$'\e[31m'; BLUE=$'\e[34m'; BOLD=$'\e[1m'; RESET=$'\e[0m'
log_info() { echo -e "${GREEN}[信息]${RESET} $*"; }
log_warn() { echo -e "${YELLOW}[提示]${RESET} $*"; }
log_err()  { echo -e "${RED}[错误]${RESET} $*" >&2; }
die()     { log_err "$*"; exit 1; }

#------------------------------------------------------------------------------ 检查环境
[ -n "${PREFIX:-}" ] || die "请在 Termux 中运行本脚本。"
command -v ollama >/dev/null 2>&1 || die "未检测到 ollama，请先运行 scripts/install.sh 完成部署。"

ADAPTER_DIR="$HOME/tablet-full-ai-workbench/ollama/adapters"
mkdir -p "$ADAPTER_DIR"

echo -e "\n${BOLD}${BLUE}========== LoRA 自定义模型导入向导 ==========${RESET}"
log_info "适配器目录：$ADAPTER_DIR"
log_warn "请先把 LoRA 适配器文件（.gguf 或 safetensors 目录）放到上面目录，"
log_warn "可以先用 cp ~/storage/downloads/xxx.gguf $ADAPTER_DIR/ 拷贝过来。"

#------------------------------------------------------------------------------ 收集信息
echo
read -r -p "1. 适配器文件名（相对 $ADAPTER_DIR，如 my-lora.gguf）: " ADAPTER_NAME
[ -n "$ADAPTER_NAME" ] || die "适配器文件名不能为空。"
ADAPTER_PATH="$ADAPTER_DIR/$ADAPTER_NAME"
[ -e "$ADAPTER_PATH" ] || die "找不到文件：$ADAPTER_PATH，请检查路径。"

read -r -p "2. 基础模型（默认 qwen:1.8b，必须与微调时一致）: " BASE_MODEL
BASE_MODEL="${BASE_MODEL:-qwen:1.8b}"

read -r -p "3. 新模型名称（如 my-coder）: " MODEL_NAME
[ -n "$MODEL_NAME" ] || die "模型名称不能为空。"

#------------------------------------------------------------------------------ 生成 Modelfile 并创建模型
log_info "正在生成 Modelfile 并创建模型「$MODEL_NAME」（约需几十秒）……"

TMP_MODELFILE="$(mktemp)"
cat > "$TMP_MODELFILE" <<EOF
FROM $BASE_MODEL
ADAPTER $ADAPTER_PATH
PARAMETER num_ctx 8192
PARAMETER temperature 0.7
EOF

if ! ollama list | awk '{print $1}' | grep -qx "$BASE_MODEL"; then
  log_warn "本地还没有基础模型 $BASE_MODEL，正在下载（约 1.1GB）……"
  ollama pull "$BASE_MODEL"
fi

ollama create "$MODEL_NAME" -f "$TMP_MODELFILE"
rm -f "$TMP_MODELFILE"

#------------------------------------------------------------------------------ 完成提示
echo
log_info "模型「$MODEL_NAME」创建成功！"
echo
echo -e "${BOLD}后续操作：${RESET}"
echo "  · 测试对话：ollama run $MODEL_NAME"
echo "  · 查看适配器是否生效：ollama run $MODEL_NAME 后输入 /show info"
echo "  · 在 Open WebUI 模型列表中即可直接选择「$MODEL_NAME」使用"
echo
log_warn "提醒：适配器必须与基础模型同架构同基座，否则输出会混乱。"
