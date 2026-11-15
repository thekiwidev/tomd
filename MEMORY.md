# MEMORY — tomd

> Current state only. Rewritten when reality changes; never a diary, never contradictory facts side by side. Read top to bottom at every session start. No secrets.

## Current Position

tomd 0.1.11 (released 2026-08-06) is a PySide6 desktop app, about 100 MB, that converts dropped files, folders and YouTube links to Markdown by driving the MarkItDown CLI. It is released for macOS and Windows.

Work in progress: **tomd 0.2.0, a rewrite of the UI in Tauri v2 + React with `backend.py` kept as a Python sidecar, macOS first.** Plan: `docs/ai/plans/active/tauri-rewrite.md` (approved 2026-11-15). Baton: `docs/ai/HANDOFF.md`. No application code of the rewrite exists yet.

The released app has three known defects on the owner's machine (macOS 27.0.1): the menu bar icon crashes it, the drop-zone corner cannot be clicked, and a pending row renders broken (`docs/ai/NOTES.md` N-001 to N-003). They are fixed by the rewrite, not patched.

## Fixed Decisions

- Tauri v2 shell, React + TypeScript + Tailwind UI, frozen Python sidecar running `backend.py`; macOS first, Windows stays on 0.1.11 until a follow-up release (ADR-001).
- MarkItDown is never bundled; tomd installs it into its own venv and drives the CLI.
- The owner controls Git; work happens on `dev`.

## Architecture

Today: three flat Python files. `app.py` is the whole Qt UI; `backend.py` (standard library only) finds or installs Python, `uv` and MarkItDown and runs conversions; `native.py` does Dock-icon, all-Spaces and login-item integration. Detail: `docs/ai/ARCHITECTURE.md`.

## Features

All working in 0.1.11 unless noted:

- Drag and drop of files and folders (26 extensions), sequential conversion queue, Stop, auto-convert on drop.
- Per row: Copy MD, drag the `.md` out, Reveal, multi-select remove / reveal. Defect N-003 in the pending state.
- Menu bar icon with menu. Crashes on macOS 27 (N-001).
- Floating drop zone at one of six screen anchors, summoned by a hot-corner. The hot-corner blocks clicks (N-002).
- Settings: drop zone and anchor, auto-convert, menu-bar-only, start at login, MarkItDown status and Repair.
- First-run setup: detect Python / `uv` / MarkItDown, one-click install with live log, Homebrew alternative.
- YouTube transcripts: link validation, slugged file name with live preview, remembered output folder.

## Environment

- `uv sync`, then `uv run python app.py` (or `uv run python dev.py` for hot reload). Python 3.12.
- Build: `bash scripts/build_macos.sh` writes `dist/tomd.app` and `dist/tomd.dmg`.
- Available on the owner's machine for the rewrite: Rust 1.96, Node 26, bun 1.4 (no pnpm).
- The installed `/Applications/tomd.app` reports version `0.0.0` in its `Info.plist` (PyInstaller default); the real version is in `pyproject.toml`.

## Gotchas

- MarkItDown exits 0 when a YouTube transcript fetch fails and writes YouTube's page footer; `backend._transcript_problem` detects it.
- MarkItDown's YouTube converter only recognises `https://www.youtube.com/watch?v=...`; links are normalised first.
- `QSystemTrayIcon` aborts on macOS 27 when its menu opens (N-001).

## Deferred Work

- Windows build of the Tauri app (after macOS 0.2.0).
- Code signing and notarisation (the app has always shipped unsigned).

## Deviations

- No tests, linter or type checker exist for the 0.1.x code; tolerated because that UI is being replaced (RULE-ENG-001 applies to new code).

## Open Questions

- Not asked at adoption: product priorities beyond the rewrite, an explicit out-of-scope list, prohibited technologies. Ask when a task depends on one.
- `RESUME-EVIDENCE.md` sits untracked at the repository root: commit, ignore or delete is the owner's call.
