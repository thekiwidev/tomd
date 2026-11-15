---
doc: context/NOTES
purpose: Agent-facing compressed copy of ../NOTES.md; never edited by hand
authority: derived
source: ../NOTES.md
source_sha256: bd98ab4f54454307b195a1764b306067191795c63d666888173ee6247be5508e
generated_at: 2026-11-15
register: caveman-ultra
---

# NOTES — agent-facing context (derived)

Each note: ID (`N-###`, never reused), date, status (`open` · `deferred` · `deliberate non-fix` · `resolved`). Sub-headings carry note ID (RULE-DOC-013). Newest first (RULE-DOC-016). Read before raising anything as new.

## N-003 — Pending row renders broken until the first state change

**Date:** 2026-11-15 · **Status:** open · **Related:** CHANGELOG v0.2.0, `src/FileRow.tsx`, `app.py:735-962` (`FileRow`, removed in 0.2.0), plan `tauri-rewrite`

### N-003 — Context

Owner report: auto-convert off, file dropped in main window: row shows no visible name, small box in middle; Run fixes row. Cause, inferred from code (not reproduced, no screenshot): in `PENDING` sub-row holds only fixed 12 px file icon, Qt centres it in free width; name label uses `QSizePolicy.Ignored`, elided in `resizeEvent` against width layout has not applied yet, re-elided only when `set_state` calls `_show_sub_text`.

### N-003 — Decision / trigger to revisit

Not patched in PySide6 `[owner: 2026-11-15]`: row rebuilt in Tauri UI, plain flex layout. Revisit only if rewrite abandoned.

State 2026-11-15: row rebuilt (`src/FileRow.tsx`); captures show name + select box at left for finished rows. Pending state not hand-confirmed; note stays open until owner has seen dropped file with auto-convert off.

## N-002 — Drop-zone hot-corner is a permanent window and swallows clicks

**Date:** 2026-11-15 · **Status:** resolved · **Related:** CHANGELOG v0.2.0, `src-tauri/src/drag_watch.rs`, `app.py:2079-2143` (`EdgeSensor`, removed in 0.2.0), CHANGELOG 0.1.7, plan `tauri-rewrite`

### N-002 — Context

Owner report: drop zone enabled, screen area at anchor not clickable, any app, nothing visible there. `EdgeSensor` = frameless, translucent, always-on-top 116 x 116 window, stays at anchor to notice drag. 0.1.7 fix set `WA_TransparentForMouseEvents`; did not help; fits attribute affecting only Qt's own event dispatch while native window still takes click (inferred). Window that must receive drag cannot also ignore clicks.

### N-002 — Decision / trigger to revisit

Rewrite keeps no window on screen while idle: global mouse monitor watches for file drag, shows drop zone only for its duration (plan task T2, ADR-001). Do not reintroduce standing sensor window.

### N-002 — Resolution

Resolved in 0.2.0. `drag_watch.rs` polls mouse button + drag pasteboard, shows drop zone only during file drag (global event monitor first tried not called on macOS 27, LOG L-005). Owner-confirmed 2026-11-15: corner clickable, drag summons zone (LOG L-005, L-009).

## N-001 — Menu bar icon click aborts the app on macOS 27

**Date:** 2026-11-15 · **Status:** resolved · **Related:** CHANGELOG v0.2.0, `app.py:2728-2765` (`_build_tray`, removed in 0.2.0), `~/Library/Logs/DiagnosticReports/tomd-2026-11-15-1421422.ips`, plan `tauri-rewrite`

### N-001 — Context

Owner report: clicking menu bar icon closes app. Two crash reports 2026-11-15, macOS 27.0.1: `SIGABRT` on main thread: `NSSceneStatusItem` opens status-item menu, `NSMenuTrackingSession` posts begin-tracking notification, Qt `libqcocoa` observer calls `-[NSEvent clickCount]` on non-mouse event, AppKit assertion handler throws. Fault inside Qt macOS plugin (PySide6 6.11), not tomd code.

### N-001 — Decision / trigger to revisit

Not patched in PySide6 `[owner: 2026-11-15]`. Rewrite uses Tauri native tray menu, removes Qt from path. Newer PySide6 fixing it: not checked.

### N-001 — Resolution

Resolved in 0.2.0: menu = `src-tauri/src/tray.rs`, native menu. Owner-confirmed 2026-11-15: menu opens without crash, items work (LOG L-004).
