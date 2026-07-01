# Changelog

All notable changes to tomd are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/); versions follow [SemVer](https://semver.org/).

## [0.1.7] — 2026-07-01

### Fixed
- Python 3.10+ detection no longer relies on a hardcoded version list — Python 3.14 and newer are now found correctly, including python.org's Framework-style installs that don't land a `python3` symlink on a GUI app's minimal PATH.
- The "Install MarkItDown" button no longer stays disabled when no Python/uv is detected yet — install now bootstraps `uv` (which can fetch its own isolated Python) automatically, so setup works on a bare machine.
- The drop zone's hot-corner sensor no longer creates a dead click zone: it now lets clicks pass through to whatever's underneath while idle, instead of silently swallowing them.

### Added
- Copy and Reveal buttons on the drop zone's file entries, matching the main window.
- "Install Python via Homebrew instead" as an explicit alternative to the automatic uv bootstrap.
- Landing page download buttons now link directly to the latest GitHub release build instead of the releases page, and detect Windows to serve the right build automatically.

## [0.1.6] — 2026-06-15

### Added
- **Background app + menu-bar icon.** tomd now keeps running when the main window is closed. A white menu-bar/tray icon (the app's `#` + arrow logo) gives quick access; clicking it opens a menu — Open window view · Open drop zone · Settings · Auto-convert · Quit — without forcing the window open.
- **Smart drop zone.** A frameless, always-on-top mini-window pinned to a screen corner of your choosing, sharing the same conversion queue as the main window. It stays hidden until you drag a file toward its corner: a translucent "ghost" appears for ~1s and then opens so you can drop. Drag away without dropping and it dismisses. Finished markdown can be dragged straight back out.
- **Settings window** (menu bar, the window's gear button, or ⌘,): enable/position the drop zone, auto-convert on drop, run in the menu bar only (hide the Dock icon), and start tomd at login.
- macOS: the drop zone shows on every Space; menu-bar-only mode hides the Dock icon (via `pyobjc`, an optional macOS-only dependency).
- Start-at-login support (macOS LaunchAgent / Windows startup).

### Changed
- The auto-convert toggle moved out of the window view into Settings and the menu bar.
- On a narrow window, **all** toolbar buttons (Add Files, Clear, Run, …) collapse to icon-only, not just the per-row actions.
- Clearing the list is now universal — clearing from the window or the drop zone clears both.

### Fixed
- The drop zone now re-arms after every use (previously it stopped triggering after the first drop-and-close).

## [0.1.5] — 2026-06-15

### Added
- Action buttons (Copy MD, drag .md, Reveal) collapse to icon-only when the window is narrower than 560 px; tooltips carry the labels
- Main window now remembers its size **and** position between launches, clamping back on-screen if the saved spot lands off every display

### Changed
- File names are middle-elided (the extension stays visible) and shrink responsively with the window instead of overflowing; the full name shows on hover
- The converted-file sub-line (`→ output.md`) is likewise middle-elided so it no longer widens the row

### Fixed
- The file list never scrolls horizontally — rows always fit the window width, so the action chips stay visible at any size

## [0.1.4] — 2026-06-12

### Changed
- `RowChip` base class: Copy MD, drag .md and Reveal are now all identical widgets (same layout, padding, icon size, font) — no more QPushButton vs QWidget rendering mismatch
- Chip label font updated to Inter to match the app body font
- All non-accent QPushButton labels (Add Files, Clear, Run/Stop, etc.) changed from font-weight 600 → 500
- Title ("tomd") lightened to font-weight 500, size 24 px, letter-spacing 0.015 em
- Count label ("Converting 6/6 — …") now uses JetBrains Mono
- Spinner rotation fixed: QPainter-based rotation around the logical center eliminates wobble
- Filename and sub-line ("→ output.md") spacing increased for breathing room
- Row actions collapse to a ••• chip below 460 px window width; right-click always shows the action menu

---

## [0.1.3] — 2026-06-12

### Changed
- Icon sizes balanced: drag grip increased to 12 px, Copy MD / Reveal reduced to 9 px so all three row-action elements are visually consistent
- Fonts aligned with the landing page: `Space Grotesk` for the app title, `JetBrains Mono` for mono / chip / sub-line elements, `Inter` for all body text

### Removed
- `.mov` source videos replaced by GIFs in assets (`.mov` files deleted from repo)

---

## [0.1.2] — 2026-06-11

### Fixed
- Drag chip background now renders correctly — added `WA_StyledBackground` so Qt paints QSS styles on the widget

### Changed
- All row and toolbar icons reduced in size for a tighter, less cluttered look
- Grabbing cursor shown while dragging a `.md` file out of the app

### Added
- Per-row `SelectBox` — a dedicated checkbox on the left of each row; only that area has a pointer cursor (the rest of the row is inert)
- File icon shown in the sub-line initially instead of the raw parent path; replaced by status text once conversion begins

---

## [0.1.1] — 2026-06-11

### Fixed
- Drag chip ("drag .md") now correctly renders its grip icon and label — base class changed from `QLabel` to `QWidget`

### Added
- Multi-select: click any file row to select/deselect it; **Remove Selected** and **Reveal Selected** buttons appear in the toolbar for the active selection
- Dragging a `.md` out of the app no longer re-triggers the drop zone inside the same window

---

## [0.1.0] — 2026-06-11

First public release.

### Added
- Drag & drop conversion of files and folders to Markdown via the device's `markitdown` CLI
- First-run setup: detects Python 3.10+ / uv / markitdown, installs `markitdown[all]` into a private venv (`~/Library/Application Support/tomd/venv` on macOS) with live command output
- Sequential conversion queue with per-file states (pending / queued / converting / done / error), animated spinner, and overall progress bar
- Auto-convert on drop (persisted setting, off by default)
- Stop button: halts the queue after the current file
- Per-file actions: copy Markdown to clipboard, drag the `.md` out of the app, reveal in Finder / Explorer
- Toast notifications for failures and batch completion
- Themed inline SVG icon set (Lucide), dark UI
- macOS `.app` / `.dmg` and Windows `.exe` builds; release automation on `v*` tags
- Landing page (GitHub Pages, `docs/`)

[0.1.7]: https://github.com/thekiwidev/tomd/releases/tag/v0.1.7
[0.1.6]: https://github.com/thekiwidev/tomd/releases/tag/v0.1.6
[0.1.5]: https://github.com/thekiwidev/tomd/releases/tag/v0.1.5
[0.1.4]: https://github.com/thekiwidev/tomd/releases/tag/v0.1.4
[0.1.3]: https://github.com/thekiwidev/tomd/releases/tag/v0.1.3
[0.1.2]: https://github.com/thekiwidev/tomd/releases/tag/v0.1.2
[0.1.1]: https://github.com/thekiwidev/tomd/releases/tag/v0.1.1
[0.1.0]: https://github.com/thekiwidev/tomd/releases/tag/v0.1.0
