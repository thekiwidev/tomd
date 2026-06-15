# Spec: Docked Tray + UI Enhancements

Status: **DRAFT — awaiting approval** · Author: thekiwidev (dictated) + Claude · Date: 2026-06-15

## Objective

Make `tomd` always-accessible and polish the existing window.

Two independent bodies of work, shipped in order:

- **Phase 1 — UI enhancements** (small, ships first): fix three rough edges in the
  current main window so long filenames and narrow widths behave well, and so the
  window reopens at the size/position the user last left it.
- **Phase 2 — Docked Tray** (larger): a small, frameless, always-on-top mini-window
  pinned to a user-chosen screen corner/edge that stays open across all desktops.
  Drop a file on it → it converts (reusing the existing queue) → drag the converted
  `.md` back out. The full window is one click away. The app keeps running in the
  background with a tray/menu-bar icon so the dock is always reachable.

### Who / why

Power users batch-converting files don't want to hunt for the app window every time.
The tray turns conversion into "drag file → corner of screen → done", while the full
window remains for multi-file queue management.

### Non-goals (explicitly parked)

- **Arbitrary-file shelf / move semantics.** The earlier idea of using the tray as a
  temporary holding area to drag *any* files in and out with copy-vs-move behavior is
  **out of scope**. The tray is **conversion-only**: files in → markdown out. Drag-out
  always offers the converted `.md` as a **Copy** (same behavior as the existing
  `DragChip`); the original `.md` stays next to its source.
- No change to the conversion engine (`markitdown` CLI, sequential `QueueWorker`,
  `.md` written next to source). One running app = one shared queue.
- No cloud, no telemetry.

## Tech Stack

- Python ≥ 3.12, PySide6 ≥ 6.11 (Qt Widgets), single-file `app.py` + `backend.py`.
- Persistence: `QSettings("thekiwidev", "tomd")` (already in use).
- Packaging: PyInstaller. Targets: **macOS + Windows**.

## Commands

```
Dev (hot reload):  uv run python dev.py
Run once:          uv run python app.py
Build:             see scripts/ (PyInstaller)
```
No automated test suite exists today (see Testing Strategy).

## Project Structure (unchanged)

```
app.py          → All UI (Qt widgets, windows, workers)
backend.py      → environment detection, install, convert_file()
dev.py          → watchfiles hot-reload runner
docs/specs/     → this spec
assets/         → icons, screenshots
scripts/        → packaging
```

New code lands in `app.py` alongside existing classes unless it grows large enough to
warrant a split (decide at Plan time, not now).

## Code Style

Match the existing file exactly. Observed conventions:

- Qt Widgets, dark theme, custom `RowChip`/`ActionChip`/`DragChip` base widgets.
- Icons via `themed_icon(name, color, size)` / `icon_pixmap(...)`; never raw image files.
- Settings read/written inline: `self.settings.value(key, default, type=bool)`.
- Responsive layout handled in `resizeEvent` + a `_update_*_layout()` helper that
  toggles `setVisible(...)`, e.g. `FileRow._update_action_layout()`:

```python
def _update_action_layout(self):
    expanded = self.width() >= 460
    for w in self._action_widgets:
        w.setVisible(expanded)
    self.more_button.setVisible(not expanded)
```

## Testing Strategy

No unit-test harness exists; this is a GUI app driven manually via `uv run python dev.py`.
For this work:

- **Manual verification checklist per task** (defined in the Tasks section) is the bar.
- Each phase gets a smoke pass on **both macOS and Windows** before it's called done.
- If we add any pure-logic helper (e.g. corner→geometry math), cover it with a tiny
  `pytest` function so it's verifiable without a display. Adding `pytest` is "Ask first".

---

## Phase 1 — UI Enhancements (ships first)

All three apply to the existing main window / `FileRow`. They are independent of the tray.

### 1.1 Truncate long filenames

**Problem:** `FileRow.name_label` (app.py:466) is a plain `QLabel`; a very long filename
expands the row and pushes the action chips off the right edge.

**Requirement (decided):** The filename column gets a **maximum width** and uses a
**middle ellipsis** (`my-quarterly-rep…report.pdf`) so the file extension stays visible.
The action chips keep a fixed right-hand position regardless of name length. Full name
remains available on hover (tooltip) and via text selection.

**Acceptance:**
- A 120-character filename does not move the Copy/drag/Reveal chips.
- The elided label shows `…`; tooltip shows the full `source.name`.

### 1.2 Responsive action chips (icon-only at narrow widths)

**Problem / current state:** Today the row has a single hard breakpoint — below 460 px the
three chips disappear entirely and a `•••` menu button appears
(`_update_action_layout`, app.py:534).

**Requirement (decided):** One simple breakpoint at **560 px**:
- **Window ≥ 560 px:** chips show **icon + text** ("Copy MD", "drag .md", "Reveal").
- **Window < 560 px:** chips show **icon only** (text hidden; tooltips carry the label).

The window minimum is already 480 px, so icon-only always fits — the old `•••` collapse is
no longer needed. Implement as a text-visibility toggle on `RowChip` (e.g.
`set_text_visible(bool)`), driven from `_update_action_layout()`.

**Acceptance:**
- Dragging the window below 560 px hides chip text, leaving icon-only chips.
- Icon-only chips keep working tooltips and click/drag behavior.

### 1.3 Remember window size & position

**Problem:** `MainWindow.__init__` hardcodes `resize(620, 700)` (app.py:1002); geometry is
never saved or restored.

**Requirement (decided):** Persist the main window's **size AND position** to `QSettings`
on close and restore both on launch, clamped to the existing minimum
(`setMinimumSize(480, 460)`). If no saved geometry, fall back to the current default.

**Acceptance:**
- Resize/move the window, quit, relaunch → it reopens at the same size and position.
- Saved geometry off-screen (e.g. unplugged monitor) is clamped back onto a visible screen.

---

## Phase 2 — Docked Tray (larger, second)

### 2.1 Background app + tray/menu-bar icon

- App keeps running when the main window is closed (don't quit on last window close).
- A `QSystemTrayIcon` (menu-bar on macOS, system tray on Windows) provides:
  Show/Hide Dock · Open Full Window · Auto-convert toggle · Quit.

### 2.2 The dock window

- A **frameless, always-on-top** mini-window (`Qt.FramelessWindowHint |
  Qt.WindowStaysOnTopHint`, `Qt.Tool` so it stays out of the app switcher).
- **Pinned** flush to a user-chosen position: top-left, top-right, bottom-left,
  bottom-right, left-center, right-center (6 anchors). Position math derived from
  `QScreen.availableGeometry()`; recomputed on screen change / resolution change.
- **Visible on all desktops/Spaces (decided).** macOS: set NSWindow `collectionBehavior`
  (`canJoinAllSpaces`) via pyobjc → shows on every Space. Windows (v1): floats
  always-on-top on the **current** virtual desktop only; we do **not** attempt the
  hard "show on all virtual desktops" path.
- Closing the dock's X just **hides** it; the app keeps running (see 2.1). The dock is
  brought back or fully quit from the tray/menu-bar icon.
- Chosen anchor persists in `QSettings`.

### 2.3 Dock interaction (conversion-only)

- **Drop a file/folder** on the dock → added to the shared queue (`MainPage.add_files`).
- Honors the **same Auto-convert setting** as the main window. If on, conversion starts
  immediately; if off, dropped files accumulate and a **Convert** button runs them.
- Each finished file shows a compact entry with a **drag-out handle** that drags the
  converted `.md` (Copy) — reuse `DragChip`.
- An **Open** affordance reveals/raises the full main window.

### 2.4 Shared state

The dock and main window are two views over the **same** `MainPage` model / `QueueWorker`.
Decide at Plan time whether the dock embeds a slimmed `MainPage` or a separate compact
widget that calls into the same controller. Conversions started in one view must be
visible (or at least consistent) in the other.

---

## Boundaries

- **Always:** match existing widget/style conventions; persist via `QSettings`; keep one
  shared conversion queue; manually smoke-test on macOS and Windows before "done".
- **Ask first:** adding any dependency (e.g. `pyobjc`, `pytest`); splitting `app.py` into
  modules; changing the conversion/output contract; changing packaging in `scripts/`.
- **Never:** add cloud/telemetry; bundle `markitdown`; commit secrets; remove the existing
  main-window flow.

## Success Criteria

**Phase 1**
- [ ] Long filenames shorten with a middle ellipsis and never displace the action chips.
- [ ] Below 560 px the chips drop their text (icon-only); above 560 px they show icon+text.
- [ ] Window reopens at last size AND position; off-screen geometry is clamped on-screen.

**Phase 2**
- [ ] Closing the main window leaves the app running with a tray/menu-bar icon.
- [ ] Dock pins to any of the 6 anchors, persists the choice, and survives display changes.
- [ ] Dock stays visible across desktop/Space switches on macOS (Windows: best-effort,
      documented).
- [ ] Dropping a file on the dock converts it via the shared queue; the converted `.md`
      can be dragged out as a copy; Open raises the full window.

## Decisions (resolved)

1. **Responsive (1.2):** single breakpoint at **560 px** — icon+text above, icon-only below.
   No `•••` collapse.
2. **Long names (1.1):** **middle ellipsis**, full name on hover.
3. **Geometry (1.3):** persist **size and position**.
4. **Windows "all desktops" (2.2):** v1 floats on the **current** virtual desktop only
   (always-on-top); macOS shows on all Spaces.
5. **Dock close / quit:** dock X **hides**; only the tray/menu-bar **Quit** fully exits.

### Still to decide at Plan time (internal, not user-facing)

- **Dock content model (2.4):** embed a slimmed `MainPage` variant vs. a separate compact
  widget over a shared controller. An implementation detail — chosen during planning.

## Risks

- **Windows virtual-desktop "show on all"** has no clean public API → likely degrade (Q4).
- **`pyobjc` dependency** for macOS all-Spaces behavior — needs "Ask first" approval and
  must be macOS-gated so Windows builds don't pull it.
- **Frameless window dragging/HiDPI/multi-monitor** anchor math is fiddly; isolate it in a
  testable helper.
- **No test harness** → regressions caught only by manual passes; keep changes incremental.
