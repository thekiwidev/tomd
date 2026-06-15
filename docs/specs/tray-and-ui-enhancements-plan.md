# Implementation Plan: Docked Tray + UI Enhancements

Status: **DRAFT — awaiting approval** · Date: 2026-06-15
Spec: [tray-and-ui-enhancements.md](tray-and-ui-enhancements.md)

## Overview

Two bodies of work, built in order. **Phase 1** is three small, independent polish fixes to
the existing main window (ships first, low risk). **Phase 2** adds the frameless docked
tray: a background-running app with a menu-bar/tray icon and a small always-on-top window
that converts dropped files through the existing queue.

## Architecture Decisions

- **Single conversion owner.** `MainPage` stays the sole owner of the `QueueWorker` and the
  file model. The dock does **not** get its own worker.
- **Dock = separate compact widget, MainPage = controller.** Rather than embedding a
  slimmed `MainPage`, the dock is a small standalone widget that calls
  `main_page.add_files(...)` and listens to the same `QueueWorker` signals
  (`job_started`/`job_done`/`job_failed`). This resolves spec open-item 2.4 with no large
  refactor and guarantees the two views never diverge on queue state.
- **Anchor math is a pure helper.** Corner/edge → on-screen `QRect` is a standalone function
  (`dock_geometry(anchor, screen_rect, dock_size)`), unit-tested without a display.
- **Platform behavior is feature-detected, not assumed.** macOS all-Spaces uses `pyobjc`
  behind a `sys.platform == "darwin"` guard; everything still runs if `pyobjc` is absent
  (dock just won't follow Spaces). Windows uses Qt flags only.
- **All new code stays in `app.py`** unless Phase 2 pushes it past ~1500 lines, at which
  point we split out a `dock.py` (decided during Phase 2, not now).

## Dependency Graph

```
Phase 1 (independent of each other and of Phase 2)
  T1 filename elision
  T2 responsive chips
  T3 remember geometry

Phase 2
  T4 background lifetime + tray icon  ─┬─→ T6 dock window shell ──→ T7 macOS all-Spaces
  T5 anchor geometry helper ───────────┘                              │
                                          T8 shared dock controller ──┴─→ T9 dock conversion UX
```

---

## Phase 1: UI Enhancements

### Task 1: Middle-ellipsis filenames with a max width

**Description:** Stop long filenames from pushing the action chips off the row. Give
`FileRow.name_label` a maximum width and render the name with a middle ellipsis; expose the
full name via tooltip (selection already works).

**Acceptance criteria:**
- [ ] A 120-char filename does not move the Copy/drag/Reveal chips.
- [ ] Name shows a middle ellipsis (extension stays visible); tooltip shows full `source.name`.

**Verification:**
- [ ] Manual: `uv run python dev.py`, drop a file with a very long name, resize the window.
- [ ] Build/run: app launches without errors.

**Dependencies:** None
**Files likely touched:** `app.py` (`FileRow.__init__`, a small elision helper / `resizeEvent`)
**Estimated scope:** S (1 file)

### Task 2: Responsive chips — icon+text ≥560 px, icon-only <560 px

**Description:** Add `set_text_visible(bool)` to `RowChip` and replace the current single
460 px `•••` collapse in `FileRow._update_action_layout` with one 560 px breakpoint that
toggles chip text. Tooltips already carry each label for the icon-only state.

**Acceptance criteria:**
- [ ] ≥560 px: chips show icon + text. <560 px: icon only, tooltips intact.
- [ ] Copy/drag/Reveal still work in icon-only mode; no `•••` button remains.

**Verification:**
- [ ] Manual: drag the window across 560 px and watch text show/hide.
- [ ] Manual: in icon-only mode, Copy copies, drag drags, Reveal opens the folder.

**Dependencies:** None
**Files likely touched:** `app.py` (`RowChip`, `FileRow._update_action_layout`, remove `more_button` path)
**Estimated scope:** S (1 file)

### Task 3: Remember window size and position

**Description:** Save the main window geometry to `QSettings` on close and restore it on
launch, clamped onto a visible screen; fall back to the current 620×700 default when nothing
is saved.

**Acceptance criteria:**
- [ ] Resize/move, quit, relaunch → reopens at the same size AND position.
- [ ] Geometry saved off-screen (e.g. unplugged monitor) is clamped back on-screen.

**Verification:**
- [ ] Manual: move/resize, quit, relaunch; confirm restored.
- [ ] Manual: hand-edit saved geometry off-screen, relaunch, confirm it snaps back.

**Dependencies:** None
**Files likely touched:** `app.py` (`MainWindow.__init__`, `MainWindow.closeEvent`)
**Estimated scope:** S (1 file)

### Checkpoint: Phase 1
- [ ] App launches and converts as before (no regression to the main flow).
- [ ] All three acceptance sets pass on macOS.
- [ ] Quick pass on Windows.
- [ ] **Review with human, commit, optionally ship as its own release.**

---

## Phase 2: Docked Tray

### Task 4: Background lifetime + tray/menu-bar icon

**Description:** Stop the app quitting when the main window closes
(`setQuitOnLastWindowClosed(False)`) and add a `QSystemTrayIcon` with a menu:
Open Full Window · Show/Hide Dock (wired in T6) · Auto-convert toggle · Quit. Quit is the
only path that fully exits.

**Acceptance criteria:**
- [ ] Closing the main window leaves the app running with a visible tray/menu-bar icon.
- [ ] Tray menu can re-open the main window and fully Quit.
- [ ] Auto-convert toggle in the menu stays in sync with the main-window checkbox via `QSettings`.

**Verification:**
- [ ] Manual: close main window → app alive in menu bar; Open re-shows it; Quit exits.

**Dependencies:** None (but precedes T6)
**Files likely touched:** `app.py` (`main()`, new `TrayController` / `MainWindow` wiring)
**Estimated scope:** M (1 file, touches app lifecycle)

### Task 5: Anchor geometry helper (pure + unit-tested)

**Description:** A standalone `dock_geometry(anchor, screen_rect, dock_size, margin)` returning
the `QRect` for each of the 6 anchors (top/bottom × left/right, plus left-center,
right-center). No widgets — pure geometry. Add a small `pytest` covering each anchor.
**Adding `pytest` is an "Ask first" item — confirm before this task.**

**Acceptance criteria:**
- [ ] Returns correct rects for all 6 anchors within a given screen rect + margin.
- [ ] Never returns a rect that falls outside the screen's available area.

**Verification:**
- [ ] `uv run pytest tests/test_dock_geometry.py` passes.

**Dependencies:** None (but precedes T6) · **Ask-first:** add `pytest` dev dependency
**Files likely touched:** `app.py` (helper), `tests/test_dock_geometry.py`
**Estimated scope:** S (1–2 files)

### Task 6: Dock window shell (frameless, on-top, pinned, persisted)

**Description:** A frameless, always-on-top `Qt.Tool` window positioned via `dock_geometry`
at the saved anchor (default bottom-right), with a small chrome: an anchor picker, an Open
button, and a close-X that hides it. Anchor choice persists in `QSettings`; geometry
recomputes on screen/resolution change. No conversion yet — it just appears and pins.

**Acceptance criteria:**
- [ ] Dock shows frameless, on top, snapped to the chosen anchor; choice persists across launches.
- [ ] Close-X hides the dock; tray Show/Hide toggles it; Open raises the main window.
- [ ] Re-pins correctly after a resolution/display change.

**Verification:**
- [ ] Manual: cycle all 6 anchors, relaunch, confirm persisted; change display scaling and re-check.

**Dependencies:** T4, T5
**Files likely touched:** `app.py` (new `DockWindow`), tray wiring from T4
**Estimated scope:** M (1 file)

### Task 7: macOS all-Spaces; Windows current-desktop float

**Description:** On macOS, set NSWindow `collectionBehavior` (`canJoinAllSpaces`) via
`pyobjc` so the dock follows across Spaces, guarded by `sys.platform == "darwin"` and a soft
import (no-op if `pyobjc` missing). On Windows, the Qt always-on-top flag from T6 already
gives current-desktop float — verify only. **Adding `pyobjc` (macOS-only) is "Ask first".**

**Acceptance criteria:**
- [ ] macOS: switching Spaces keeps the dock visible.
- [ ] Windows: dock floats on top of the current virtual desktop; no crash without all-Spaces.
- [ ] App still runs if `pyobjc` is not installed.

**Verification:**
- [ ] Manual macOS: create a second Space, swipe across, dock stays.
- [ ] Manual Windows: switch virtual desktop, confirm float on current.

**Dependencies:** T6 · **Ask-first:** add macOS-gated `pyobjc` dependency
**Files likely touched:** `app.py`, `pyproject.toml` (platform marker)
**Estimated scope:** S (1–2 files)

### Task 8: Shared dock controller wiring

**Description:** Connect the dock to `MainPage` as controller: dropping on the dock calls
`main_page.add_files(...)`; the dock subscribes to the existing `QueueWorker` signals to
mirror status on its own compact rows. No second worker; no duplicate enqueue.

**Acceptance criteria:**
- [ ] A file dropped on the dock appears in the shared queue and converts once.
- [ ] Dock and main window never disagree about a file's state.

**Verification:**
- [ ] Manual: drop on dock with main window open; confirm single conversion, consistent status in both.

**Dependencies:** T6
**Files likely touched:** `app.py` (`DockWindow` ↔ `MainPage` signal wiring)
**Estimated scope:** M (1 file)

### Task 9: Dock conversion UX

**Description:** Flesh out the dock's interaction: drop target highlight; respects the shared
Auto-convert setting (on → convert immediately; off → accumulate + a **Convert** button);
each finished file shows a compact entry with a `DragChip` to drag the `.md` out (Copy); an
**Open** affordance raises the full window.

**Acceptance criteria:**
- [ ] Auto-convert on: dropped file converts immediately; the `.md` can be dragged out as a copy.
- [ ] Auto-convert off: files accumulate; **Convert** runs them through the shared queue.
- [ ] Open raises the full window; original `.md` stays next to its source.

**Verification:**
- [ ] Manual: both auto-convert states; drag a converted `.md` into Finder/Explorer and an editor.

**Dependencies:** T8
**Files likely touched:** `app.py` (`DockWindow`)
**Estimated scope:** M (1 file)

### Checkpoint: Phase 2
- [ ] All Phase 2 acceptance sets pass on macOS.
- [ ] Windows pass: dock floats on current desktop, conversion + drag-out work.
- [ ] No regression to the main-window flow or to Phase 1 behavior.
- [ ] Update `CHANGELOG.md` and README; review with human before release.

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Windows "show on all virtual desktops" has no clean API | Med | Scoped out in spec; v1 floats current desktop only (T7). |
| `pyobjc` adds a macOS dependency / packaging weight | Med | macOS-gated, soft-imported; "Ask first" before T7; app runs without it. |
| Frameless anchor math wrong on HiDPI / multi-monitor | Med | Isolated in pure `dock_geometry` helper with unit tests (T5). |
| Dock + main window queue divergence | High | Single `QueueWorker` owner; dock is a view, not an owner (T8). |
| No existing test harness | Low | Manual checklists per task; add `pytest` only for the geometry helper. |

## Open Questions (need human input before the noted tasks)

- **Before T5:** OK to add `pytest` as a dev dependency for the geometry unit test?
- **Before T7:** OK to add `pyobjc` (macOS-only) for the all-Spaces behavior?

## Suggested Execution Order

1. **T1 → T2 → T3** (Phase 1), Checkpoint, commit/ship.
2. **T4 → T5 → T6** (dock foundation), Checkpoint.
3. **T7 → T8 → T9** (Spaces + conversion), Checkpoint, release.
