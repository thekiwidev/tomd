---
doc: ARCHITECTURE
purpose: "The current architectural model: workspaces, services, dependency directions, contracts, persistence, integrations, deployment shape, structural constraints"
authority: canonical
hosts_rules: []
mirrors_rules: []
last_reviewed: "2026-11-15"
---

# ARCHITECTURE — tomd

> How the repository is structured **now** — not how it was planned, not a directory listing. Document boundaries and why they exist, non-obvious constraints, what breaks if you touch a given thing, and where authority lives. Every statement is `[verified]` against the repository or tagged otherwise.

> **This describes the PySide6 app as it is on 2026-11-15.** It is being replaced by the design in [`decisions/ADR-001-tauri-shell-python-sidecar.md`](./decisions/ADR-001-tauri-shell-python-sidecar.md); rewrite this document as each part of [`plans/active/tauri-rewrite.md`](./plans/active/tauri-rewrite.md) lands.

## 1. Repository shape

A flat Python project, no packages `[verified]`:

| File | Lines | Role |
| --- | --- | --- |
| `app.py` | 2,783 | The whole PySide6 UI: styles, icons, widgets, windows, tray, `AppController` |
| `backend.py` | 811 | System side: locate Python and `uv`, install / verify / repair MarkItDown in a private venv, run one conversion, translate errors. Standard library only |
| `native.py` | 148 | macOS Dock-icon hiding and all-Spaces windows (pyobjc), login item (LaunchAgent plist on macOS, `Run` registry key on Windows) |
| `dev.py` | 31 | Hot-reload runner (`watchfiles`) |
| `scripts/` | — | `build_macos.sh`, `build_windows.ps1` (PyInstaller) |
| `docs/index.html` | — | Static marketing site |

## 2. Boundaries and dependency directions

`app.py` imports `backend` and `native`; neither imports `app` or Qt. Conversion, install and repair run on `QThread` workers in `app.py` (`QueueWorker`, `SetupWorker`, `HomebrewSetupWorker`, `RepairWorker`, `EnvProbeWorker`) that call `backend` functions and report through Qt signals.

`AppController` (`app.py:2521`) is the one object that owns the main window, the drop zone (`DockWindow`), the hot-corner (`EdgeSensor`), the settings window and the tray, and applies persisted settings.

## 3. Cross-boundary contracts

- **MarkItDown CLI:** `backend.convert_file` runs `markitdown <source> -o <output>` as a subprocess. tomd depends on its exit code, stderr text and, for YouTube, on the output actually containing a transcript (MarkItDown exits 0 on a failed transcript fetch).
- **`backend` to UI:** long operations take an `on_line` callback for streamed log lines and return `(ok, error_or_detail)`. `environment_report()` returns a dict (`markitdown`, `health.missing_features`, and the Python / `uv` findings).

## 4. Persistence

`QSettings("thekiwidev", "tomd")`: `dropzone_enabled`, `dock_anchor`, `auto_convert_on_drop`, `menu_bar_only`, the YouTube output folder and `window_geometry`. The managed MarkItDown venv lives under `backend.app_data_dir()`. No database.

## 5. Integrations

MarkItDown (CLI), `uv` (bootstrapped at runtime when missing), Homebrew (optional Python install), YouTube (through MarkItDown only).

## 6. Queue / worker

`QueueWorker` converts sequentially, one file at a time; Stop drains the queue and returns queued rows to pending.

## 7. Deployment shape

PyInstaller app bundle: `tomd.app` in a UDZO `tomd.dmg` on macOS (about 100 MB, unsigned), `tomd.exe` on Windows. `.github/workflows/release.yml` builds both on a `v*` tag and attaches them to a GitHub release. The site links to `releases/latest/download/`.

## 8. Structural constraints

- `backend.py` must not import Qt or any UI module (it becomes the sidecar).
- `EdgeSensor` is a permanent always-on-top window at the drop-zone anchor; this is the cause of the dead-space defect (NOTES N-002) and must not be reproduced in the rewrite.
- The tray uses `QSystemTrayIcon`, which crashes on macOS 27 (NOTES N-001).
