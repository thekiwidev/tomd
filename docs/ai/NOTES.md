---
doc: NOTES
purpose: "Observations that are not yet durable architecture or current state: open defects, deferred concerns, investigation notes, deliberate non-fixes, gotchas"
authority: reference
hosts_rules: []
mirrors_rules: []
last_reviewed: "2026-11-15"
---

# NOTES — tomd

> Each note has an ID (`N-###`, never reused), a date, a status (`open` · `deferred` · `deliberate non-fix` · `resolved`), and enough context to understand it later. Every sub-heading carries the note's ID so headings stay unique (RULE-DOC-013). Read before raising anything as new.

<!-- Entry shape (newest first: insert each new entry directly under this header, above the previous one; continue the numbering upward; RULE-DOC-016):

## N-001 — <title>

**Date:** YYYY-MM-DD · **Status:** open · **Related:** CHANGELOG vX.Y.Z, `path/to/file`

### N-001 — Context

### N-001 — Decision / trigger to revisit

### N-001 — Resolution
(only once resolved; update the status line at the same time)
-->

## N-003 — Pending row renders broken until the first state change

**Date:** 2026-11-15 · **Status:** open · **Related:** CHANGELOG v0.2.0, `src/FileRow.tsx`, `app.py:735-962` (`FileRow`, removed in 0.2.0), plan `tauri-rewrite`

### N-003 — Context

Reported by the owner: with auto-convert off, a file dropped into the main window shows a row with no visible name and a small box in the middle; pressing Run fixes the row. Cause, inferred from the code (not reproduced, no screenshot was available): in the `PENDING` state the sub-row holds only the fixed 12 px file icon, which Qt centres in the free width; the name label uses `QSizePolicy.Ignored` and is elided in `resizeEvent` against a width the layout has not applied yet, and is only re-elided when `set_state` calls `_show_sub_text`.

### N-003 — Decision / trigger to revisit

Not patched in PySide6 `[owner: 2026-11-15]`: the row is rebuilt in the Tauri UI with plain flex layout. Revisit only if the rewrite is abandoned.

State on 2026-11-15: the row is rebuilt (`src/FileRow.tsx`) and captures show the name and the select box at the left for finished rows. The pending state itself has not been confirmed by hand; the note stays open until the owner has seen a dropped file with auto-convert off.

## N-002 — Drop-zone hot-corner is a permanent window and swallows clicks

**Date:** 2026-11-15 · **Status:** resolved · **Related:** CHANGELOG v0.2.0, `src-tauri/src/drag_watch.rs`, `app.py:2079-2143` (`EdgeSensor`, removed in 0.2.0), CHANGELOG 0.1.7, plan `tauri-rewrite`

### N-002 — Context

Reported by the owner: with the drop zone enabled, the screen area at its anchor cannot be clicked, in any app, even though nothing is visible there. `EdgeSensor` is a frameless, translucent, always-on-top 116 x 116 window that stays at the anchor so it can notice a drag. The 0.1.7 fix set `WA_TransparentForMouseEvents`; that did not help, which fits the attribute affecting only Qt's own event dispatch while the native window still takes the click (inferred). A window that must receive a drag cannot also ignore clicks.

### N-002 — Decision / trigger to revisit

The rewrite keeps no window on screen while idle: a global mouse monitor watches for a file drag and shows the drop zone only for its duration (plan task T2, ADR-001). Do not reintroduce a standing sensor window.

### N-002 — Resolution

Resolved in 0.2.0. `drag_watch.rs` polls the mouse button and the drag pasteboard and shows the drop zone only during a file drag (the global event monitor first tried was not called on macOS 27, LOG L-005). Confirmed by the owner on 2026-11-15: the corner is clickable and a drag summons the zone (LOG L-005, L-009).

## N-001 — Menu bar icon click aborts the app on macOS 27

**Date:** 2026-11-15 · **Status:** resolved · **Related:** CHANGELOG v0.2.0, `app.py:2728-2765` (`_build_tray`, removed in 0.2.0), `~/Library/Logs/DiagnosticReports/tomd-2026-11-15-1421422.ips`, plan `tauri-rewrite`

### N-001 — Context

Reported by the owner: clicking the menu bar icon closes the app. Two crash reports from 2026-11-15 on macOS 27.0.1 show `SIGABRT` on the main thread: `NSSceneStatusItem` opens the status-item menu, `NSMenuTrackingSession` posts its begin-tracking notification, Qt's `libqcocoa` observer calls `-[NSEvent clickCount]` on an event that is not a mouse event, and AppKit's assertion handler throws. The fault is inside Qt's macOS plugin (PySide6 6.11), not in tomd's code.

### N-001 — Decision / trigger to revisit

Not patched in PySide6 `[owner: 2026-11-15]`. The rewrite uses Tauri's native tray menu, which removes Qt from the path. Whether a newer PySide6 fixes it was not checked.

### N-001 — Resolution

Resolved in 0.2.0: the menu is `src-tauri/src/tray.rs`, a native menu. Confirmed by the owner on 2026-11-15: the menu opens without a crash and its items work (LOG L-004).
