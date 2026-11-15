---
doc: context/CHANGELOG
purpose: Agent-facing compressed copy of ../../../CHANGELOG.md; never edited by hand
authority: derived
source: ../../../CHANGELOG.md
source_sha256: c72d05117bdae3f148ab9ddb1cc55b162b4f09c2ba85971074a17b0b7b1ea994
generated_at: 2026-11-15
register: caveman-ultra
---

# CHANGELOG — agent-facing context (derived)

Format: Keep a Changelog; SemVer. Newest first.

## [0.1.11] — 2026-08-06

### Changed
- Share links converted, not refused: `youtu.be/_0A2BnRYVCo` and `youtube.com/watch?v=_0A2BnRYVCo` both accepted, rewritten to form MarkItDown understands.
- Link validation names each case: Shorts and live streams not supported yet; playlists and channels not single videos; mistyped id = bad id; missing `https://` said so. Every message ends with where to get working link.
- Shorts, live, embed, playlist links rejected outright. Previously accepted, passed to MarkItDown, which does not recognise them: conversion appeared to succeed, produced page of YouTube footer links.
- Link field carries standing note of what it accepts.

## [0.1.10] — 2026-08-06

### Fixed
- Failed YouTube transcript no longer looks like success. MarkItDown exits 0 when it cannot fetch transcript: YouTube converter gives up, generic HTML converter picks page up, `.md` = YouTube footer (About, Press, Copyright, © Google). tomd checks transcript came back, deletes bogus file, says what went wrong.
- YouTube links normalised before conversion. MarkItDown YouTube converter recognises only URLs beginning exactly `https://www.youtube.com/watch?`, reads id from `v` parameter. `youtu.be`, `/shorts/`, `/live/`, bare `youtube.com` fell through to generic HTML converter silently. Every accepted shape rewritten to canonical form.
- 429 from somewhere other than YouTube no longer blames YouTube.

## [0.1.9] — 2026-08-06

### Fixed
- Conversion failures explain themselves. Refused YouTube fetch used to surface as `HTTPError: 429 Client Error: Too Many Requests for url: https://www.google.com/sorry/index?continue=…`. Now: "YouTube is refusing requests from this network — it returns a bot check instead of the video page. Turn off any VPN, or try another network."
- Same for: captions turned off, no transcript in supported language, video unavailable, age-restricted, missing MarkItDown dependencies (points at Settings → Repair). Unrecognised still shows underlying exception.

### Known issues
- YouTube blocks transcript fetches at IP level from some networks (VPNs, shared/CGNAT, datacenter ranges). Every video fails identically; YouTube serves bot check. Usually temporary; different network (phone hotspot) = reliable workaround.
- MarkItDown sends no `User-Agent` fetching URLs; sites with user-agent policy (Wikipedia) reject with HTTP 403. Upstream; does not affect local files or YouTube links, only sources tomd accepts.

## [0.1.8] — 2026-08-06

### Added
- **Repair MarkItDown**, in Settings. Shows version, available file formats, which Python; rebuilds on one click: private environment deleted, MarkItDown build caches cleared, everything installed again, fetching compatible Python first if device has none. MarkItDown installs of other Pythons detected, listed; removing them = opt-in checkbox.
- First-run setup screen offers same repair when MarkItDown present but cannot convert. Previously Install button greyed out there, dead end.
- **YouTube transcripts.** YouTube button in toolbar, "Add YouTube video…" in menu bar. Paste link, give title; transcript saved as `<title-slug>.md` (lowercase, hyphenated) into folder chosen once, remembered. File name previewed live; title optional (video id used instead).

### Fixed
- MarkItDown install verified, not just detected. tomd used to accept any existing `markitdown` file. When pip could not resolve `markitdown[all]` it backtracked to 0.0.2 (predates `[all]` extra), reported success: CLI converted CSV and text, failed every PDF, Word, PowerPoint, Excel. Installs now checked for version and each format's dependencies.
- Installs request `markitdown[all]>=0.1.0`, try device Pythons newest-first, step down only when one cannot produce working CLI. Floor, not pin.
- `markitdown` on PATH no longer wins automatically; must pass same health check. Partially-installed system copy could shadow working managed one.
- `uv` bootstrap no longer dies with TLS certificate error on python.org macOS Framework builds (no CA store until `Install Certificates.command` run). Falls back to curl and system trust store.
- Conversion failures show real error (`HTTPError: 429 Client Error: Too Many Requests`) instead of slice of traceback from last 500 characters.
- Startup no longer waits on MarkItDown health check; runs in background, window appears immediately.

## [0.1.7] — 2026-07-01

### Fixed
- Python 3.10+ detection no longer relies on hardcoded version list: Python 3.14 and newer found, including python.org Framework-style installs with no `python3` symlink on GUI app's minimal PATH.
- "Install MarkItDown" button no longer stays disabled when no Python/uv detected: install bootstraps `uv` (fetches own isolated Python), setup works on bare machine.
- Drop zone hot-corner sensor no longer creates dead click zone: lets clicks pass through while idle.

### Added
- Copy and Reveal buttons on drop zone file entries, matching main window.
- "Install Python via Homebrew instead" as explicit alternative to automatic uv bootstrap.
- Landing page download buttons link directly to latest GitHub release build, detect Windows to serve right build.

## [0.1.6] — 2026-06-15

### Added
- **Background app + menu-bar icon.** tomd keeps running when main window closed. White menu-bar/tray icon (app `#` + arrow logo); click opens menu: Open window view · Open drop zone · Settings · Auto-convert · Quit; does not force window open.
- **Smart drop zone.** Frameless, always-on-top mini-window pinned to chosen screen corner, shares conversion queue with main window. Hidden until file dragged toward corner: translucent "ghost" appears ~1s, then opens for drop. Drag away without dropping: dismisses. Finished markdown draggable back out.
- **Settings window** (menu bar, window gear button, or ⌘,): enable/position drop zone, auto-convert on drop, menu bar only (hide Dock icon), start at login.
- macOS: drop zone on every Space; menu-bar-only hides Dock icon (via `pyobjc`, optional macOS-only dependency).
- Start-at-login (macOS LaunchAgent / Windows startup).

### Changed
- Auto-convert toggle moved from window view into Settings and menu bar.
- Narrow window: **all** toolbar buttons (Add Files, Clear, Run, …) collapse to icon-only, not just per-row actions.
- Clearing list universal: clearing from window or drop zone clears both.

### Fixed
- Drop zone re-arms after every use (previously stopped triggering after first drop-and-close).

## [0.1.5] — 2026-06-15

### Added
- Action buttons (Copy MD, drag .md, Reveal) collapse to icon-only when window narrower than 560 px; tooltips carry labels.
- Main window remembers size **and** position between launches, clamps back on-screen if saved spot off every display.

### Changed
- File names middle-elided (extension stays visible), shrink with window; full name on hover.
- Converted-file sub-line (`→ output.md`) likewise middle-elided.

### Fixed
- File list never scrolls horizontally; rows fit window width, action chips stay visible.

## [0.1.4] — 2026-06-12

### Changed
- `RowChip` base class: Copy MD, drag .md, Reveal identical widgets (layout, padding, icon size, font); no QPushButton vs QWidget mismatch.
- Chip label font Inter, matching app body font.
- Non-accent QPushButton labels (Add Files, Clear, Run/Stop, etc.) font-weight 600 → 500.
- Title ("tomd") font-weight 500, size 24 px, letter-spacing 0.015 em.
- Count label ("Converting 6/6 — …") uses JetBrains Mono.
- Spinner rotation fixed: QPainter-based rotation around logical center, no wobble.
- Filename and sub-line ("→ output.md") spacing increased.
- Row actions collapse to ••• chip below 460 px window width; right-click always shows action menu.

## [0.1.3] — 2026-06-12

### Changed
- Icon sizes balanced: drag grip 12 px, Copy MD / Reveal 9 px.
- Fonts aligned with landing page: `Space Grotesk` app title, `JetBrains Mono` mono / chip / sub-line, `Inter` body.

### Removed
- `.mov` source videos replaced by GIFs in assets (`.mov` deleted from repo).

## [0.1.2] — 2026-06-11

### Fixed
- Drag chip background renders: added `WA_StyledBackground` so Qt paints QSS styles.

### Changed
- Row and toolbar icons reduced in size.
- Grabbing cursor while dragging `.md` out of app.

### Added
- Per-row `SelectBox`: dedicated checkbox left of each row; only that area has pointer cursor.
- File icon in sub-line initially instead of raw parent path; replaced by status text once conversion begins.

## [0.1.1] — 2026-06-11

### Fixed
- Drag chip ("drag .md") renders grip icon and label: base class `QLabel` → `QWidget`.

### Added
- Multi-select: click file row to select/deselect; **Remove Selected**, **Reveal Selected** toolbar buttons for active selection.
- Dragging `.md` out of app no longer re-triggers drop zone inside same window.

## [0.1.0] — 2026-06-11

First public release.

### Added
- Drag & drop conversion of files and folders to Markdown via device's `markitdown` CLI.
- First-run setup: detects Python 3.10+ / uv / markitdown, installs `markitdown[all]` into private venv (`~/Library/Application Support/tomd/venv` on macOS) with live command output.
- Sequential conversion queue, per-file states (pending / queued / converting / done / error), animated spinner, overall progress bar.
- Auto-convert on drop (persisted setting, off by default).
- Stop button: halts queue after current file.
- Per-file actions: copy Markdown to clipboard, drag `.md` out of app, reveal in Finder / Explorer.
- Toast notifications for failures and batch completion.
- Themed inline SVG icon set (Lucide), dark UI.
- macOS `.app` / `.dmg` and Windows `.exe` builds; release automation on `v*` tags.
- Landing page (GitHub Pages, `docs/`).

Release links: `https://github.com/thekiwidev/tomd/releases/tag/<tag>` for v0.1.11, v0.1.10, v0.1.9, v0.1.8, v0.1.7, v0.1.6, v0.1.5, v0.1.4, v0.1.3, v0.1.2, v0.1.1, v0.1.0.
