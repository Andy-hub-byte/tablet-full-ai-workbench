# 常见问题排障

## 目录

- [安装部署问题](#安装部署问题)
- [服务启动问题](#服务启动问题)
- [模型与推理问题](#模型与推理问题)
- [Open WebUI 使用问题](#open-webui-使用问题)
- [代码编辑器问题](#代码编辑器问题)
- [Android 系统问题](#android-系统问题)

---

## 安装部署问题

### Q1：`pkg install ollama` 提示找不到软件包

```bash
pkg update -y
pkg install -y tur-repo     # ollama 由 tur-repo 提供
pkg install -y ollama
```

### Q2：proot 容器安装失败 / 下载中断

```bash
proot-distro remove ubuntu        # 清理残留
proot-distro install ubuntu       # 重试
```

若网络不稳定，可先给 Termux 换源：`termux-change-repo`

### Q3：`pip install open-webui` 很慢或超时

容器内使用国内镜像源加速：

```bash
proot-distro login ubuntu --shared-tmp -- bash -lc '
  cd /root/workbench && . .venv/bin/activate
  pip install open-webui -i https://pypi.tuna.tsinghua.edu.cn/simple
'
```

### Q4：磁盘空间不足

```bash
df -h ~                          # 查看空间
ollama list                      # 删除不用的模型：ollama rm <模型名>
proot-distro login ubuntu -- apt-get clean
```

---

## 服务启动问题

### Q5：浏览器打不开 http://localhost:8080

按顺序排查：

```bash
bash scripts/status.sh           # 1. 看各服务状态
tail -50 ~/.tablet-workbench/logs/ollama.log          # 2. 看 Ollama 日志
proot-distro login ubuntu --shared-tmp -- tail -50 /root/.tablet-workbench/logs/open-webui.log
```

常见原因：

| 现象 | 原因 | 解决 |
|---|---|---|
| 端口被占用 | 旧进程未退 | `bash scripts/stop.sh` 后重启 |
| 服务未启动 | proot 会话退出 | 重新 `bash scripts/start.sh` |
| 显示 502/连接被拒 | Open WebUI 还在启动 | 等待 30 秒刷新 |

### Q6：端口被占用

```bash
# 查看 8080 被谁占用（Termux 侧）
ss -ltnp 2>/dev/null | grep 8080 || netstat -ltnp 2>/dev/null | grep 8080
bash scripts/stop.sh     # 用脚本清理全部服务进程
```

### Q7：Open WebUI 日志报 `Connection refused 11434`

Ollama 没启动或端口不对：

```bash
bash scripts/start.sh                    # 重新启动（会自动拉起 Ollama）
curl http://127.0.0.1:11434/api/version  # 单独验证 Ollama
```

确认 `.env` 中 `OLLAMA_BASE_URL=http://127.0.0.1:11434`。

---

## 模型与推理问题

### Q8：模型下载慢

Ollama 下载走的是 GitHub/官方 CDN，平板网络下较慢属正常。
可尝试：切换 Wi-Fi、避开高峰时段，或先用电脑下载 GGUF 再导入：

```bash
# 电脑下载 qwen1.5-1.8b 的 GGUF，传到平板后：
# 编辑 Modelfile：FROM /path/to/qwen1_5-1_8b-chat-q4_0.gguf
# ollama create qwen18b-local -f Modelfile
```

### Q9：推理很慢 / 平板发烫

- 1.8B 模型在平板 CPU 上速度约 3~10 tokens/s，属正常水平
- 发烫时可降低上下文：`ollama create` 时把 `PARAMETER num_ctx` 调小（如 4096）
- 不要同时运行多个模型（已默认限制 `OLLAMA_MAX_LOADED_MODELS=1`）
- 对话过长时点「新对话」，上下文越短越快

### Q10：提示内存不足（OOM）

```bash
free -h                          # 查看内存
ollama rm <大模型名>             # 换小模型
```

内存不够时优先选择 `qwen:0.5b` 或 `qwen:1.8b`。

### Q11：Agent 不调用工具 / 工具调用失败

- 1.8B 模型工具调用能力弱，请切换 `qwen2.5:3b` 及以上
- 确认对话界面「集成」中工具已勾选
- 确认工具已导入：管理员面板 → 工作区 → 工具，应显示 5 个工具且状态为启用

---

## Open WebUI 使用问题

### Q12：忘记管理员密码

```bash
# 容器内重置（会删除所有用户，需重新注册）
proot-distro login ubuntu --shared-tmp -- bash -lc '
  rm -f /root/.open-webui/webui.db
  bash /root/workbench/scripts/services-stop.sh
  bash /root/workbench/scripts/services-start.sh
'
```

### Q13：工具导入脚本失败（import-tools.py 报错）

脚本只是自动化手段，失败可完全手动导入：

1. 浏览器打开 Open WebUI → 管理员面板 → 工作区 → 工具
2. 点击「新建工具」
3. 打开项目 `webui/tools/` 下对应的 `.py` 文件，**复制全部内容**粘贴进去
4. 保存并启用

### Q14：Open WebUI 升级后主题失效

升级会覆盖前端文件，重新注入主题即可：

```bash
proot-distro login ubuntu --shared-tmp -- bash -lc '
  cd /root/workbench && bash scripts/patch-ui.sh
'
```

### Q15：其他设备访问不到 http://<平板IP>:8080

- 确认平板与其他设备在同一 Wi-Fi
- 确认 Ollama/Open WebUI 绑定的是 `0.0.0.0`（默认配置已满足）
- 部分路由器开启了 AP 隔离，需在路由器后台关闭
- 查看平板 IP：`bash scripts/status.sh`

---

## 代码编辑器问题

### Q16：编辑器页面空白 / 一直加载

- 检查服务：`bash scripts/status.sh`，确认 Code Studio 在运行
- 页面使用了 CDN 加载 CodeMirror，**首次打开需要联网**；
  离线打开会降级为纯文本框，功能不受影响
- 查看日志：容器内 `tail -50 /root/.tablet-workbench/logs/editor.log`

### Q17：C++ 运行提示找不到 g++

```bash
proot-distro login ubuntu --shared-tmp -- bash -lc 'g++ --version'
```

没安装则补装：

```bash
proot-distro login ubuntu --shared-tmp -- bash -lc 'apt-get update -y && apt-get install -y g++'
```

### Q18：AI 生成/解释按钮无反应

编辑器通过 Open WebUI 接口调用 AI：

1. 确认 Open WebUI 正在运行（:8080）
2. 在 Open WebUI 中创建 API Key：设置 → 账号 → API Keys
3. 编辑容器内 `/root/workbench/.env`，填入 `OWUI_TOKEN=<你的Key>`
4. 重启服务：`bash scripts/stop.sh && bash scripts/start.sh`

---

## Android 系统问题

### Q19：服务总被系统杀掉（最常见的坑！）

Android 对后台进程非常激进。务必完成以下设置：

1. **开发者选项** → 关闭「后台进程限制」/ 开启「不保留活动」相反的选项
   （不同品牌叫法不同：小米叫「省电策略 → 无限制」，华为叫「后台活动」）
2. Termux 通知栏**常驻**，并下拉通知获取「唤醒锁」
3. 系统电池优化中，将 Termux 设为「无限制」
4. 可选：安装 Termux:Widget / Termux:Boot 实现开机自启

临时维持：`termux-wake-lock`

### Q20：重启平板后服务没了

```bash
bash scripts/start.sh     # 重新启动全部服务
```

如需开机自启，安装 **Termux:Boot** 应用，然后：

```bash
mkdir -p ~/.termux/boot
cat > ~/.termux/boot/start-workbench.sh <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
termux-wake-lock
bash $HOME/tablet-full-ai-workbench/scripts/start.sh
EOF
chmod +x ~/.termux/boot/start-workbench.sh
```

### Q21：Termux 存储权限

```bash
termux-setup-storage       # 首次使用弹窗授权
```

授权后 `~/storage/downloads` 即为平板下载目录，
LoRA 适配器、备份文件通常放在这里。

---

## 仍有问题？

1. 收集日志：
   ```bash
   bash scripts/status.sh > ~/status.txt
   cp ~/.tablet-workbench/logs/*.log ~/
   proot-distro login ubuntu --shared-tmp -- cp /root/.tablet-workbench/logs/*.log /root/workbench/
   ```
2. 到本项目 GitHub Issues 页面提交问题，附上日志和平板型号
