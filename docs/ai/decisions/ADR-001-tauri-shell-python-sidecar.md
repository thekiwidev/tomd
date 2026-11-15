---
doc: decisions/ADR-001
purpose: "Replace the PySide6 UI with a Tauri v2 shell, a React UI and a frozen Python sidecar; macOS first"
authority: canonical
hosts_rules: []
mirrors_rules: []
last_reviewed: "2026-11-15"
---

# ADR-001 — Tauri v2 shell, React UI, frozen Python sidecar; macOS first

**Status:** Accepted
**Date:** 2026-11-15

## Decision

tomd 0.2.0 replaces the PySide6 UI (`app.py`, `native.py`) with:

- a **Tauri v2** shell in Rust (`src-tauri/`) that owns the windows, the native tray menu, the global drag watcher, settings and the login item;
- a **React + TypeScript + Tailwind** UI built with Vite, using bun;
- **`backend.py` unchanged**, run as a long-lived **frozen Python sidecar** (PyInstaller onedir, standard library only) that speaks JSON lines over stdin/stdout.

macOS ships first. Windows users stay on 0.1.11 until a follow-up release.

## Context

The owner wants the app lightweight and modern; the PySide6 bundle is about 100 MB. Three defects reported on macOS 27 all sit in the Qt layer (NOTES N-001 to N-003), and one of them is inside Qt's own macOS plugin, outside tomd's control. `backend.py` imports only the standard library and has been hardened over several releases (install ladder, health checks, error translation), so it is worth keeping as is.

## Options considered

- **Patch the three defects in PySide6, then rewrite.** Rejected by the owner: the fixes would be thrown away, and N-001 would need a hand-written `NSStatusItem` through pyobjc.
- **Patch PySide6 only, no rewrite.** Rejected: the app stays about 100 MB.
- **Port `backend.py` to Rust.** Rejected: 800 lines of verified behaviour rewritten for a saving of roughly 10 MB; the owner asked to keep Python in the background.
- **Svelte or vanilla TypeScript for the UI.** Rejected in favour of React, which the owner knows.
- **macOS and Windows together.** Rejected: Windows cannot be tested on the owner's machine; parity on both would delay any release.

## Consequences

- The drop zone must not keep a window on screen while idle; a global mouse monitor shows it only during a file drag (N-002).
- Two build toolchains (Rust / bun and Python / PyInstaller) in one release script.
- `releases/latest` will stop carrying `tomd.exe`; the site's Windows link must be pinned to the `v0.1.11` asset.
- QSettings values from 0.1.x are not migrated; the user sets six preferences again.
- The 0.1.x login item (`~/Library/LaunchAgents/me.thekiwidev.tomd.plist`) must be removed by the new app on first run, or tomd would start twice.

## Related documents

[`../plans/completed/tauri-rewrite.md`](../plans/completed/tauri-rewrite.md) · [`../NOTES.md`](../NOTES.md) N-001 to N-003 · [`../ARCHITECTURE.md`](../ARCHITECTURE.md)
