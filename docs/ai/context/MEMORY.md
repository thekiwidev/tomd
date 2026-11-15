---
doc: context/MEMORY
purpose: Agent-facing compressed copy of ../../../MEMORY.md; never edited by hand
authority: derived
source: ../../../MEMORY.md
source_sha256: c790ad81b9ccedc79d0efacd4aaf11a99768b676f2fcba0be902852227a9f1ad
generated_at: 2026-11-15
register: caveman-ultra
---

# MEMORY — agent-facing context (derived)

## Current Position

- tomd 0.2.0 built, not released: Tauri v2 app (Rust shell, React UI) over unchanged Python backend, macOS only, 24 MB installed, 12 MB DMG. Converts dropped files, folders, YouTube links to Markdown via MarkItDown CLI. All uncommitted on `dev`; owner commits, tags, releases. Last release: 0.1.11 (2026-08-06, PySide6, macOS + Windows).
- Plans: `tauri-rewrite` complete (`docs/ai/plans/completed/tauri-rewrite.md`). `finder-convert` (`docs/ai/plans/active/finder-convert.md`, PRD `docs/ai/prd/prd-finder-convert.md`) coded, built, documented; stays active until owner checks three drag modes, Finder switch in Settings, failure toast. Baton + open hand checks: `docs/ai/HANDOFF.md`. Attempt history: `docs/ai/LOG.md` (L-001 to L-017).
- Three 0.1.11 defects: menu bar crash + dead corner resolved, owner-confirmed (NOTES N-001, N-002); pending-row fix in, not hand-confirmed (N-003, open).

## Fixed Decisions

- Tauri v2 shell, React + TypeScript + Tailwind UI, frozen Python sidecar running `backend.py`; macOS first, Windows stays 0.1.11 until follow-up release (ADR-001).
- MarkItDown never bundled; tomd installs into own venv, drives CLI.
- Owner controls Git; work on `dev`.
- Finder entry = Quick Action while app unsigned; top-level right-click item waits for signing (owner, 2026-11-15, LOG L-013).

## Architecture

Shell (`src-tauri/`, Rust): windows, menu bar icon, settings, drag watcher, Finder Quick Action, sidecar process. UI (`src/`, React): three windows, one bundle (`main`, `dropzone`, `toast`); conversion queue = pure reducer in main window (`src/queue.ts`). Sidecar (`sidecar.py` over `backend.py` + `links.py`, standard library only): JSON lines over stdin / stdout; finds or installs Python, `uv`, MarkItDown; runs conversions. Detail: `docs/ai/ARCHITECTURE.md`.

## Features

- Drag and drop files + folders (26 extensions) onto main window, sequential queue, Stop, auto-convert on drop, Add files picker.
- Per row: Copy MD, drag `.md` out, Reveal, multi-select remove / reveal.
- Menu bar icon, native menu: open window, open drop zone, add YouTube video, settings, auto-convert, quit.
- Floating drop zone at one of six anchors; appears when file drag starts anywhere, leaves when dropped elsewhere. Setting "When a drag starts": show, shake to hide, start small, hold Option to hide.
- Finder: right-click, Quick Actions, "Convert to Markdown" for supported files; background conversion, status toast at anchor; switch in Settings. Not offered for `.ipynb`, `.msg` (no system file type).
- Settings: drop zone, position, drag mode, Finder entry, auto-convert, menu-bar-only, start at login, MarkItDown status + Repair.
- First-run setup: detect Python / `uv` / MarkItDown, one-click install with live log, Homebrew alternative.
- YouTube transcripts: link validation, slugged file name with live preview, remembered output folder.

## Environment

- Tests: `uv run pytest`; `bun run test` (vitest, queue reducer); `cargo test` in `src-tauri/`. Typecheck: `bun run typecheck`.
- `src-tauri/Cargo.toml` builds dev profile without debug info (`debug = 0`): with it `src-tauri/target` grew to several GB and filled owner's disk. `rm -rf src-tauri/target` is always safe.
- Tauri shell: `bun install`, then `bun run tauri build --debug --bundles app`; app lands in `src-tauri/target/debug/bundle/macos/tomd.app`. Debug builds run `sidecar.py` from repository's `.venv`.
- Run from source: `uv sync`, `bun install`, `bun run tauri dev`. Python 3.12. PySide6 app (`app.py`, `native.py`, `dev.py`) was removed in T4 (2026-11-15); its last state is in Git history and release v0.1.11.
- Build: `bash scripts/build_macos.sh` freezes `sidecar.py` with PyInstaller into `build/sidecar/tomd-sidecar/`, runs `bun run tauri build --bundles app` with that folder as resource `sidecar/` and ad-hoc signature, and writes `dist/tomd.app` (24 MB) and `dist/tomd.dmg` (12 MB). release app runs `Contents/Resources/sidecar/tomd-sidecar`.
- On owner's machine: Rust 1.96, Node 26, bun 1.4 (no pnpm), macOS 27.0.1.
- version lives in four files: `pyproject.toml`, `package.json`, `src-tauri/Cargo.toml`, `src-tauri/tauri.conf.json`.

## Gotchas

- MarkItDown exits 0 when YouTube transcript fetch fails and writes YouTube's page footer; `backend._transcript_problem` detects it.
- MarkItDown's YouTube converter only recognises `https://www.youtube.com/watch?v=...`; links are normalised first.
- Vite builds to `dist-ui/`, not `dist/` (release build's output). `cargo check` fails if `dist-ui/` does not exist.
- macOS filesystem is case-insensitive: `Main.tsx` and `main.tsx` are one file. Component files must not differ from another file only by case.
- To check that webview actually rendered, capture window (`screencapture -l <window id>`); window being on screen proves nothing.
- A debug build must never touch login items (`migrate_login_item` is skipped under `debug_assertions`); the "start at login" toggle in debug build registers `target/debug` binary.
- A fresh launch can receive files (`RunEvent::Opened`) before `setup` has run: state used by that handler must be managed on builder (`Opened` in `lib.rs`), or panic aborts app inside Apple Event handler.
- tomd sets `ApplePersistenceIgnoreState` at start: after crash macOS otherwise shows a "reopen windows?" dialog that blocks background launch.
- On owner's Mac app Vorssaint sends tomd Quit Apple Event when tomd has no window (found with `lldb` on `_handleAEQuit`, LOG L-014). A tomd that exits with code 0 seconds after background launch is that, not crash.
- Finder Quick Action is written only by tomd running from `.app` outside any `target/` folder (`quick_action.rs`); `/Applications/tomd.app` on owner's Mac is release build from `dist/` (installed with `ditto`, 2026-11-15).
- Agents cannot click menu bar or drag files on this machine (no assistive access); those checks are owner's.

## Deferred Work

- Code signing, notarisation, top-level Finder right-click item (needs signed Finder Sync extension + Apple Developer Program membership).
- Windows build of Tauri app.
- Universal (Intel + Apple Silicon) macOS build; build = building machine's architecture.

## Deviations

- `backend.py` no tests of its own (exercised through `tests/test_sidecar.py` with fakes); carried over from 0.1.x.
- React components + Rust window, tray, drag code: no automated tests; verified by hand in built app (ENGINEERING § 7). Tested: queue reducer, shake detector, anchor geometry, settings validation, Quick Action generator.

## Open Questions

- `scripts/build_windows.ps1`, `assets/make_icon.py` no longer work (need removed `app.py`, PySide6): delete, or keep for Windows follow-up?
- `docs/index.html` still says "Intel Macs", "Linux: run from source"; neither true for 0.2.0.
- `RESUME-EVIDENCE.md` untracked at repository root: commit, ignore or delete = owner's call.
- Not asked at adoption: product priorities beyond rewrite, explicit out-of-scope list, prohibited technologies. Ask when task depends on one.
