# Changelog

All notable changes to tomd are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/); versions follow [SemVer](https://semver.org/).

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

[0.1.2]: https://github.com/thekiwidev/tomd/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/thekiwidev/tomd/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/thekiwidev/tomd/releases/tag/v0.1.0
