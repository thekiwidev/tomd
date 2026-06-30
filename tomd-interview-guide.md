# tomd — Interview Preparation & Technical Learning Guide

> **Project:** tomd — A drag-and-drop desktop GUI for Microsoft MarkItDown  
> **Stack:** Python 3.12+, PySide6 (Qt Widgets), PyInstaller, uv  
> **Platforms:** macOS, Windows  
> **Repo:** https://github.com/thekiwidev/tomd  
> **Current Version:** 0.1.6

---

## Table of Contents

1. [The Elevator Pitch](#1-the-elevator-pitch)
2. [High-Level Architecture](#2-high-level-architecture)
3. [Project Structure & File Responsibilities](#3-project-structure--file-responsibilities)
4. [Core Design Decisions & Rationale](#4-core-design-decisions--rationale)
5. [Deep Dive: The GUI (app.py)](#5-deep-dive-the-gui-apppy)
6. [Deep Dive: Backend & Environment (backend.py)](#6-deep-dive-backend--environment-backendpy)
7. [Deep Dive: Native OS Integration (native.py)](#7-deep-dive-native-os-integration-nativepy)
8. [The Conversion Queue & Threading Model](#8-the-conversion-queue--threading-model)
9. [Drag-and-Drop Architecture](#9-drag-and-drop-architecture)
10. [Responsive UI & Elided Text](#10-responsive-ui--elided-text)
11. [The Dock / Drop Zone System](#11-the-dock--drop-zone-system)
12. [Settings & Persistence](#12-settings--persistence)
13. [Build, Packaging & CI/CD](#13-build-packaging--cicd)
14. [Interview Q&A — Technical Questions](#14-interview-qa--technical-questions)
15. [Interview Q&A — Behavioral / Design Questions](#15-interview-qa--behavioral--design-questions)
16. [Changelog Evolution — What Each Version Taught](#16-changelog-evolution--what-each-version-taught)
17. [Quick Reference — Code Snippets](#17-quick-reference--code-snippets)

---

## 1. The Elevator Pitch

**tomd** is a thin desktop GUI that sits on top of Microsoft's **MarkItDown** CLI. It lets users drag and drop files (or entire folders) onto a window and converts them to Markdown — one at a time, sequentially, with progress tracking and per-file actions.

The key philosophy: **tomd does NOT bundle MarkItDown**. It detects whether the user already has it installed, and if not, installs it into a private virtual environment. The app itself is just a UI shell — all conversion happens via `markitdown <file> -o <file>.md` subprocess calls running on the user's own machine.

**Why this matters:** No cloud dependency, no bundled runtime bloat, no licensing issues. The app is a pure GUI layer.

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Layer                            │
│  ┌──────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Main Window  │  │  Dock Zone  │  │  Menu Bar / Tray    │  │
│  │ (MainPage)   │  │ (DockWindow)│  │  (QSystemTrayIcon)  │  │
│  └──────┬───────┘  └──────┬──────┘  └─────────┬───────────┘  │
│         │                 │                   │              │
│         └─────────────────┴───────────────────┘              │
│                           │                                  │
│                    AppController                             │
│                           │                                  │
│         ┌─────────────────┴───────────────────┐              │
│         │         MainPage (shared)            │              │
│         │  - File rows, queue, progress        │              │
│         │  - QueueWorker (QThread)             │              │
│         └─────────────────┬───────────────────┘              │
│                           │                                  │
│                    ┌──────┴──────┐                           │
│                    │  backend.py  │                           │
│                    │  - env check │                           │
│                    │  - install   │                           │
│                    │  - convert   │                           │
│                    └──────┬──────┘                           │
│                           │                                  │
│                    ┌──────┴──────┐                           │
│                    │  markitdown  │  ← external CLI           │
│                    │   CLI tool   │                           │
│                    └─────────────┘                           │
└─────────────────────────────────────────────────────────────┘
```

**Three layers:**
1. **UI Layer** — `MainWindow`, `DockWindow`, `EdgeSensor`, `SettingsWindow`, tray icon
2. **Controller Layer** — `AppController` wires everything together; `MainPage` owns the shared queue
3. **Backend Layer** — `backend.py` handles environment detection, installation, and subprocess conversion

---

## 3. Project Structure & File Responsibilities

| File | Lines | Purpose |
|------|-------|---------|
| `app.py` | ~2,077 | **Entire GUI** — all Qt widgets, windows, workers, styling, drag-and-drop, dock, settings, tray |
| `backend.py` | ~172 | **Device plumbing** — env detection, markitdown resolution, setup install, `convert_file()` |
| `native.py` | ~148 | **OS-level integrations** — macOS Dock hide, all-Spaces window, start-at-login (LaunchAgent / Registry) |
| `dev.py` | ~31 | **Hot-reload runner** — `watchfiles` restarts `app.py` on save |
| `pyproject.toml` | ~21 | Project metadata, dependencies (`pyside6>=6.11.1`, `pyobjc` macOS-only), dev deps |
| `scripts/build_macos.sh` | ~23 | PyInstaller → `dist/tomd.app` + `dist/tomd.dmg` |
| `scripts/build_windows.ps1` | ~8 | PyInstaller → `dist\tomd.exe` |
| `.github/workflows/release.yml` | ~50 | GitHub Actions — builds macOS + Windows on `v*` tags, auto-releases |

---

## 4. Core Design Decisions & Rationale

### 4.1 "Thin GUI" — Never Bundle MarkItDown

**Decision:** The app does not ship with MarkItDown baked in. It either finds an existing installation on the user's PATH, or installs it into a private virtualenv at `~/Library/Application Support/tomd/venv`.

**Rationale:**
- MarkItDown is actively developed; bundling it would mean stale versions
- Avoids licensing/compliance questions (we're not redistributing Microsoft's code)
- The app stays small (~MBs instead of 100MB+ if bundling Python + ML deps)
- Users who already have MarkItDown get zero friction

**How it works:**
```python
# backend.py
def resolve_markitdown():
    on_path = which("markitdown")
    if on_path:
        return on_path
    managed = venv_executable("markitdown")
    if managed.exists():
        return str(managed)
    return None
```

---

### 4.2 Sequential Conversion (One at a Time)

**Decision:** The `QueueWorker` processes one file per subprocess, not parallel.

**Rationale:**
- MarkItDown can be CPU/memory-intensive (especially with LLM-based image transcription)
- Running multiple instances simultaneously could overwhelm the user's machine
- Sequential processing gives predictable resource usage and clearer per-file error attribution
- A single progress bar and status per row is simpler UX

**Implementation:** `QueueWorker` extends `QThread` with a `queue.Queue`. The `run()` loop blocks on `queue.get()` until a `None` sentinel stops it.

---

### 4.3 Single-File UI (`app.py` is ~2,000 lines)

**Decision:** The entire GUI lives in one file despite its size.

**Rationale:**
- For a solo project, module boundaries add friction without team benefit
- Qt widgets are tightly coupled by signals/slots — splitting them often creates circular imports
- The spec document explicitly says: "All new code stays in `app.py` unless Phase 2 pushes it past ~1500 lines"
- PyInstaller single-file entry point is simpler

**Trade-off:** The file is large, but it's linear and searchable. Classes are ordered: icons → workers → widgets → pages → windows → controller → main.

---

### 4.4 Inline SVG Icons (No Image Assets)

**Decision:** All icons are Lucide SVG paths stored as strings in `ICON_PATHS`, rendered at runtime via `QSvgRenderer` into `QPixmap`/`QIcon`.

**Rationale:**
- No image files to bundle, lose, or scale badly
- Icons are theme-aware — tint them to any color on the fly
- HiDPI/Retina automatically handled by `setDevicePixelRatio(2)`
- The app icon itself (hash + arrow glyphs) is also inline SVG paths extracted from `assets/icon.svg`

```python
def icon_pixmap(name: str, color: str, size: int = 16) -> QPixmap:
    svg = f'<svg ... stroke="{color}" ...>{ICON_PATHS[name]}</svg>'
    renderer = QSvgRenderer(QByteArray(svg.encode()))
    pixmap = QPixmap(size * 2, size * 2)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    pixmap.setDevicePixelRatio(2)
    return pixmap
```

---

### 4.5 Platform-Native Behaviors via Optional Dependencies

**Decision:** macOS-specific features (hide Dock icon, show on all Spaces) use `pyobjc-framework-Cocoa`, but it's **soft-imported** with graceful degradation.

**Rationale:**
- Windows builds don't pull macOS-only dependencies
- If pyobjc is missing, the app still runs — the dock just won't follow Spaces
- Feature detection, not platform assumption: `if QGuiApplication.platformName() == "cocoa":`

```python
# native.py
def _appkit():
    try:
        import AppKit
        return AppKit
    except Exception:
        return None
```

---

## 5. Deep Dive: The GUI (app.py)

### 5.1 Class Hierarchy

```
QObject
├── QueueWorker (QThread)          # sequential conversion queue
├── SetupWorker (QThread)          # markitdown installation
├── Toast (QLabel)                 # transient notification
├── RowChip (QWidget)              # base: icon + label chip
│   ├── ActionChip (RowChip)       # clickable chip
│   └── DragChip (RowChip)         # draggable chip (drag .md out)
├── SelectBox (QLabel)             # checkbox toggle on file rows
├── FileRow (QFrame)               # one file in the queue
├── SetupPage (QWidget)            # first-run setup screen
├── MainPage (QWidget)             # main conversion UI
├── MainWindow (QMainWindow)       # main app window
├── DockEntry (QFrame)             # compact file row in dock
├── DockWindow (QWidget)           # frameless always-on-top dock
├── EdgeSensor (QWidget)           # hot-corner drag detector
├── SettingsWindow (QWidget)       # preferences panel
└── AppController                   # owns all windows, tray, wiring
```

### 5.2 Custom Widgets Worth Knowing

#### `RowChip` / `ActionChip` / `DragChip`
- **Purpose:** Unified visual spec for all chip buttons (Copy MD, drag .md, Reveal)
- **Why it matters:** Earlier versions (v0.1.0) had `QPushButton` vs `QWidget` rendering mismatches. By v0.1.4, everything inherits `RowChip` for identical layout, padding, font, and icon size.
- **Responsive:** `set_text_visible(bool)` toggles icon+text vs icon-only at narrow widths.

#### `DragChip`
- **Purpose:** Let users drag the converted `.md` file out of the app into Finder, Slack, an editor, etc.
- **How it works:**
  1. `mousePressEvent` records press position
  2. `mouseMoveEvent` checks if movement exceeds `QApplication.startDragDistance()`
  3. Creates a `QDrag` with `QMimeData` containing `QUrl.fromLocalFile(str(self.md_path))`
  4. `drag.exec(Qt.CopyAction)` — the file is copied, not moved

#### `SelectBox`
- Custom checkbox built from `QLabel`, not `QCheckBox`
- Gives full visual control (border, background, checkmark icon) without fighting Qt's native checkbox styling
- Only the 18×18 box area has `PointingHandCursor`; the rest of the row is inert

#### `FileRow`
- **State machine:** `PENDING → QUEUED → RUNNING → DONE/ERROR`
- **Animated spinner:** `QTimer` at 80ms rotates a `QPainter`-rendered pixmap around its logical center (fixed wobble from v0.1.4)
- **Elided text:** `fontMetrics().elidedText(..., Qt.ElideMiddle, ...)` — middle ellipsis so the extension stays visible
- **Responsive actions:** Below 560px window width, action chips collapse to icon-only; tooltips carry the labels

### 5.3 Styling Approach

- **Global QSS string** (`STYLE`) applied via `app.setStyleSheet(...)`
- **Object IDs** (`#fileRow`, `#dragChip`) and **dynamic properties** (`dragOver`, `state`, `selected`) for state-dependent styling
- `style().unpolish(widget); style().polish(widget)` forces Qt to re-evaluate QSS when properties change
- Custom checkbox indicator image is written to disk as an SVG because `QSS` can only load indicator images from files

---

## 6. Deep Dive: Backend & Environment (backend.py)

### 6.1 PATH Augmentation for GUI Apps

**Problem:** On macOS, GUI apps launched from Finder have a minimal PATH (no `/opt/homebrew/bin`, no `~/.local/bin`). `shutil.which("markitdown")` would fail even if the user has it installed via Homebrew.

**Solution:** `env_with_path()` appends common directories before resolving executables:
```python
EXTRA_PATH_DIRS = [
    "/opt/homebrew/bin",
    "/usr/local/bin",
    str(Path.home() / ".local" / "bin"),
    str(Path.home() / ".cargo" / "bin"),
]
```

### 6.2 Installation Strategy (uv-first, fallback to venv+pip)

**Preferred path:** If `uv` is installed, use it — it's fast, can download its own Python, and handles the venv + install in one shot.

**Fallback:** Find a system Python >= 3.10, create a `venv`, upgrade pip, install `markitdown[all]`.

**Why streaming output matters:** The setup screen shows a live terminal log. `run_streamed()` uses `subprocess.Popen` with `stdout=subprocess.PIPE` and yields lines to the UI via a signal.

### 6.3 Conversion Subprocess

```python
def convert_file(markitdown_exe: str, source: Path) -> tuple[bool, str]:
    output = source.with_suffix(".md")
    proc = subprocess.run(
        [markitdown_exe, str(source), "-o", str(output)],
        capture_output=True, text=True, ...
    )
    if proc.returncode == 0 and output.exists():
        return True, str(output)
    return False, (proc.stderr or proc.stdout or "...")[-500:]
```

- Output is always written next to the source file (`source.with_suffix(".md")`)
- Error messages are truncated to last 500 chars to avoid UI overflow
- `creationflags=subprocess.CREATE_NO_WINDOW` on Windows prevents console popups

---

## 7. Deep Dive: Native OS Integration (native.py)

### 7.1 macOS Dock Icon Hide (Menu-Bar-Only Mode)

```python
def set_dock_icon_visible(visible: bool) -> bool:
    appkit = _appkit()
    if not IS_MAC or appkit is None:
        return False
    app = appkit.NSApplication.sharedApplication()
    policy = (appkit.NSApplicationActivationPolicyRegular if visible
              else appkit.NSApplicationActivationPolicyAccessory)
    app.setActivationPolicy_(policy)
    return True
```

- `Accessory` policy = no Dock icon, no app switcher entry, but menu bar icon stays
- Soft-imported; returns `False` if pyobjc is missing

### 7.2 Show Window on Every Space (macOS)

```python
def show_on_all_spaces(window) -> bool:
    import objc
    view = objc.objc_object(c_void_p=int(window.winId()))
    nswindow = view.window()
    behavior = (nswindow.collectionBehavior()
                | appkit.NSWindowCollectionBehaviorCanJoinAllSpaces
                | appkit.NSWindowCollectionBehaviorFullScreenAuxiliary)
    nswindow.setCollectionBehavior_(behavior)
```

- Gets the native `NSWindow` from the Qt `winId()` via `objc.objc_object`
- Sets `CanJoinAllSpaces` so the dock follows the user across Spaces
- Also `FullScreenAuxiliary` so it floats above full-screen apps

### 7.3 Start at Login

**macOS:** Writes a `LaunchAgent` plist to `~/Library/LaunchAgents/me.thekiwidev.tomd.plist` with `RunAtLoad=true`.

**Windows:** Writes to `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run` via `winreg`.

**Launch command adapts:** When frozen (PyInstaller), uses `sys.executable`. When running from source, uses `[sys.executable, "app.py"]`.

---

## 8. The Conversion Queue & Threading Model

### 8.1 Why `QThread` and not `asyncio` or `concurrent.futures`?

- Qt's signal/slot mechanism is thread-safe and integrates seamlessly with the GUI
- `QThread` lives in the Qt event loop — no need to bridge between asyncio and Qt
- The worker emits `job_started`, `job_done`, `job_failed` signals that auto-marshal to the main thread for UI updates

### 8.2 QueueWorker Implementation

```python
class QueueWorker(QThread):
    job_started = Signal(object)       # emits the FileRow
    job_done = Signal(object, str)     # (row, output_path)
    job_failed = Signal(object, str)   # (row, error_message)

    def run(self):
        while True:
            row = self._queue.get()
            if row is None:              # None sentinel = stop
                break
            self.job_started.emit(row)
            ok, detail = backend.convert_file(self.markitdown_exe, row.source)
            (self.job_done if ok else self.job_failed).emit(row, detail)
```

### 8.3 Stop Behavior

"Stop" doesn't kill the running subprocess — it drains the pending queue and lets the current file finish. This avoids corrupting output or leaving temp files.

```python
def stop_queue(self):
    drained = self.worker.clear_pending()   # drain queue.Queue
    for row in drained:
        row.set_state(PENDING)
    self.batch_total -= len(drained)
```

---

## 9. Drag-and-Drop Architecture

### 9.1 Drop In (Files → App)

`MainWindow` accepts drops at the window level. `dragEnterEvent` validates:
- `event.source() is None` — rejects drags *from inside the app* (prevents dragging a `.md` chip back onto the window and re-triggering conversion)
- `mimeData.hasUrls()` — only accept file URLs

`collect_paths()` expands dropped URLs:
- Single file → add directly
- Folder → recursively walk, filtering by `SUPPORTED_EXTENSIONS`

### 9.2 Drag Out (App → Finder/Editor)

The `DragChip` initiates a `QDrag` with `QMimeData.setUrls([QUrl.fromLocalFile(...)])`. The action is `Qt.CopyAction` — the original `.md` stays next to its source.

---

## 10. Responsive UI & Elided Text

### 10.1 Middle Ellipsis for Filenames

```python
def _elide_labels(self):
    fm = self.name_label.fontMetrics()
    self.name_label.setText(
        fm.elidedText(self._full_name, Qt.ElideMiddle, max(self.name_label.width(), 0))
    )
```

- `Qt.ElideMiddle` truncates the middle: `my-quarterly-rep…report.pdf`
- The extension stays visible, which is critical for user recognition
- Called in `resizeEvent` so it re-flows as the window resizes

### 10.2 Toolbar Button Collapse

At window width < 560px, all toolbar buttons (Add Files, Clear, Run, etc.) collapse to icon-only. The labels are stored in `self._labeled_buttons` and restored when the window widens.

---

## 11. The Dock / Drop Zone System

### 11.1 Why a Dock?

Power users don't want to hunt for the app window every time. The dock turns conversion into: **drag file → corner of screen → done**.

### 11.2 Ghost Drop Zone Pattern

```
User drags file toward screen corner
         ↓
  EdgeSensor (hot-corner, invisible)
         ↓
   "approached" signal fires
         ↓
  DockWindow appears as ghost (62% opacity)
         ↓
   After 1s dwell → solidifies (opened)
         ↓
   User drops file → pins open, converts
         ↓
   Drag leaves without dropping → dismisses, re-arm sensor
```

### 11.3 Shared State Between Main Window and Dock

- `MainPage` is the **sole owner** of the `QueueWorker` and file model
- `DockWindow` holds a reference to `MainPage` and calls `controller.add_files()`
- The dock listens to `MainPage.row_converted` / `row_failed` / `cleared` signals to mirror status
- **One queue, two views** — they never diverge

### 11.4 Edge Sensor

A small 116×116 widget at the dock's anchor corner. It stays invisible until a drag approaches. Its `dragEnterEvent` summons the ghost; `dropEvent` opens the dock and forwards the files.

---

## 12. Settings & Persistence

### 12.1 QSettings

All settings use `QSettings("thekiwidev", "tomd")` — cross-platform, no file I/O code needed.

Persisted keys:
- `auto_convert_on_drop` — bool
- `window_geometry` — `QByteArray` from `saveGeometry()` / `restoreGeometry()`
- `dock_anchor` — string (one of 6 positions)
- `dropzone_enabled` — bool
- `menu_bar_only` — bool

### 12.2 Geometry Clamping

On launch, if the saved window position is off every screen (e.g., unplugged monitor), the window is recentered on the primary screen:
```python
def _clamp_on_screen(self):
    frame = self.frameGeometry()
    if any(s.availableGeometry().intersects(frame) for s in QGuiApplication.screens()):
        return
    available = QGuiApplication.primaryScreen().availableGeometry()
    self.move(available.center() - self.rect().center())
```

---

## 13. Build, Packaging & CI/CD

### 13.1 PyInstaller Configuration

**macOS:** `--windowed --name tomd --icon assets/tomd.icns --osx-bundle-identifier dev.thekiwidev.tomd`
- Produces `dist/tomd.app` bundle
- DMG is built via `hdiutil create` with an `/Applications` symlink for drag-to-install UX

**Windows:** `--onefile --windowed --name tomd`
- Single `.exe` for simplicity

### 13.2 GitHub Actions Release Flow

```
Developer pushes tag vX.Y.Z
         ↓
  GitHub Actions triggers
         ↓
  ┌──────────────┐  ┌──────────────┐
  │ build-macos  │  │ build-windows│
  │ (macos-latest)│  │ (windows-latest)│
  │ → tomd.dmg   │  │ → tomd.exe   │
  └──────────────┘  └──────────────┘
         ↓                   ↓
         └─────────┬─────────┘
                   ↓
            release job
         (softprops/action-gh-release)
```

- Uses `astral-sh/setup-uv@v7` for fast Python setup
- `permissions: contents: write` allows attaching artifacts to releases

---

## 14. Interview Q&A — Technical Questions

### Q: Why didn't you use a web-based UI (Electron, Tauri)?
**A:** The app is a thin wrapper around a CLI tool. A native Qt app:
- Starts instantly (no Chromium overhead)
- Has native drag-and-drop, file manager integration, and menu bar APIs
- Packages to a small binary (~tens of MB, not 100MB+)
- PySide6 is mature and Python-native — no JS/bridge complexity

### Q: How do you handle the fact that GUI apps on macOS have a stripped PATH?
**A:** `backend.py` explicitly augments `PATH` with common directories (`/opt/homebrew/bin`, `~/.local/bin`, etc.) before calling `shutil.which()`. Without this, a user-installed `markitdown` via Homebrew would be invisible.

### Q: Why `QThread` instead of Python's `threading` module?
**A:** `QThread` integrates with Qt's signal/slot thread-safety. When the worker emits `job_done`, Qt automatically marshals the signal to the main thread so the UI can be updated safely. Raw `threading` would require manual `queue` + `window.after()` or similar bridges.

### Q: How does the spinner work without an animated GIF?
**A:** A `QTimer` (80ms) increments a rotation angle. On each tick, a fresh `QPixmap` is created, a `QPainter` rotates around the logical center, draws the static loader icon, and the result is set as the label's pixmap. This avoids bundling animation assets and gives crisp rendering at any DPI.

### Q: Why did you choose a single `app.py` instead of splitting into modules?
**A:** For a solo project, the overhead of module imports and cross-file signal wiring isn't worth it. `app.py` is linear and fully searchable. The contributing guide explicitly states: "All new code stays in `app.py` unless it grows past ~1500 lines."

### Q: How do you prevent the app from converting a file that's already converted?
**A:** `MainPage.add_files()` tracks `existing = {row.source for row in self.rows}`. Duplicate drops are silently deduplicated. Also, `convert_pending()` only enqueues rows whose state is `PENDING` or `ERROR`.

### Q: What's the rationale behind the "ghost" drop zone?
**A:** An always-visible dock would be visually intrusive. The ghost pattern keeps the screen clean until the user actually needs to convert something — they just drag toward the corner, the dock appears, they drop, and it can hide again. It's an affordance that stays out of the way.

### Q: How does `DragChip` not re-trigger the drop zone when dragging within the app?
**A:** `MainWindow.dragEnterEvent` checks `if event.source() is not None: event.ignore()`. Drags originating from inside the app (including `DragChip`) have a non-None source, so they're rejected.

### Q: How do you handle the case where the user has no Python installed?
**A:** The setup screen checks for Python 3.10+ via `find_python()`, which probes `python3.13`, `python3.12`, ..., `python`. If none found, the install button is disabled and the user is told to install Python first. If `uv` is present, it can bootstrap its own Python — so the button stays enabled if `uv` is found even without a system Python.

### Q: Why middle-ellipsis instead of end-ellipsis for filenames?
**A:** File extensions are the most important identifier. `Qt.ElideMiddle` keeps `…report.pdf` readable, whereas `Qt.ElideRight` would show `my-quarterly-repo…` and the extension would be lost.

### Q: How do you test the geometry helper without a display?
**A:** `dock_geometry()` is a pure function — it takes an anchor string, a `QRect` screen, a `QSize` dock, and a margin, and returns a `QRect`. It has no widget dependencies, so it can be unit-tested with plain pytest without a Qt display server.

### Q: Why does the dock use `Qt.Tool` window flag?
**A:** `Qt.Tool` keeps the window out of the app switcher (Alt-Tab / Cmd-Tab) and taskbar, which is appropriate for an accessory utility window. Combined with `FramelessWindowHint` and `WindowStaysOnTopHint`, it becomes a floating utility panel.

### Q: How do you handle platform differences for "start at login"?
**A:** `native.py` uses completely different mechanisms:
- macOS: LaunchAgent plist in `~/Library/LaunchAgents/`
- Windows: Registry key in `HKEY_CURRENT_USER\...\Run`
- Both are guarded by `IS_MAC` / `IS_WIN` checks; unsupported platforms return `False`

### Q: Why `QSettings` instead of a JSON config file?
**A:** `QSettings` is cross-platform (registry on Windows, plist/defaults on macOS, INI on Linux), handles type serialization, and requires zero file path management. It also follows the OS conventions for where apps store preferences.

---

## 15. Interview Q&A — Behavioral / Design Questions

### Q: Walk me through a feature you added from spec to shipping.
**A:** The docked drop zone (v0.1.6). Started with a spec doc (`docs/specs/tray-and-ui-enhancements.md`) that defined two phases: UI polish first (low risk), then the dock. I broke it into 9 tasks (T1–T9) with acceptance criteria. The dock required:
1. Background app lifetime + tray icon (T4)
2. A pure geometry helper for anchor positioning (T5)
3. Frameless window shell (T6)
4. macOS all-Spaces integration via pyobjc (T7)
5. Shared controller wiring so dock and main window see the same queue (T8)
6. Conversion UX with auto-convert respect and drag-out (T9)

Each phase had a manual verification checklist. I shipped UI polish first, then the dock, updating `CHANGELOG.md` and `pyproject.toml` version before tagging.

### Q: What's a trade-off you made?
**A:** Single-file `app.py` vs. modular structure. I chose single-file for velocity and simplicity in a solo project, accepting that the file is large. The trade-off is that code navigation is slightly harder, but there are no import cycles, no module boundary debates, and PyInstaller entry point is trivial.

### Q: How did you decide what goes in the menu bar vs. the window UI?
**A:** Auto-convert started as a visible checkbox in the main window (v0.1.0). As features grew, the window chrome was getting cluttered. I moved auto-convert into Settings and the tray menu (v0.1.6) because:
- It's a "set and forget" preference, not an action
- The tray menu is always accessible even when the window is hidden
- The dock also needs to respect the same setting, so centralizing it in `QSettings` makes sense

### Q: How do you handle regressions without automated tests?
**A:** Each task in the spec has a manual verification checklist. I smoke-test both macOS and Windows before releasing. For pure logic (like `dock_geometry()`), I add pytest coverage. The app is intentionally simple enough that manual testing is sufficient — the risk of complex state bugs is low because the architecture is: drop → queue → subprocess → signal → UI update.

### Q: What would you do differently if starting over?
**A:**
- Add the dock concept earlier in the design — retrofitting a background-app model onto a "quit on last window close" app required careful lifecycle changes
- Consider `pytest-qt` for automated GUI smoke tests
- Potentially split `app.py` into `widgets.py`, `pages.py`, `dock.py` once the project had multiple contributors

---

## 16. Changelog Evolution — What Each Version Taught

### v0.1.0 — First Release
**What I learned:**
- The core architecture works: thin GUI over CLI, QThread queue, inline SVG icons
- PyInstaller + GitHub Actions can produce cross-platform releases automatically
- The landing page (`docs/index.html`) is essential for credibility

### v0.1.1 — Multi-select + Drag Chip Fix
**What I learned:**
- `QLabel` base class doesn't render QSS background styles reliably; `QWidget` with `WA_StyledBackground` is needed
- Drag-out needs to be explicitly prevented from re-entering the same window

### v0.1.2 — SelectBox + Spinner Fix
**What I learned:**
- Custom widgets (SelectBox) are worth it for visual consistency
- QPainter rotation around the logical center (not physical pixels) eliminates wobble on HiDPI screens
- Cursor feedback (`OpenHandCursor` / `ClosedHandCursor`) significantly improves drag UX

### v0.1.3 — Font Alignment + Asset Cleanup
**What I learned:**
- Fonts should match the landing page brand (`Space Grotesk`, `JetBrains Mono`, `Inter`)
- GIFs are better than `.mov` for README compatibility across GitHub renderers

### v0.1.4 — RowChip Unification + Responsive Actions
**What I learned:**
- Having `QPushButton` and `QWidget` chips in the same row causes visual inconsistency (border-radius, padding, hover states). A single `RowChip` base class fixes everything.
- A single responsive breakpoint (560px) is cleaner than multiple breakpoints
- `WA_StyledBackground` is critical for custom widgets with QSS backgrounds

### v0.1.5 — Window Geometry + Better Elision
**What I learned:**
- `saveGeometry()` / `restoreGeometry()` is the correct Qt way to persist window state
- Always clamp restored geometry to available screens — users unplug monitors
- Middle-eliding the sub-line (`→ output.md`) is as important as the filename

### v0.1.6 — Background App + Dock
**What I learned:**
- `setQuitOnLastWindowClosed(False)` changes the entire app lifecycle — you need a tray/menu-bar quit path
- Ghost drop zones are a great UX pattern for "always available but not intrusive"
- pyobjc soft-importing is essential for cross-platform packaging
- The sensor → ghost → dock → dismiss state machine needs careful timer management (`_dwell`, `_orphan`, `_rearm_sensor`)
- Clearing must be universal: clearing from the window clears the dock and vice versa

---

## 17. Quick Reference — Code Snippets

### 17.1 Thread-Safe Signal Pattern
```python
class QueueWorker(QThread):
    job_done = Signal(object, str)

    def run(self):
        ok, detail = backend.convert_file(...)
        self.job_done.emit(row, detail)   # auto-marshalled to main thread
```

### 17.2 Dynamic QSS Property Update
```python
widget.setProperty("state", "done")
widget.style().unpolish(widget)
widget.style().polish(widget)
```

### 17.3 Drag Out with QDrag
```python
drag = QDrag(self)
mime = QMimeData()
mime.setUrls([QUrl.fromLocalFile(str(self.md_path))])
drag.setMimeData(mime)
drag.exec(Qt.CopyAction)
```

### 17.4 Middle Ellipsis
```python
fm = label.fontMetrics()
label.setText(fm.elidedText(full_text, Qt.ElideMiddle, available_width))
```

### 17.5 Window Geometry Persistence
```python
# On close:
settings.setValue("window_geometry", self.saveGeometry())

# On init:
saved = settings.value("window_geometry")
if isinstance(saved, QByteArray) and not saved.isEmpty():
    self.restoreGeometry(saved)
```

### 17.6 macOS Native Window Manipulation
```python
import objc
view = objc.objc_object(c_void_p=int(window.winId()))
nswindow = view.window()
behavior = nswindow.collectionBehavior() | AppKit.NSWindowCollectionBehaviorCanJoinAllSpaces
nswindow.setCollectionBehavior_(behavior)
```

### 17.7 Platform-Gated Dependency
```python
# pyproject.toml
dependencies = [
    "pyobjc-framework-Cocoa>=10.0; sys_platform == 'darwin'",
]

# native.py
def _appkit():
    try:
        import AppKit
        return AppKit
    except Exception:
        return None
```

---

## Closing Notes

This guide covers the **what**, **why**, and **how** of every major decision in tomd. Before an interview, review:
1. The **elevator pitch** (Section 1) — be able to explain it in 30 seconds
2. **Architecture diagram** (Section 2) — draw it on a whiteboard if needed
3. **Three design decisions** (Section 4) — pick the ones most relevant to the role
4. **Technical deep dives** (Sections 5–12) — know the code patterns cold
5. **Q&A responses** (Sections 14–15) — adapt these to your speaking style
6. **Changelog evolution** (Section 16) — shows iterative thinking and polish

Good luck! 🚀
