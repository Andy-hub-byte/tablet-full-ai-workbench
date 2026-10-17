#!/usr/bin/env bash
#===============================================================================
# 触屏主题注入脚本（proot Ubuntu 容器内部运行）
#-------------------------------------------------------------------------------
# 功能：把 webui/custom.css 内联注入 Open WebUI 前端 index.html
# 特点：幂等（已有标记则跳过）；注入前自动备份原文件
# 注意：升级 Open WebUI 后前端文件被覆盖，需重新运行本脚本
#===============================================================================
set -euo pipefail

WORKDIR="/root/workbench"
cd "$WORKDIR"

GREEN=$'\e[32m'; YELLOW=$'\e[33m'; RED=$'\e[32m'; RESET=$'\e[0m'
log_info() { echo -e "${GREEN}[主题]${RESET} $*"; }
log_warn() { echo -e "${YELLOW}[主题]${RESET} $*"; }

#------------------------------------------------------------------------------
# 1. 定位 Open WebUI 前端目录（在虚拟环境的 site-packages 内）
#------------------------------------------------------------------------------
[ -x ".venv/bin/python" ] || { echo "未找到虚拟环境，请先执行安装脚本" >&2; exit 1; }
FRONTEND_DIR="$(.venv/bin/python -c 'import open_webui, os; print(os.path.join(os.path.dirname(open_webui.__file__), "frontend"))')"
INDEX_FILE="${FRONTEND_DIR}/index.html"

if [ ! -f "$INDEX_FILE" ]; then
  log_warn "未找到前端文件：${INDEX_FILE}（Open WebUI 可能未安装）"
  exit 1
fi
log_info "前端文件：${INDEX_FILE}"

#------------------------------------------------------------------------------
# 2. 幂等检查：已注入则跳过
#------------------------------------------------------------------------------
MARKER="workbench-touch-theme"
if grep -q "$MARKER" "$INDEX_FILE"; then
  log_info "触屏主题已注入，跳过（升级 Open WebUI 后会自动失效，届时重跑本脚本即可）"
  exit 0
fi

#------------------------------------------------------------------------------
# 3. 备份原文件（仅首次）
#------------------------------------------------------------------------------
[ -f "${INDEX_FILE}.bak" ] || cp "$INDEX_FILE" "${INDEX_FILE}.bak"
log_info "已备份原文件：${INDEX_FILE}.bak"

#------------------------------------------------------------------------------
# 4. 用 Python 安全地把 CSS 内联进 </head> 之前
#    （用 Python 而非 sed，避免 CSS 中的特殊字符被 sed 误解析）
#------------------------------------------------------------------------------
.venv/bin/python - "$INDEX_FILE" "$MARKER" <<'PYEOF'
import sys

index_path, marker = sys.argv[1], sys.argv[2]
css_path = "/root/workbench/webui/custom.css"

with open(css_path, encoding="utf-8") as f:
    css = f.read()
with open(index_path, encoding="utf-8") as f:
    html = f.read()

# 注入内容：标记注释 + 内联样式（这样无需额外托管静态文件）
inject = f"<!-- {marker} -->\n<style>\n{css}\n</style>\n<!-- /{marker} -->"

if "</head>" in html:
    html = html.replace("</head>", inject + "</head>", 1)
else:
    html = inject + html

with open(index_path, "w", encoding="utf-8") as f:
    f.write(html)
print("触屏主题注入成功 ✅")
PYEOF

log_info "完成。刷新浏览器页面即可看到触屏优化效果。"
