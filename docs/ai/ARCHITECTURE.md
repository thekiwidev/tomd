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

Describes tomd 0.2.0 (2026-11-15). Decision record: [`decisions/ADR-001-tauri-shell-python-sidecar.md`](./decisions/ADR-001-tauri-shell-python-sidecar.md). The 0.1.x PySide6 app is gone from the tree; its last state is tag `v0.1.11`.

## 1. Repository shape

Three parts in one repository `[verified]`:

| Path | Role |
| --- | --- |
| `src-tauri/` | The shell (Tauri v2, Rust): windows, menu bar icon, settings, drag watcher, Finder Quick Action, sidecar process |
| `src/` | The UI (React, TypeScript, Tailwind v4), built by Vite into `dist-ui/` and loaded by all three windows |
| `sidecar.py`, `backend.py`, `links.py` | The sidecar (Python, standard library only): everything that touches MarkItDown |
| `tests/` | pytest for `links.py` and `sidecar.py` |
| `scripts/build_macos.sh` | Release build: frozen sidecar, Tauri app, DMG |
| `docs/index.html` | Static marketing site (GitHub Pages) |

## 2. Boundaries and dependency directions

UI → shell (Tauri commands and events) → sidecar (JSON lines). Nothing points the other way except events.

- The **UI** has no file or process access. It reaches the sidecar only through `src/ipc.ts` and the system only through shell commands and four plugins (`dialog` open, `opener` reveal, `drag` start, `autostart`).
- The **shell** does not interpret sidecar messages: `sidecar.rs` writes one request line (`sidecar_send`) and emits each stdout line as the event `sidecar-message`. Replies are matched to requests by id in `src/ipc.ts`; ids carry the window label because every window hears every reply.
- The **sidecar** knows nothing about windows. `backend.py` imports no UI code.

## 3. Cross-boundary contracts

- **MarkItDown CLI:** `backend.convert_file` runs `markitdown <source> -o <output>`. tomd depends on its exit code, stderr text and, for YouTube, on the output actually containing a transcript (MarkItDown exits 0 on a failed transcript fetch).
- **Sidecar protocol** (docstring of `sidecar.py`): request `{"id", "method", "params"}`; replies `{"id", "event": "log", "line"}` any number of times, then one `{"id", "event": "result", "ok", "data" | "error"}`. One thread per request. When stdin closes it finishes running requests and exits. Methods: `environment_report`, `find_foreign_markitdowns`, `invalidate_health_cache`, `install_markitdown`, `install_homebrew_python`, `repair_markitdown`, `convert_file` (`output` optional, default beside the source), `collect_paths`, `youtube_plan`.
- **Shell commands:** `get_settings`, `set_setting`, `sidecar_send`, `hide_dropzone`, `show_main_window`, `set_toast`, `get_toast`, `quick_action_available`, `take_opened`, `copy_markdown` (reads `.md` files only, so it is not a general file read).
- **Events:** `settings-changed`, `sidecar-message`, `menu-action` (`youtube`, `settings`), `sources-opened` (shell to main window); `queue-changed` (main window to the others); `sources-dropped`, `queue-run` (drop zone to main window); `toast-changed` (shell to toast window).

## 4. Persistence

`tauri-plugin-store`, file `settings.json` in the app's data directory, owned by `settings.rs`: `dropzone_enabled`, `dock_anchor`, `drag_mode`, `auto_convert_on_drop`, `menu_bar_only`, `finder_action`, `youtube_folder`. Rust owns them because several have effects outside the webview (Dock icon, tray check mark, drag watcher, Finder entry); every write validates, applies, saves and emits `settings-changed`. Main window geometry: `tauri-plugin-window-state`. The managed MarkItDown venv lives under `backend.app_data_dir()`. `~/Library/Services/Convert to Markdown.workflow` is generated. No database. 0.1.x `QSettings` values are not migrated.

## 5. Integrations

MarkItDown (CLI), `uv` (bootstrapped at runtime when missing), Homebrew (optional Python install), YouTube (through MarkItDown only), Finder (Automator service bundle, open-document events), macOS login items (`tauri-plugin-autostart`, LaunchAgent).

## 6. Queue / worker

One queue, in the main window's webview, which exists for the life of the app even while its window is hidden.

- `src/queue.ts`: pure reducer over `{rows, batch}`. Actions `add` (with `enqueue` and `background`), `enqueue`, `start`, `finish`, `stop`, `clear`, `remove`, `select`, `seen`. A row's id is its source path or canonical URL, so adding twice is a no-op. Stop lets the running file finish and returns waiting rows to pending. `toastOf` derives the status toast from rows flagged `background`. Tested in `src/queue.test.ts`.
- `src/useQueue.ts`: starts the next queued row when none is running (one `convert_file` at a time) and emits `queue-changed` on every change.
- `DropZone.tsx` and `Toast.tsx` hold no queue; they render what the main window broadcasts.

## 7. Deployment shape

`scripts/build_macos.sh`: PyInstaller one-folder build of `sidecar.py` into `build/sidecar/tomd-sidecar/`; `bun run tauri build --bundles app` with that folder added as the resource `sidecar` and an ad-hoc signature (both passed by `--config`, not in `tauri.conf.json`, so a debug build needs no frozen sidecar); `hdiutil` wraps `dist/tomd.app` (24 MB) into `dist/tomd.dmg` (12 MB). Unsigned beyond ad hoc, not notarised. `.github/workflows/release.yml` runs the script on a `v*` tag and attaches `tomd.dmg`. macOS only; the site links Windows visitors to `v0.1.11`.

`sidecar.rs` chooses the sidecar: debug builds run `.venv/bin/python sidecar.py` from the repository (path compiled in); release builds run `Contents/Resources/sidecar/tomd-sidecar`.

## 8. Structural constraints

- **No window on screen while idle.** `drag_watch.rs` polls (120 ms) the left mouse button and the drag pasteboard's change count; a new count carrying file URLs shows the drop zone for that drag only. A standing sensor window swallows clicks (NOTES N-002) and must not come back. A global `NSEvent` monitor is not an alternative: it is not called on macOS 27 (LOG L-005).
- **The drop zone and toast are shown without activating tomd** (`windows::order_front`, `orderFrontRegardless`, all Spaces): they appear while another app is in use.
- **State used before `setup` must be managed on the builder.** macOS can deliver `RunEvent::Opened` before `setup` runs; `Opened` in `lib.rs` exists for that. A panic there aborts the app inside the Apple Event handler (LOG L-014).
- **Debug builds do not touch the user's machine setup:** `migrate_login_item` is skipped under `debug_assertions`, and `quick_action.rs` writes the Finder entry only from an `.app` outside any `target/` folder.
- **The tray is a native menu** (`tray.rs`); no UI toolkit handles its events (NOTES N-001).
- Vite builds to `dist-ui/`; `cargo check` fails if that directory is missing.

## 9. Shell and UI modules

- `src-tauri/src/lib.rs`: builder, plugins, `Shell` (state shared by tray, drag watcher and commands: `dropzone_enabled`, `pinned`, `drag_active`, `drag_mode`, `toast`, the tray's auto-convert item), `Opened`, close-hides-main, `--background`, `ignore_saved_window_state`.
- `settings.rs`: load, validate, apply, save. `tray.rs`: the menu. `windows.rs`: `anchor_position` (six anchors, clamped to the work area), show / hide / compact for the drop zone, the toast commands. `drag_watch.rs` with `shake.rs` (pure shake detector): the drag modes `show`, `shake`, `small`, `option`. `quick_action.rs`: generates the service bundle from `src-tauri/quick-action/`. `sidecar.rs`: the sidecar process.
- `src/main.tsx` picks the root by window label: `main` → `MainWindow.tsx`, `dropzone` → `DropZone.tsx`, `toast` → `Toast.tsx`.
- `MainWindow.tsx`: toolbar, list, progress, in-window toast; shows `SetupPage.tsx` when the environment report has no MarkItDown and a banner when it is unhealthy (`environment.ts`: shallow report first, then the health probe). `SettingsPage.tsx`, `YouTubeDialog.tsx` (validation and file name preview come from the sidecar's `youtube_plan`), `FileRow.tsx`, `LogBox.tsx`, `ui.tsx` (button, switch, copy / reveal / drag-out), `settings.ts`, `ipc.ts`.
