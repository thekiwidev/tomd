# tomd

[![Release](https://img.shields.io/github/v/release/thekiwidev/tomd?color=6c5ce7)](https://github.com/thekiwidev/tomd/releases/latest)
[![Build](https://github.com/thekiwidev/tomd/actions/workflows/release.yml/badge.svg)](https://github.com/thekiwidev/tomd/actions/workflows/release.yml)
[![Downloads](https://img.shields.io/github/downloads/thekiwidev/tomd/total?color=6c5ce7)](https://github.com/thekiwidev/tomd/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Drag & drop anything. Get Markdown.** · [Website](https://thekiwidev.github.io/tomd/) · [Download](https://github.com/thekiwidev/tomd/releases/latest)

A thin desktop GUI for [Microsoft MarkItDown](https://github.com/microsoft/markitdown). Drop files or whole folders onto the window and a `.md` file appears next to every source file.

tomd does **no conversion itself** — it runs the `markitdown` CLI on *your* device, exactly as you would in a terminal. It's a developer tool: a friendly face over `markitdown file.pdf -o file.md`.

## How it works

1. On launch, tomd checks your device for the `markitdown` CLI (your `PATH` first, then tomd's own managed environment).
2. If it's missing, a one-time setup screen shows what your device has (Python 3.10+, uv) and installs `markitdown[all]` into a private virtualenv at `~/Library/Application Support/tomd/venv` (macOS) — your global Python is never touched. If you have [uv](https://docs.astral.sh/uv/), it's used (and can even download a Python for you).
3. After that, every conversion is just tomd running `markitdown <file> -o <file>.md` in the background, one file at a time, in a queue.

If you already have `markitdown` installed, tomd uses yours and never asks anything.

## Features

- 🖱️ **Drag & drop** files or entire folders (recursively picks up supported files)
- ⚙️ **Auto-convert on drop** (toggleable) — drop and it queues immediately, no clicks
- 🚶 **Sequential queue** — one conversion at a time, with per-file status, an animated spinner, and an overall progress bar
- 🔔 **Toasts** for failures and batch completion
- 📋 **Copy MD** — copy the converted markdown straight to your clipboard
- 🫳 **Drag the `.md` out** — drag the result file from the app into Finder, an editor, Slack, anywhere
- 🔍 **Reveal** — jump to the converted file in Finder / Explorer

## Install

Grab the latest build from [Releases](../../releases):

- **macOS** — see below.
- **Windows** — download `tomd.exe` and run it.

### macOS — Gatekeeper workaround

tomd is currently unsigned (no Apple Developer certificate yet), so macOS will block it on first install. Pick either option:

**Option A — remove the quarantine flag before opening the DMG**

```bash
xattr -d com.apple.quarantine ~/Downloads/tomd.dmg
```

Then open the DMG and drag tomd into Applications as normal.

**Option B — allow it after the fact via System Settings**

1. Download `tomd.dmg`, open it, drag **tomd** into **Applications**, and try to open it.
2. macOS will show a "cannot be opened" dialog — click **Done**.
3. Go to **System Settings → Privacy & Security**, scroll down, and click **Open Anyway** next to tomd.
4. Confirm in the follow-up dialog.

Either option is a one-time step — subsequent launches open normally.

## Run from source

Requires [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/thekiwidev/tomd.git
cd tomd
uv sync
uv run python app.py
```

## Build the app yourself

```bash
# macOS — produces dist/tomd.app and dist/tomd.dmg
bash scripts/build_macos.sh

# Windows — produces dist\tomd.exe
pwsh scripts/build_windows.ps1
```

Tagged pushes (`v*`) build both platforms on GitHub Actions and attach them to a release automatically.

## Supported formats

PDF, DOCX/DOC, PPTX/PPT, XLSX/XLS, CSV, JSON, XML, HTML, TXT, RTF, EPUB, MSG/EML, WAV/MP3/M4A, JPG/PNG/WEBP, IPYNB, ZIP — everything [MarkItDown](https://github.com/microsoft/markitdown) handles.

## Credits

All conversion is done by [MarkItDown](https://github.com/microsoft/markitdown), an open-source project by Microsoft's AutoGen team. tomd is an independent GUI and is not affiliated with or endorsed by Microsoft.

## License

MIT
