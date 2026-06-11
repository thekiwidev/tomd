# tomd

**Drag & drop anything. Get Markdown.**

A tiny, fast desktop GUI for [Microsoft MarkItDown](https://github.com/microsoft/markitdown). Drop files or whole folders onto the window, hit **Run ⚡**, and a `.md` file appears next to every source file.

## Features

- 🖱️ **Drag & drop** files or entire folders (recursively picks up supported files)
- ⚡ **Batch convert** PDFs, Word, PowerPoint, Excel, images, audio, HTML, EPUB, and more
- 📋 **Copy MD** — copy the converted markdown straight to your clipboard
- 🫳 **Drag the `.md` out** — drag the result file from the app into Finder, an editor, Slack, anywhere
- 🔍 **Reveal** — jump to the converted file in Finder / Explorer
- 🧵 Conversion runs in the background; the UI never freezes

## Install

Grab the latest build from [Releases](../../releases):

- **macOS** — download `tomd.dmg`, open it, drag **tomd** into **Applications**.
  First launch: right-click → **Open** (the app is unsigned).
- **Windows** — download `tomd.exe` and run it.

## Run from source

Requires [uv](https://docs.astral.sh/uv/) (or Python 3.10+ with pip).

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

PDF, DOCX/DOC, PPTX/PPT, XLSX/XLS, CSV, JSON, XML, HTML, TXT, RTF, EPUB, MSG/EML, WAV/MP3/M4A (transcription metadata), JPG/PNG/WEBP (EXIF/OCR), IPYNB, ZIP — everything MarkItDown handles.

## License

MIT
