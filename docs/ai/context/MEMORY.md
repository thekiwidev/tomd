---
doc: context/MEMORY
purpose: Agent-facing compressed copy of ../../../MEMORY.md; never edited by hand
authority: derived
source: ../../../MEMORY.md
source_sha256: 336954b24260f79c365d924737a1374b6cfeb5ce80186917fe72e70ddb727a83
generated_at: 2026-11-15
register: caveman-ultra
---

# MEMORY — agent-facing context (derived)

## Current Position

- tomd 0.1.11 (released 2026-08-06): PySide6 desktop app, ~100 MB. Converts dropped files, folders, YouTube links to Markdown via MarkItDown CLI. Released macOS + Windows.
- In progress: **tomd 0.2.0 — UI rewrite, Tauri v2 + React, `backend.py` kept as Python sidecar, macOS first.** Plan: `docs/ai/plans/active/tauri-rewrite.md` (approved 2026-11-15). Baton: `docs/ai/HANDOFF.md`. No rewrite application code yet.
- Released app, owner's machine (macOS 27.0.1), three known defects: menu bar icon crashes app; drop-zone corner not clickable; pending row renders broken (`docs/ai/NOTES.md` N-001 to N-003). Fixed by rewrite, not patched.

## Fixed Decisions

- Tauri v2 shell, React + TypeScript + Tailwind UI, frozen Python sidecar running `backend.py`; macOS first, Windows stays 0.1.11 until follow-up release (ADR-001).
- MarkItDown never bundled; tomd installs into own venv, drives CLI.
- Owner controls Git; work on `dev`.

## Architecture

Today: three flat Python files. `app.py` = whole Qt UI. `backend.py` (standard library only) = find/install Python, `uv`, MarkItDown; run conversions. `native.py` = Dock-icon, all-Spaces, login-item. Detail: `docs/ai/ARCHITECTURE.md`.

## Features

All working in 0.1.11 unless noted:

- Drag and drop files + folders (26 extensions), sequential conversion queue, Stop, auto-convert on drop.
- Per row: Copy MD, drag `.md` out, Reveal, multi-select remove / reveal. Defect N-003 in pending state.
- Menu bar icon with menu. Crashes on macOS 27 (N-001).
- Floating drop zone at one of six screen anchors, summoned by hot-corner. Hot-corner blocks clicks (N-002).
- Settings: drop zone + anchor, auto-convert, menu-bar-only, start at login, MarkItDown status + Repair.
- First-run setup: detect Python / `uv` / MarkItDown, one-click install with live log, Homebrew alternative.
- YouTube transcripts: link validation, slugged file name with live preview, remembered output folder.

## Environment

- `uv sync`, then `uv run python app.py` (or `uv run python dev.py`, hot reload). Python 3.12.
- Build: `bash scripts/build_macos.sh` writes `dist/tomd.app`, `dist/tomd.dmg`.
- Owner's machine, for rewrite: Rust 1.96, Node 26, bun 1.4 (no pnpm).
- Installed `/Applications/tomd.app` reports version `0.0.0` in `Info.plist` (PyInstaller default); real version in `pyproject.toml`.

## Gotchas

- MarkItDown exits 0 when YouTube transcript fetch fails, writes YouTube page footer; `backend._transcript_problem` detects.
- MarkItDown YouTube converter recognises only `https://www.youtube.com/watch?v=...`; links normalised first.
- `QSystemTrayIcon` aborts on macOS 27 when menu opens (N-001).

## Deferred Work

- Windows build of Tauri app (after macOS 0.2.0).
- Code signing, notarisation (app always shipped unsigned).

## Deviations

- No tests, linter, type checker for 0.1.x code; tolerated, that UI being replaced (RULE-ENG-001 applies to new code).

## Open Questions

- Not asked at adoption: product priorities beyond rewrite, explicit out-of-scope list, prohibited technologies. Ask when task depends on one.
- `RESUME-EVIDENCE.md` untracked at repository root: commit, ignore or delete = owner's call.
