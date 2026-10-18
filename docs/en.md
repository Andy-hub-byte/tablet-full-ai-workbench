# Full AI Workbench — English Guide

> One web page with a whole toolbox inside: music player, C++ code editor, AI chat agent, notepad, and timer.
> Runs entirely in your browser — no install, no server, works offline.
>
> - Live demo: <https://andy-hub-byte.github.io/tablet-full-ai-workbench/>
> - Repository: <https://github.com/Andy-hub-byte/tablet-full-ai-workbench>

---

## Table of contents

1. [Getting started in three minutes](#1-getting-started-in-three-minutes)
2. [The music player, in depth](#2-the-music-player-in-depth)
3. [The code editor, in depth](#3-the-code-editor-in-depth)
4. [AI chat and agent skills](#4-ai-chat-and-agent-skills)
5. [The notepad](#5-the-notepad)
6. [The timer](#6-the-timer)
7. [Tips for tablets and phones](#7-tips-for-tablets-and-phones)
8. [Deployment](#8-deployment)
9. [Developer guide](#9-developer-guide)
10. [Troubleshooting quick reference](#10-troubleshooting-quick-reference)

---

## 1. Getting started in three minutes

### 1.1 Pick a way to open it

| Method | What to do | Best for |
|---|---|---|
| Live demo | Visit <https://andy-hub-byte.github.io/tablet-full-ai-workbench/> | Trying it right now |
| Single file | Download `index.html` and open it | Offline use / sharing with friends |
| Clone the repo | `git clone`, then open `index.html` (or run `python3 -m http.server 8000`) | Development |

All three are functionally identical. The entire app is one HTML file with zero external requests, so it keeps working with your Wi-Fi off (the AI chat module still needs to reach whatever model endpoint you configure).

### 1.2 A quick tour

- Top navigation: 🎵 Music / 💻 Code / 🤖 AI Chat / 📝 Notepad / ⏱️ Timer — tap to switch;
- Top right: ⭐ jumps to the GitHub repo; 🌙 / ☀️ toggles dark / light mode (your choice is remembered).

---

## 2. The music player, in depth

### 2.1 Adding music

Three ways, take your pick:

1. Click **＋ Upload audio** and multi-select local files;
2. **Drag and drop** audio files straight onto the playlist panel;
3. No files on hand? Click **🎶 Demo track** and the app will *synthesize* a short WAV tune in your browser (about 8 seconds) so you can try everything out.

MP3 / WAV / OGG / FLAC / M4A / AAC and anything else your browser can decode are supported.

### 2.2 Playback controls

| Action | What it does |
|---|---|
| Tap a playlist row | Plays that track; tapping the currently playing row toggles pause / resume |
| ⏮ / ⏭ | Previous / next track |
| ▶ / ⏸ big round button | Play / pause |
| Progress bar | **Press and drag** to seek (touch friendly) |
| 🔊 icon + slider | Mute toggle and volume |
| 🔁 / 🔂 / 🔀 | Cycles play mode: list loop → single loop → shuffle |

While a track plays, its playlist row shows an animated equalizer and the cover art gently pulses.

### 2.3 Other capabilities

- **Lock-screen / system media controls**: on phones, playback controls appear on the lock screen and in notifications (via the Media Session API);
- **Remove a track**: tap the ✕ on the right of a playlist row;
- **An empty playlist after refresh is expected**: browsers don't allow a web page to write local files to disk, and nothing is ever uploaded. Just re-add files after a refresh (text data like notes is unaffected).

---

## 3. The code editor, in depth

### 3.1 The basics

- **Syntax highlighting** for C++ and C, rendered live as you type;
- **Line numbers** in the left gutter, synced with scrolling;
- **Tab indent**: Tab inserts two spaces; pressing Enter after `{`, `(`, `:` or `[` adds one more indent level automatically;
- **Font size**: `A−` / `A＋` buttons (11px – 22px);
- **Template / Copy / Download / Clear**: one-tap tools in the toolbar; downloads come out as `.cpp`.

### 3.2 The on-screen symbol keyboard (the tablet feature)

Click **⌨️ Symbol keyboard** to reveal 33 large buttons: `{ } ( ) [ ] ; : , . " ' = + - * / % < > ! & | ^ ~ # \ _ @ ? $`, plus Tab and Space.

- Tapping a bracket inserts the **pair** with the cursor parked between them;
- If you've selected text first, the selection gets wrapped instead;
- Click **⌨️ Symbol keyboard** (now labeled "收起键盘" / collapse) again to hide it.

> This exists because typing C++ symbols on a tablet with a system keyboard is genuinely painful.

### 3.3 Keyboard shortcuts and tricks

| Input | Effect |
|---|---|
| `Tab` | Insert indent (two spaces) |
| `Enter` | New line, auto-aligned to the previous line's indent |
| `Shift + Enter` | Plain newline, no auto-indent |
| "Insert template" | Fills in a sample C++ program (commented, good for testing highlighting) |

---

## 4. AI chat and agent skills

### 4.1 What this module is

An **AI chat window that runs in your browser**. It connects to any OpenAI-compatible endpoint, including:

- A local **Ollama** server (fully offline — recommended);
- A local **LM Studio** server (offline);
- Any OpenAI-compatible cloud API (bring your own key).

What makes it different from an ordinary chat box is the **agent layer**: the model can call built-in tools and *actually operate the toolbox*.

### 4.2 Configuring a model (30 seconds)

1. Click **⚙️ Model settings** at the top right of the chat panel;
2. Tap a preset to auto-fill (or type your own):

| Preset | Base URL | API Key | Example model |
|---|---|---|---|
| 🖥 Local Ollama | `http://localhost:11434/v1` | anything, e.g. `ollama` | `qwen2.5:3b` |
| 🖥 LM Studio | `http://localhost:1234/v1` | anything, e.g. `lm-studio` | `local-model` |
| ☁️ OpenAI-compatible | `https://api.openai.com/v1` | your real key | `gpt-4o-mini` |

3. Optionally click **🔍 Fetch models** to list what's available;
4. Click **💾 Save settings** and start chatting.

> Everything you enter is stored only in your own browser's localStorage. Nothing passes through any middle server.

### 4.3 Full local example with Ollama

```bash
# 1. After installing Ollama (https://ollama.com):
ollama pull qwen2.5:3b     # download a model (~2GB; swap in gemma3, qwen3, etc. if you like)
ollama serve               # starts the server on port 11434

# 2. In the toolbox → AI Chat → Model settings:
#    Base URL: http://localhost:11434/v1
#    API Key : ollama (any non-empty string works)
#    Model   : qwen2.5:3b
```

Recent Ollama versions support function calling natively, so tool calls go over the standard protocol. For older versions or smaller models that don't, the app automatically falls back to a "```tool JSON block" protocol (the rules are baked into the default system prompt). Both paths are built in.

### 4.4 The agent toolset

| Tool | Parameters | Effect |
|---|---|---|
| `notepad_write` | `content` | Overwrite the notepad with content |
| `notepad_read` | — | Read the current notepad contents |
| `timer_start` | `seconds`, `label` | Start a countdown and announce it |
| `music_play` | `query` | Play a track by name keyword |
| `music_control` | `pause` / `resume` / `next` / `prev` | Pause, resume, skip tracks |
| `switch_app` | `music` / `code` / `chat` / `notes` / `timer` | Jump to another module |
| `get_current_time` | — | Return the current date and time |

### 4.5 Things to try

- "Add a grocery list for the weekend to my notepad"
- "Remind me to drink water in 5 minutes"
- "Play the first song in my playlist"
- "What time is it? Also write today's date into the notepad"
- "Switch to the timer and set a 25-minute pomodoro"

Every tool call shows up as a dashed bubble with the **tool name, arguments, and result**, so the agent's actions stay fully transparent.

### 4.6 Want to see it without a model?

Open the page, press `F12`, and run this in the console:

```js
TFAW.seedChatDemo()
```

You'll get a scripted conversation showing the full "user asks → three tool calls → summary" flow, no API key required.

### 4.7 Generation controls

- `Enter` sends, `Shift + Enter` adds a newline (IME-friendly);
- Hit **⏹ Stop** to interrupt generation;
- **Clear conversation** wipes the visible messages and the context history.

---

## 5. The notepad

- **Auto-save**: writes to localStorage about 0.4s after you stop typing — refreshing or closing the browser won't lose it;
- **Character count** in the bottom-left corner;
- **Export .txt**: one click, filename includes a timestamp;
- **Clear**: asks for confirmation;
- Heads-up: private/incognito mode or clearing site data will drop the content — export anything important.

---

## 6. The timer

### 6.1 Countdown

- Type hours / minutes / seconds, or tap a preset: 1 / 3 / 5 / 10 / 25 minutes (25 is the classic pomodoro 🍅);
- **▶ Start** begins the count (the button becomes **⏸ Pause**); **↺ Reset** returns to the set value;
- An SVG ring shrinks as time runs out; at zero it turns red and chimes three times (synthesized in real time with WebAudio — there are no audio files in the repo);
- While running, the **browser tab title** mirrors the remaining time, so you can see it from another tab.

### 6.2 Stopwatch

Tap **⏱ Stopwatch** to switch: counts up from zero, with the ring completing one revolution per minute. Handy for measuring how long something takes — it won't alarm.

---

## 7. Tips for tablets and phones

1. **Browser choice**: Chrome or Edge on Android tablets; Safari on iPad. Both are tested.
2. **Landscape for coding**: the editor adapts to portrait too, but landscape gives you the most room.
3. **Use the symbol keyboard** when writing C++ — it's much faster than hunting for symbols on a system keyboard.
4. **Local music**: tap "Upload audio" and pick songs in the file picker; files never leave the device.
5. **One-handed use**: high-frequency controls (play, start timer) are deliberately oversized.
6. **Dark mode**: easier on the eyes at night, one tap away, and it's remembered.
7. **Offline**: everything except AI chat (which needs to reach your model endpoint) works with no network at all.

---

## 8. Deployment

### 8.1 GitHub Pages (what this project's demo uses)

1. Fork or push this repo to your GitHub;
2. Repo → **Settings → Pages → Build and deployment → Source**: choose `Deploy from a branch`;
3. Branch `main`, folder `/`, Save;
4. Wait a minute or two, then visit `https://<your-username>.github.io/tablet-full-ai-workbench/`.

### 8.2 Any other static host

Since it's a single static file, drop it anywhere: Netlify, Vercel, Cloudflare Pages, Alibaba Cloud OSS, Tencent Cloud COS, Nginx… just put `index.html` at the root.

### 8.3 Fully offline

Copy `index.html` to your phone, tablet, or USB stick and open it in a browser. Paired with a local Ollama server, even the AI chat never touches the internet.

---

## 9. Developer guide

### 9.1 Code layout (single file, comment-delimited sections)

`index.html` is organized into 9 regions, each with a Chinese comment banner:

| Region | Contents |
|---|---|
| 0. Utilities | `$`, `esc`, `toast`, `fmtTime`, `downloadFile`, etc. |
| 1. Theme | `applyTheme()`, driven by CSS variables |
| 2. Module switching | `switchApp()` |
| 3. Music player | `addFiles()`, `playIndex()`, `renderPlaylist()`, `makeDemoWav()` |
| 4. Code editor | `highlightCode()`, `updateEditor()`, symbol keyboard |
| 5. AI chat | `AGENT_TOOLS`, `streamChat()`, `runAgentLoop()`, `runTool()` |
| 6. Notepad | `saveNotes()` |
| 7. Timer | `startCountdown()`, `toggleTimer()`, `playBeep()` |
| 8. Public API | `window.TFAW` |

### 9.2 Changing the theme

Every color is a CSS variable — edit `:root` (dark) and `:root[data-theme="light"]` (light) and the whole app follows:

```css
:root{
  --accent:#5b8cff;                    /* buttons, highlights, progress */
  --accent-soft:rgba(91,140,255,.14);  /* tinted backgrounds */
  --bg:#0b0e14;                        /* page background */
  --surface:#151a26;                   /* card background */
  /* … */
}
```

### 9.3 Adding a new agent tool

Two steps. Example: a "what should I eat" tool.

1. Add the schema to the `AGENT_TOOLS` array (this is what gets sent to the model):

```js
{ type:'function', function:{
  name:'what_to_eat',
  description:'Randomly recommend a dish',
  parameters:{ type:'object', properties:{ meal:{ type:'string', enum:['breakfast','lunch','dinner'] } } } } }
```

2. Add a branch in `runTool()`'s `switch`:

```js
case 'what_to_eat': {
  const menu = ['Kung Pao Chicken','Tomato and Egg','Beef Noodles','Caesar Salad'];
  return 'How about: ' + menu[Math.floor(Math.random()*menu.length)];
}
```

Save and refresh. No build step.

### 9.4 Adding a new module (say, a unit converter)

1. Copy any `<section class="app" id="app-xxx">…</section>` block;
2. Add a matching tab: `<button class="tab" data-app="xxx">🧮<span>Convert</span></button>`;
3. If the AI should be able to drive it, add a tool as in 9.3.

### 9.5 Console API

The page exposes `window.TFAW`:

```js
TFAW.version          // version string
TFAW.switchApp('code')
TFAW.addDemoTrack()   // synthesize a demo track
TFAW.setCodeSample()  // fill in the sample program
TFAW.seedChatDemo()   // scripted agent demo
TFAW.notes.set('hi')  // write the notepad
TFAW.music            // player state (playlist, current track)
TFAW.audio            // the underlying audio element
```

---

## 10. Troubleshooting quick reference

| Problem | Answer |
|---|---|
| Playlist empty after refresh | Expected — browsers can't persist local files; just re-add them |
| `Failed to fetch` from the AI | Check the Base URL; is the local service running; is CORS allowed |
| `HTTP 404` | The Base URL usually needs to end with `/v1` |
| Demo page can't reach local Ollama | An https page can't call an http endpoint — open the page over `http://localhost` |
| No autoplay on iOS | Safari policy — tap play once and it behaves afterwards |
| Notepad content gone | Incognito mode or cleared site data; export important text |
| Want to recolor the app | See [9.2](#92-changing-the-theme) |

More errors and fixes live in the [README FAQ](../README.md#-faq).

---

**License**: MIT · Original author: Andy-hub-byte · Stars and PRs welcome ⭐
