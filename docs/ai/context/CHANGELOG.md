---
doc: context/CHANGELOG
purpose: Agent-facing compressed copy of ../../../CHANGELOG.md; never edited by hand
authority: derived
source: ../../../CHANGELOG.md
source_sha256: a3d3e67f09258aa1561c51d964b671738e845e0288afad5e8f22ec3ba78850c0
generated_at: 2026-11-15
register: caveman-ultra
---

# CHANGELOG — agent-facing context (derived)

Format: Keep a Changelog; SemVer. Newest first. From v0.2.0: versioned sub-headings (RULE-DOC-012).

## v0.2.0 — 2026-11-16 — "Rebuilt on Tauri: quarter of size, three macOS defects gone, convert from Finder"

tomd's window, menu bar icon and drop zone were rebuilt as Tauri v2 app with React UI; Python code that finds, installs and drives MarkItDown is unchanged and now runs behind it as background process. download drops from about 100 MB to 12 MB, and three defects reported on macOS 27 (menu bar icon closing app, dead corner where drop zone docks, broken row before first conversion) are gone with Qt layer that caused them. New: convert files from Finder's right-click menu, and choose how drop zone gets out of way during drag. macOS only; Windows stays on 0.1.11.

### v0.2.0 — Added

- Convert to Markdown from Finder. Right-click one or more supported files, Quick Actions, "Convert to Markdown". No window opens: small toast at drop zone's position shows "Converting name" (or "Converting 2 of 5"), then "Done", and disappears. `.md` is written beside file and file also appears in tomd's list, where Copy, Reveal and retry are available. Works when tomd is not running (it starts in menu bar). switch in Settings removes or restores entry. file dropped on tomd's Dock icon converts same way.
- "When drag starts" setting for drop zone: Show drop zone (as before, default), Shake to hide (shake pointer and it hides for that drag), Start small (small pill that grows when file comes near), Hold Option to hide.
- drop zone has button that opens main window, and Run button when files are waiting.

### v0.2.0 — Changed

- app is Tauri v2 shell with React + TypeScript + Tailwind UI. Download 12 MB, installed 24 MB (0.1.11: about 100 MB).
- drop zone appears moment file drag starts anywhere on screen and leaves when file is dropped elsewhere. It used to appear only when drag reached its corner.
- "Start at login" is handled by system login-item plugin; login item set by 0.1.x is taken over on first launch.
- Settings open inside main window instead of separate window.
- Preferences are stored in new place. Settings chosen in 0.1.x (drop zone position, auto-convert, menu bar only, YouTube folder) are not carried over and need setting once.
- macOS only for now. Windows build remains 0.1.11; website sends Windows visitors to that release.

### v0.2.0 — Fixed

- Clicking menu bar icon closed app (macOS 27). Everyone on macOS 27 was affected. Cause: Qt's macOS plugin read `clickCount` from event that is not mouse event when status-item menu opened, and AppKit aborted process (crash reports of 2026-11-15; NOTES N-001). Not caught because nothing tested tray and fault is inside Qt, on macOS version newer than last release. Fix: menu is native Tauri tray menu; no UI toolkit handles its events. Regression coverage: none automated (menu bar click cannot be scripted here); confirmed by hand by owner.
- screen corner where drop zone docks could not be clicked, in any app, while drop zone feature was on. Cause: invisible always-on-top window sat there permanently to notice approaching drag, and window that can receive drag also takes clicks (NOTES N-002); 0.1.7 fix changed only Qt's own event handling. Fix: nothing is on screen while idle; watcher polls mouse button and system drag pasteboard and shows drop zone only while files are being dragged. Regression coverage: none automated; confirmed by hand by owner.
- dropped file showed row with no name and stray box until Run was pressed (auto-convert off). Cause, inferred from code: name label was sized before layout had width (NOTES N-003). Fix: row is plain flex layout in new UI. Regression coverage: none; pending state has not yet been confirmed by hand.

### v0.2.0 — Removed

- PySide6 application: `app.py`, `native.py`, `dev.py`, and `pyside6`, `pyobjc-framework-Cocoa` and `watchfiles` dependencies.
- Windows job in release workflow.
- hot-corner that summoned drop zone (replaced by drag watcher).

### v0.2.0 — How it works

- Three parts. shell (`src-tauri/`, Rust) owns windows, menu bar icon, settings, drag watcher and Finder entry. UI (`src/`, React) runs in shell's webviews. sidecar (`sidecar.py` over `backend.py` and `links.py`) does everything that touches MarkItDown; shell starts it and passes JSON lines both ways (`sidecar.rs`, `src/ipc.ts`). release build carries PyInstaller-frozen sidecar in its resources; debug build runs `sidecar.py` from project's `.venv`.
- One queue. `src/queue.ts` is pure reducer living in main window; `src/useQueue.ts` converts one row at time. drop zone and toast are separate windows that hold no queue: they send events to main window and draw state it broadcasts.
- Drag watcher (`drag_watch.rs`): every 120 ms, if left button is down and drag pasteboard's change count is new and carries files, drop zone is shown without activating tomd; while drag is on it polls at 30 ms to apply chosen drag mode; button up hides zone unless drop pinned it.
- Finder entry (`quick_action.rs`): generated Automator service bundle in `~/Library/Services` whose shell line is `open -g -"<tomd.app>" "$@" --args --background`. macOS delivers files as open-document event (`RunEvent::Opened`), also to tomd that is already running; `--background` stops fresh launch from showing its window. Rows added this way are flagged `background`, converted at once, and reported by toast.

### v0.2.0 — Notes

- unsigned app cannot add top-level item to Finder's right-click menu; that needs signed Finder extension. Signing, notarisation and that item are deferred.
- `.ipynb` and `.msg` files have no system file type, so Finder entry is not offered for them; drag and drop still converts them. entry is offered for every image and audio type.
- app that quits other apps with no open window (found on owner's Mac: Vorssaint) will quit tomd that was started in background by Finder entry, after it has converted. Excluding tomd there keeps it in menu bar.
- build is for architecture of machine that builds it (Apple Silicon on owner's Mac and on GitHub's `macos-latest`).

### v0.2.0 — Files changed

- Added: `src-tauri/` (`src/{lib,settings,sidecar,tray,windows,drag_watch,shake,quick_action,main}.rs`, `quick-action/`, `capabilities/`, `icons/`, `Cargo.toml`, `tauri.conf.json`), `src/` (`{MainWindow,DropZone,Toast,FileRow,SetupPage,SettingsPage,YouTubeDialog,LogBox,ui,main}.tsx`, `{queue,queue.test,useQueue,environment,ipc,settings,dragIcon}.ts`, `app.css`), `sidecar.py`, `links.py`, `tests/`, `package.json`, `bun.lock`, `index.html`, `vite.config.ts`, `tsconfig*.json`.
- Changed: `scripts/build_macos.sh`, `.github/workflows/release.yml`, `docs/index.html`, `README.md`, `CONTRIBUTING.md`, `pyproject.toml`, `uv.lock`, `.gitignore`.
- Removed: `app.py`, `native.py`, `dev.py`.

### v0.2.0 — Verification

- Automated, all passing on 2026-11-15: `uv run pytest` (25), `bun run test` (10), `bun run typecheck`, `cargo clippy`, `cargo test` (8), `bash scripts/build_macos.sh` (exit 0; app 24 MB, DMG 12 MB).
- Release app, by agent: starts its frozen sidecar; two files sent with `open -g -a` converted, with tomd running and with tomd quit; toast window captured showing "2 converted" and gone afterwards; main window captured showing both rows done.
- By owner, by hand: menu bar menu without crash; corner clickable; file drag summons drop zone; drop, Copy, drag out, Reveal, open main window; Finder entry converts PDF with toast.
- Not verified: three new drag modes; Finder switch in Settings; failure and setup-needed toasts; pending-row fix; setup page (MarkItDown was installed throughout); Settings switches, Repair and YouTube dialog one by one; installing from DMG; GitHub Actions workflow; Intel Macs.

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
