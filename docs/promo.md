# 社区宣传文案 · Community Promotion Copy

> 适用于掘金、HelloGitHub、GitHub 社区、V2EX 等平台的推广文案，中英双语。
> 使用时请把 `[链接]` 替换为实际地址（仓库 / 演示站）。

---

## 一、掘金版（中文长文）

### 标题（三选一）

1. 我把音乐播放器、代码编辑器和 AI 助手塞进了一个 HTML 文件，76KB，离线可用
2. 零依赖单文件工具箱：手机、平板、电脑打开即用，AI 还能帮你记事和定时
3. 告别装软件！这个网页工具箱把 5 个常用工具合体了，数据还不出浏览器

### 正文

> 不知道你有没有这种经历：想听本地音乐要装播放器，想写两行代码要开 IDE，想记个事要翻备忘录，想定时要找个闹钟 App……工具越装越多。
>
> 于是我做了 **Full AI Workbench（tablet-full-ai-workbench）**：一个网页，装下整个工具箱。

**它有什么？**

- 🎵 **音乐播放器**：上传本地音频（支持拖拽），歌单管理、进度拖动、音量调节、三种播放模式，手机端还有锁屏控制。没有音频文件？点一下「演示音轨」，浏览器实时合成一段给你试听。
- 💻 **C++ 代码编辑器**：语法高亮、行号、Tab 缩进、Enter 自动对齐，最贴心的是给平板做了**符号键盘**，括号分号一键插入，妈妈再也不用担心我在平板上打代码找符号了。
- 🤖 **AI 聊天助手（带 Agent 能力）**：可以接任意 OpenAI 兼容接口，包括本机 Ollama / LM Studio 离线模型。重点是它不只是聊天——它能**直接操作工具箱**：帮你写记事本、设倒计时、放音乐、切换界面、报时。每次工具调用都明明白白展示在对话里。
- 📝 **记事本**：自动保存，刷新不丢，一键导出 txt。
- ⏱️ **计时器**：倒计时 + 正计时，番茄钟预设，结束有提示音，剩余时间同步到浏览器标签标题。

**它没有什么？**

- 没有服务器 —— 所有功能都在浏览器本地跑；
- 没有安装 —— `index.html` 双击就能用；
- 没有依赖 —— 零框架、零构建、零外部请求，断网也能用（AI 聊天除外）；
- 没有上传 —— 你的文件和 API Key 都只待在你自己的浏览器里。

**技术上的几个小亮点**

- 整个应用就是一个 76KB 的 HTML 文件，代码全中文注释，方便二次开发；
- 语法高亮、WAV 演示音轨、提示音全是**运行时实时生成**的，仓库里没有任何大文件；
- AI 工具调用同时支持原生 Function Calling 和「```tool JSON 代码块」回退协议，本地小模型也能用；
- 深色 / 浅色模式、响应式布局，手机 / 安卓平板 / 电脑全适配。

**试试看**

- 在线演示：[链接]
- 仓库地址：[链接]（觉得好用欢迎点个 ⭐ Star）

MIT 开源，欢迎来玩。

### 标签建议

`前端` `JavaScript` `开源` `效率工具` `AI` `HTML5` `GitHub`

---

## 二、HelloGitHub 投稿格式

> HelloGitHub 投稿模板（monthly/月刊或月度收录）：按其官网要求填写以下内容。

- **项目名称**：tablet-full-ai-workbench（Full AI Workbench · 全功能 AI 网页工具箱）
- **项目地址**：`https://github.com/Andy-hub-byte/tablet-full-ai-workbench`
- **在线演示**：`https://andy-hub-byte.github.io/tablet-full-ai-workbench/`
- **一句话简介**：一个网页装下整个工具箱——音乐播放器、C++ 代码编辑器、AI 助手（Agent）、记事本、计时器，纯浏览器运行，离线可用。
- **项目简介**：
  Full AI Workbench 是一个**零依赖的单文件网页工具箱**。整个应用只有一个 `index.html`（约 76KB），双击即可在浏览器运行，无需安装、无需服务器，手机 / 安卓平板 / 电脑通用。功能包括：本地音乐播放器（歌单管理、进度拖动、音量调节、深色模式）、C++ 代码编辑器（语法高亮、触屏符号键盘）、带 Agent 能力的 AI 聊天（可接入本地 Ollama / LM Studio 离线模型，AI 能直接操作工具箱的记事本、计时器、播放器）、自动保存的记事本和带提示音的计时器。所有数据不出浏览器。
- **推荐理由**：
  1. **真正零依赖**：不引框架、不构建、不请求外部资源，断网可用，源码全中文注释，非常适合前端初学者阅读和二次开发；
  2. **单文件交付**：一个 HTML 文件就是完整应用，拷贝即用，部署到任何静态托管都只要一秒；
  3. **AI 不只是聊天**：内置 7 个工具，AI 可以直接帮用户写记事本、设闹钟、放音乐，工具调用过程透明可见；
  4. **平板触屏友好**：代码编辑器带符号键盘，播放器 / 计时器大按钮设计，安卓平板上体验良好；
  5. **仓库干净**：无大文件，截图和演示音轨均运行时生成，clone 秒完成。
- **项目截图**：`docs/screenshots/` 目录（音乐播放器、代码编辑器、AI 聊天、记事本、计时器、浅色模式）

---

## 三、V2EX / 短平快版

**标题**：单文件网页工具箱——音乐播放器 + C++ 编辑器 + AI Agent + 记事本 + 计时器，76KB 离线可用

**正文**：

做了个纯前端小工具集合，一个 HTML 文件搞定，双击就能用：

- 音乐播放器（本地上传/拖拽、进度音量、播放模式）
- C++ 编辑器（高亮、行号、平板符号键盘）
- AI 聊天（OpenAI 兼容，可接本地 Ollama，带工具调用能直接操作其他模块）
- 记事本（自动保存）、计时器（倒计时+正计时）

零依赖零构建，数据不出浏览器，深浅色模式。演示：[链接] 源码：[链接]（MIT）

---

## 四、GitHub 社区 / Discussions 英文版（Show and tell）

**Title**: Full AI Workbench — a single-file browser toolbox with an AI agent inside (76KB, zero dependencies)

**Body**:

Hi everyone! I built **Full AI Workbench** — a browser toolbox packed into a single `index.html` file (~76KB, no dependencies, no build step, works offline).

**What's inside**

- 🎵 Music player: local audio upload (drag & drop), playlist, draggable progress, volume, loop/shuffle, lock-screen media controls — plus a demo track synthesized in-browser when you have no files
- 💻 C++ code editor: syntax highlighting, line numbers, auto-indent, and an on-screen symbol keyboard designed for tablets
- 🤖 AI chat with real agent skills: works with any OpenAI-compatible endpoint (including local Ollama / LM Studio offline models). The AI can actually operate the toolbox — write notes, set timers, play music, switch screens. Every tool call is shown transparently in the conversation
- 📝 Notepad with auto-save and .txt export
- ⏱️ Timer with countdown presets, stopwatch mode, and a synthesized chime (no audio files in the repo)

**Why I built it this way**

Everything runs locally in the browser — no server, no uploads, no accounts. Syntax highlighting, the demo WAV, and the chime are all generated at runtime, so the repo stays tiny. All comments are in Chinese (my primary audience), but the README and docs are fully bilingual.

**Try it**

- Live demo: [link]
- Repo: [link] — MIT licensed, stars and PRs very welcome ⭐

I'd love feedback, especially on the agent tool-calling flow with local models!

---

## 五、Twitter / X 短文案（中英各一）

**中文**：

做了个单文件网页工具箱 🧰 一个 HTML（76KB）装下：音乐播放器 / C++ 编辑器（带平板符号键盘）/ AI 助手（能直接帮你记事、定时、放歌）/ 记事本 / 计时器。零依赖、离线可用、数据不出浏览器。演示 👉 [链接] 源码 👉 [链接] #开源 #前端 #AI

**English**:

Built a whole toolbox in one HTML file (76KB, zero deps, offline-capable) 🧰 Music player · C++ editor with a tablet symbol keyboard · AI chat agent that can actually write your notes, set timers and play music · notepad · timer. Demo 👉 [link] Repo 👉 [link] #opensource #webdev #AI

---

## 发布小贴士

1. **配图**：用 `docs/screenshots/` 里的截图，掘文建议 3~4 张（音乐、代码、AI 聊天必带）；
2. **时机**：掘金工作日早上 9~10 点发布流量较好；
3. **互动**：发布后 1 小时内回复评论，有助于推荐权重；
4. **HelloGitHub**：每月在其官网"投稿"入口提交，命中率较高的是"有新意的小工具"类；
5. 所有文案中的 `[链接]` 记得替换成真实地址。
