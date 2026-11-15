# MEMORY — tomd

> Current state only. Rewritten when reality changes; never a diary, never contradictory facts side by side. Read top to bottom at every session start. No secrets.

## Current Position

tomd 0.2.0 is released (2026-11-16): a Tauri v2 app (Rust shell, React UI) over the unchanged Python backend, macOS only, 24 MB installed and 12 MB as a DMG. It converts dropped files, folders and YouTube links to Markdown by driving the MarkItDown CLI. Everything is uncommitted on `dev`; the owner commits, tags and releases. Last release: 0.1.11 (2026-08-06, PySide6, macOS and Windows).

Plans: `tauri-rewrite` is complete (`docs/ai/plans/completed/tauri-rewrite.md`). `finder-convert` (`docs/ai/plans/active/finder-convert.md`, PRD `docs/ai/prd/prd-finder-convert.md`) is coded, built and documented; it stays active until the owner has checked the three drag modes, the Finder switch in Settings and the failure toast. Baton and the list of open hand checks: `docs/ai/HANDOFF.md`. History of every attempt: `docs/ai/LOG.md` (L-001 to L-017).

Of the three defects reported on 0.1.11, the menu bar crash and the dead corner are resolved and confirmed by the owner (NOTES N-001, N-002); the pending-row fix is in but not yet confirmed by hand (N-003, open).

## Fixed Decisions

- Tauri v2 shell, React + TypeScript + Tailwind UI, frozen Python sidecar running `backend.py`; macOS first, Windows stays on 0.1.11 until a follow-up release (ADR-001).
- MarkItDown is never bundled; tomd installs it into its own venv and drives the CLI.
- The owner controls Git; work happens on `dev`.
- The Finder entry is a Quick Action while the app is unsigned; a top-level right-click item waits for signing (owner, 2026-11-15, LOG L-013).

## Architecture

Shell (`src-tauri/`, Rust): windows, menu bar icon, settings, drag watcher, Finder Quick Action, and the process that runs the sidecar. UI (`src/`, React): three windows from one bundle (`main`, `dropzone`, `toast`); the conversion queue is a pure reducer in the main window (`src/queue.ts`). Sidecar (`sidecar.py` over `backend.py` and `links.py`, standard library only): JSON lines over stdin / stdout; finds or installs Python, `uv` and MarkItDown and runs conversions. Detail: `docs/ai/ARCHITECTURE.md`.

## Features

- Drag and drop of files and folders (26 extensions) onto the main window, sequential conversion queue, Stop, auto-convert on drop, Add files picker.
- Per row: Copy MD, drag the `.md` out, Reveal, multi-select remove / reveal.
- Menu bar icon with a native menu: open window, open drop zone, add YouTube video, settings, auto-convert, quit.
- Floating drop zone at one of six screen anchors; appears when a file drag starts anywhere, leaves when the file is dropped elsewhere. Setting "When a drag starts": show, shake to hide, start small, hold Option to hide.
- Finder: right-click, Quick Actions, "Convert to Markdown" for supported files; converts in the background with a status toast at the anchor; switch in Settings. Not offered for `.ipynb` and `.msg` (no system file type).
- Settings: drop zone, position, drag mode, Finder entry, auto-convert, menu-bar-only, start at login, MarkItDown status and Repair.
- First-run setup: detect Python / `uv` / MarkItDown, one-click install with live log, Homebrew alternative.
- YouTube transcripts: link validation, slugged file name with live preview, remembered output folder.

## Environment

- Tests: `uv run pytest`; `bun run test` (vitest, the queue reducer); `cargo test` in `src-tauri/`. Typecheck: `bun run typecheck`.
- `src-tauri/Cargo.toml` builds the dev profile without debug info (`debug = 0`): with it `src-tauri/target` grew to several GB and filled the owner's disk. `rm -rf src-tauri/target` is always safe.
- Tauri shell: `bun install`, then `bun run tauri build --debug --bundles app`; the app lands in `src-tauri/target/debug/bundle/macos/tomd.app`. Debug builds run `sidecar.py` from the repository's `.venv`.
- Run from source: `uv sync`, `bun install`, `bun run tauri dev`. Python 3.12. The PySide6 app (`app.py`, `native.py`, `dev.py`) was removed in T4 (2026-11-15); its last state is in Git history and release v0.1.11.
- Build: `bash scripts/build_macos.sh` freezes `sidecar.py` with PyInstaller into `build/sidecar/tomd-sidecar/`, runs `bun run tauri build --bundles app` with that folder as the resource `sidecar/` and an ad-hoc signature, and writes `dist/tomd.app` (24 MB) and `dist/tomd.dmg` (12 MB). The release app runs `Contents/Resources/sidecar/tomd-sidecar`.
- On the owner's machine: Rust 1.96, Node 26, bun 1.4 (no pnpm), macOS 27.0.1.
- The version lives in four files: `pyproject.toml`, `package.json`, `src-tauri/Cargo.toml`, `src-tauri/tauri.conf.json`.

## Gotchas

- MarkItDown exits 0 when a YouTube transcript fetch fails and writes YouTube's page footer; `backend._transcript_problem` detects it.
- MarkItDown's YouTube converter only recognises `https://www.youtube.com/watch?v=...`; links are normalised first.
- Vite builds to `dist-ui/`, not `dist/` (the release build's output). `cargo check` fails if `dist-ui/` does not exist.
- The macOS filesystem is case-insensitive: `Main.tsx` and `main.tsx` are one file. Component files must not differ from another file only by case.
- To check that a webview actually rendered, capture the window (`screencapture -l <window id>`); a window being on screen proves nothing.
- A debug build must never touch login items (`migrate_login_item` is skipped under `debug_assertions`); the "start at login" toggle in a debug build registers the `target/debug` binary.
- A fresh launch can receive files (`RunEvent::Opened`) before `setup` has run: state used by that handler must be managed on the builder (`Opened` in `lib.rs`), or the panic aborts the app inside the Apple Event handler.
- tomd sets `ApplePersistenceIgnoreState` at start: after a crash macOS otherwise shows a "reopen windows?" dialog that blocks a background launch.
- On the owner's Mac the app Vorssaint sends tomd a Quit Apple Event when tomd has no window (found with `lldb` on `_handleAEQuit`, LOG L-014). A tomd that exits with code 0 seconds after a background launch is that, not a crash.
- The Finder Quick Action is written only by a tomd running from an `.app` outside any `target/` folder (`quick_action.rs`); `/Applications/tomd.app` on the owner's Mac is the release build from `dist/` (installed with `ditto`, 2026-11-15).
- Agents cannot click the menu bar or drag files on this machine (no assistive access); those checks are the owner's.

## Deferred Work

- Code signing, notarisation and a top-level Finder right-click item (needs a signed Finder Sync extension and an Apple Developer Program membership).
- Windows build of the Tauri app.
- A universal (Intel + Apple Silicon) macOS build; the build is for the building machine's architecture.

## Deviations

- `backend.py` has no tests of its own (it is exercised through `tests/test_sidecar.py` with fakes); carried over from 0.1.x.
- The React components and the Rust window, tray and drag code have no automated tests; they are verified by hand in the built app (ENGINEERING § 7). The queue reducer, shake detector, anchor geometry, settings validation and Quick Action generator are tested.

## Open Questions

- `scripts/build_windows.ps1` and `assets/make_icon.py` no longer work (they need the removed `app.py` and PySide6): delete, or keep for the Windows follow-up?
- `docs/index.html` still says "Intel Macs" and "Linux: run from source"; neither is true for 0.2.0.
- `RESUME-EVIDENCE.md` sits untracked at the repository root: commit, ignore or delete is the owner's call.
- Not asked at adoption: product priorities beyond the rewrite, an explicit out-of-scope list, prohibited technologies. Ask when a task depends on one.
