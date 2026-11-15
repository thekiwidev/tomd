---
doc: plans/tauri-rewrite
purpose: "tomd 0.2.0: Tauri v2 + React UI over the existing Python backend, macOS first"
authority: canonical
hosts_rules: []
mirrors_rules: []
last_reviewed: "2026-11-15"
---

# tauri-rewrite

**Status:** active · **Classification:** refactor (re-platform at feature parity) + three bug fixes · **Source:** owner request 2026-11-15 · **Owner approval:** 2026-11-15

## Objective

Ship tomd 0.2.0 for macOS as a Tauri v2 app with the same features as 0.1.11, a size of roughly 15 to 25 MB, and without defects N-001, N-002 and N-003.

## Scope

Everything the 0.1.11 app does (MEMORY.md → Features), on macOS. Behaviour reference: `README.md`, `docs/specs/tray-and-ui-enhancements.md`, `assets/*.png`.

## Non-goals

Windows build; code signing or notarisation; any new feature; changes to `backend.py` behaviour; migrating 0.1.x QSettings values.

## Dependencies

Rust 1.96, bun 1.4, uv, PyInstaller (all present). Tauri plugins: `store`, `window-state`, `autostart`, `dialog`, `opener`, `clipboard-manager`, `drag`. macOS bindings: `objc2-app-kit`.

## Ordered tasks

| ID | Task | Acceptance criteria | Status |
| --- | --- | --- | --- |
| T0 | Adopt the kiwi AI system | `kiwi doctor --project` clean; committed on `dev` | done |
| T1 | Python sidecar. `links.py`: move `collect_paths`, `parse_youtube_url`, `youtube_video_id`, `canonical_youtube_url`, `slugify`, `unique_output` and the extension set out of `app.py:73-78, 301-431`, without Qt types. `sidecar.py`: JSON lines over stdin/stdout, request `{id, method, params}`, replies `{id, event: "log", line}` and `{id, event: "result", ok, data or error}`, one thread per request; methods `environment_report`, `find_foreign_markitdowns`, `invalidate_health_cache`, `install_markitdown`, `install_homebrew_python`, `repair_markitdown`, `convert_file`, `collect_paths`, `youtube_plan` | `uv run pytest` passes: the URL cases named in CHANGELOG 0.1.10 and 0.1.11, and a spawn / request / log / result round trip; a file converts from the command line through the sidecar | pending |
| T2 | Tauri shell (`src-tauri/`): sidecar manager (spawn, forward `invoke`, emit events, kill on quit); native tray menu with the items of `app.py:2728-2765`; main window hides on close; menu-bar-only via activation policy; `autostart` plus removal of the 0.1.x LaunchAgent plist; `store` settings; `drag_watch.rs`: global `NSEvent` monitor for `leftMouseDragged` / `leftMouseUp`, a file drag is detected by a changed `NSPasteboard(name: .drag).changeCount` carrying file URLs, then the drop zone window is shown at the anchor (non-activating, all Spaces) and hidden on mouse-up without a drop; anchor geometry ported from `dock_geometry` (`app.py:457`) | `cargo check` clean; in the built app the tray menu opens ten times with no new `tomd-*.ips`; with the drop zone enabled and idle, a control of another app under the anchor is clickable; dragging a file from Finder shows the zone | pending |
| T3 | React UI (`src/`): main window (toolbar, list, progress, toast), file row, setup page, settings, YouTube dialog, drop zone window; one queue store replacing `QueueWorker` (sequential; Stop returns queued rows to pending) | `bun run test` (queue store) and `bun run tsc --noEmit` pass; with auto-convert off a dropped file shows its name with the select box at the left (N-003); every feature in MEMORY.md walked through by hand | pending |
| T4 | Packaging and cleanup: `scripts/build_macos.sh` freezes the sidecar and runs `bun run tauri build`, output `tomd.dmg`; `release.yml` macOS only; `docs/index.html` Windows button pinned to `v0.1.11`; README and CONTRIBUTING updated; remove `app.py`, `native.py`, `dev.py`, `tomd.spec`, PySide6 and pyobjc; version 0.2.0 | DMG builds; size reported; the installed app passes the T2 and T3 hand checks | pending |
| T5 | Documentation: CHANGELOG 0.2.0 (RULE-DOC-012), MEMORY, ARCHITECTURE, ENGINEERING § 1, VERIFICATION gates, NOTES N-001 to N-003 resolved, context docs regenerated, this plan moved to `completed/` | `kiwi doctor --project` clean | pending |

The owner reviews after each task.

## Verification

Gates as they come into existence: `uv run pytest`, `bun run test`, `bun run tsc --noEmit`, `cargo check`. Hand checks in the built app on macOS 27 as listed per task; Finder drag tests need the owner.

## Documentation impact

T5. `VERIFICATION.md` and `SYSTEM.md → verification_commands` gain each gate in the task that creates it.

## Owner decisions required

None open. Risks: (1) the drag-pasteboard detection is the usual technique for shelf apps but unverified on macOS 27; T2 proves it early, fallback is to show the zone on any global drag that nears the anchor. (2) Sidecar and app size are estimates until the first build.
