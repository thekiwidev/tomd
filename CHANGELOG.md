# Changelog

All notable changes to tomd are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/); versions follow [SemVer](https://semver.org/).

## v0.2.0 — 2026-11-16 — "Rebuilt on Tauri: a quarter of the size, three macOS defects gone, convert from Finder"

tomd's window, menu bar icon and drop zone were rebuilt as a Tauri v2 app with a React UI; the Python code that finds, installs and drives MarkItDown is unchanged and now runs behind it as a background process. The download drops from about 100 MB to 12 MB, and the three defects reported on macOS 27 (the menu bar icon closing the app, a dead corner where the drop zone docks, a broken row before the first conversion) are gone with the Qt layer that caused them. New: convert files from Finder's right-click menu, and choose how the drop zone gets out of the way during a drag. macOS only; Windows stays on 0.1.11.

### v0.2.0 — Added

- **Convert to Markdown from Finder.** Right-click one or more supported files, Quick Actions, "Convert to Markdown". No window opens: a small toast at the drop zone's position shows "Converting name" (or "Converting 2 of 5"), then "Done", and disappears. The `.md` is written beside the file and the file also appears in tomd's list, where Copy, Reveal and retry are available. Works when tomd is not running (it starts in the menu bar). A switch in Settings removes or restores the entry. A file dropped on tomd's Dock icon converts the same way.
- **"When a drag starts" setting** for the drop zone: Show the drop zone (as before, the default), Shake to hide (shake the pointer and it hides for that drag), Start small (a small pill that grows when the file comes near), Hold Option to hide.
- The drop zone has a button that opens the main window, and a Run button when files are waiting.

### v0.2.0 — Changed

- The app is a Tauri v2 shell with a React + TypeScript + Tailwind UI. Download 12 MB, installed 24 MB (0.1.11: about 100 MB).
- The drop zone appears the moment a file drag starts anywhere on screen and leaves when the file is dropped elsewhere. It used to appear only when the drag reached its corner.
- "Start at login" is handled by the system login-item plugin; a login item set by 0.1.x is taken over on first launch.
- Settings open inside the main window instead of a separate window.
- Preferences are stored in a new place. Settings chosen in 0.1.x (drop zone position, auto-convert, menu bar only, YouTube folder) are not carried over and need setting once.
- macOS only for now. The Windows build remains 0.1.11; the website sends Windows visitors to that release.

### v0.2.0 — Fixed

- **Clicking the menu bar icon closed the app** (macOS 27). Everyone on macOS 27 was affected. Cause: Qt's macOS plugin read `clickCount` from an event that is not a mouse event when the status-item menu opened, and AppKit aborted the process (crash reports of 2026-11-15; NOTES N-001). Not caught because nothing tested the tray and the fault is inside Qt, on a macOS version newer than the last release. Fix: the menu is a native Tauri tray menu; no UI toolkit handles its events. Regression coverage: none automated (a menu bar click cannot be scripted here); confirmed by hand by the owner.
- **The screen corner where the drop zone docks could not be clicked**, in any app, while the drop zone feature was on. Cause: an invisible always-on-top window sat there permanently to notice an approaching drag, and a window that can receive a drag also takes clicks (NOTES N-002); the 0.1.7 fix changed only Qt's own event handling. Fix: nothing is on screen while idle; a watcher polls the mouse button and the system drag pasteboard and shows the drop zone only while files are being dragged. Regression coverage: none automated; confirmed by hand by the owner.
- **A dropped file showed a row with no name and a stray box until Run was pressed** (auto-convert off). Cause, inferred from the code: the name label was sized before the layout had a width (NOTES N-003). Fix: the row is plain flex layout in the new UI. Regression coverage: none; the pending state has not yet been confirmed by hand.

### v0.2.0 — Removed

- The PySide6 application: `app.py`, `native.py`, `dev.py`, and the `pyside6`, `pyobjc-framework-Cocoa` and `watchfiles` dependencies.
- The Windows job in the release workflow.
- The hot-corner that summoned the drop zone (replaced by the drag watcher).

### v0.2.0 — How it works

- **Three parts.** The shell (`src-tauri/`, Rust) owns windows, the menu bar icon, settings, the drag watcher and the Finder entry. The UI (`src/`, React) runs in the shell's webviews. The sidecar (`sidecar.py` over `backend.py` and `links.py`) does everything that touches MarkItDown; the shell starts it and passes JSON lines both ways (`sidecar.rs`, `src/ipc.ts`). A release build carries a PyInstaller-frozen sidecar in its resources; a debug build runs `sidecar.py` from the project's `.venv`.
- **One queue.** `src/queue.ts` is a pure reducer living in the main window; `src/useQueue.ts` converts one row at a time. The drop zone and the toast are separate windows that hold no queue: they send events to the main window and draw the state it broadcasts.
- **Drag watcher** (`drag_watch.rs`): every 120 ms, if the left button is down and the drag pasteboard's change count is new and carries files, the drop zone is shown without activating tomd; while a drag is on it polls at 30 ms to apply the chosen drag mode; button up hides the zone unless a drop pinned it.
- **Finder entry** (`quick_action.rs`): a generated Automator service bundle in `~/Library/Services` whose shell line is `open -g -a "<tomd.app>" "$@" --args --background`. macOS delivers the files as an open-document event (`RunEvent::Opened`), also to a tomd that is already running; `--background` stops a fresh launch from showing its window. Rows added this way are flagged `background`, converted at once, and reported by the toast.

### v0.2.0 — Notes

- An unsigned app cannot add a top-level item to Finder's right-click menu; that needs a signed Finder extension. Signing, notarisation and that item are deferred.
- `.ipynb` and `.msg` files have no system file type, so the Finder entry is not offered for them; drag and drop still converts them. The entry is offered for every image and audio type.
- An app that quits other apps with no open window (found on the owner's Mac: Vorssaint) will quit a tomd that was started in the background by the Finder entry, after it has converted. Excluding tomd there keeps it in the menu bar.
- The build is for the architecture of the machine that builds it (Apple Silicon on the owner's Mac and on GitHub's `macos-latest`).

### v0.2.0 — Files changed

- Added: `src-tauri/` (`src/{lib,settings,sidecar,tray,windows,drag_watch,shake,quick_action,main}.rs`, `quick-action/`, `capabilities/`, `icons/`, `Cargo.toml`, `tauri.conf.json`), `src/` (`{MainWindow,DropZone,Toast,FileRow,SetupPage,SettingsPage,YouTubeDialog,LogBox,ui,main}.tsx`, `{queue,queue.test,useQueue,environment,ipc,settings,dragIcon}.ts`, `app.css`), `sidecar.py`, `links.py`, `tests/`, `package.json`, `bun.lock`, `index.html`, `vite.config.ts`, `tsconfig*.json`.
- Changed: `scripts/build_macos.sh`, `.github/workflows/release.yml`, `docs/index.html`, `README.md`, `CONTRIBUTING.md`, `pyproject.toml`, `uv.lock`, `.gitignore`.
- Removed: `app.py`, `native.py`, `dev.py`.

### v0.2.0 — Verification

- Automated, all passing on 2026-11-15: `uv run pytest` (25), `bun run test` (10), `bun run typecheck`, `cargo clippy`, `cargo test` (8), `bash scripts/build_macos.sh` (exit 0; app 24 MB, DMG 12 MB).
- Release app, by an agent: starts its frozen sidecar; two files sent with `open -g -a` converted, with tomd running and with tomd quit; the toast window captured showing "2 converted" and gone afterwards; main window captured showing both rows done.
- By the owner, by hand: menu bar menu without a crash; corner clickable; a file drag summons the drop zone; drop, Copy, drag out, Reveal, open main window; the Finder entry converts a PDF with the toast.
- Not verified: the three new drag modes; the Finder switch in Settings; the failure and setup-needed toasts; the pending-row fix; the setup page (MarkItDown was installed throughout); Settings switches, Repair and the YouTube dialog one by one; installing from the DMG; the GitHub Actions workflow; Intel Macs.

## [0.1.11] — 2026-08-06

### Changed
- **Share links are converted, not refused.** YouTube's own Share button gives you `youtu.be/_0A2BnRYVCo` while the address bar gives `youtube.com/watch?v=_0A2BnRYVCo` — the same video written two ways. Both are now accepted and rewritten to the form MarkItDown understands, so it no longer matters which one you paste.
- **Link validation says what's actually wrong.** Instead of one catch-all "that doesn't look like a YouTube link", each case names itself: Shorts and live streams aren't supported yet, playlists and channels aren't single videos, a mistyped id is reported as a bad id, and a link missing its `https://` says so. Every message ends with where to get a working link.
- Shorts, live, embed and playlist links are now rejected outright. They were previously accepted and passed to MarkItDown, which doesn't recognise them — the conversion appeared to succeed and produced a page of YouTube's footer links.
- The link field carries a standing note of what it accepts, so the rules are visible before you paste rather than after.

## [0.1.10] — 2026-08-06

### Fixed
- **A failed YouTube transcript no longer looks like a successful conversion.** MarkItDown exits 0 even when it can't fetch a transcript: its YouTube converter gives up, the generic HTML converter picks the page up instead, and the `.md` you get is YouTube's footer — About, Press, Copyright, © Google — reported as a finished job. tomd now checks that a transcript actually came back, deletes the bogus file, and says what went wrong instead of leaving page furniture on disk under the video's name.
- **YouTube links are normalised before conversion.** MarkItDown's YouTube converter only recognises URLs beginning exactly `https://www.youtube.com/watch?`, and reads the video id from the `v` parameter. A `youtu.be`, `/shorts/`, `/live/` or bare `youtube.com` link satisfied neither and fell through to the generic HTML converter without a word. Every accepted link shape is now rewritten to the canonical form.
- A 429 from somewhere other than YouTube no longer blames YouTube in the error message.

## [0.1.9] — 2026-08-06

### Fixed
- Conversion failures now explain themselves. A YouTube fetch that YouTube refuses used to surface as `HTTPError: 429 Client Error: Too Many Requests for url: https://www.google.com/sorry/index?continue=…` — two hundred characters of Google challenge URL, truncated to fit a one-line row, saying nothing a person could act on. It now reads "YouTube is refusing requests from this network — it returns a bot check instead of the video page. Turn off any VPN, or try another network."
- The same treatment for the other failures worth naming: captions turned off, no transcript in a supported language, video unavailable, age-restricted, and missing MarkItDown dependencies (which now points at Settings → Repair). Anything unrecognised still shows the underlying exception.

### Known issues
- YouTube blocks transcript fetches at the IP level from some networks — VPNs, shared/CGNAT addresses, and datacenter ranges especially. When that happens every video fails identically regardless of the app, because YouTube serves a bot check instead of the page. The block is usually temporary; a different network (a phone hotspot) is the reliable workaround.
- MarkItDown sends no `User-Agent` when fetching URLs, so sites with a user-agent policy — Wikipedia among them — reject it with HTTP 403. This is upstream behaviour and does not affect local files or YouTube links, the only sources tomd currently accepts.

## [0.1.8] — 2026-08-06

### Added
- **Repair MarkItDown**, in Settings. Shows what the conversion engine actually is — version, which file formats are available, which Python — and rebuilds it on one click: tomd's private environment is deleted, MarkItDown's build caches are cleared, and everything is installed again from scratch, fetching a compatible Python first if the device hasn't got one. MarkItDown installs belonging to other Pythons on the machine are detected and listed; removing those is an opt-in checkbox, since tomd didn't create them.
- The first-run setup screen offers the same repair when MarkItDown is present but can't convert anything. Previously its Install button greyed out in exactly that situation, leaving the page a dead end.
- **YouTube transcripts.** A YouTube button in the toolbar, and "Add YouTube video…" in the menu bar. Paste a link and give it a title; the transcript is saved as `<title-slug>.md` — lowercase and hyphenated — into a folder you choose once and tomd remembers. The file name is previewed live as you type, and the title is optional (the video id is used instead).

### Fixed
- **A MarkItDown install is now verified, not just detected.** tomd used to accept any `markitdown` file that existed. When pip couldn't resolve `markitdown[all]` it would quietly backtrack to 0.0.2 — a release predating the `[all]` extra entirely — and report success, leaving a CLI that converted CSV and text happily and failed every PDF, Word, PowerPoint and Excel file. Installs are now checked for version *and* for each format's dependencies before being accepted.
- Installs request `markitdown[all]>=0.1.0` and try the device's Pythons newest-first, stepping down only when one genuinely cannot produce a working CLI. This is a floor, not a pin — the newest Python and the newest MarkItDown are still preferred, and are used the moment they work.
- A `markitdown` on PATH no longer wins automatically; it has to pass the same health check. A partially-installed system copy could previously shadow the working one tomd manages, which looked exactly like tomd being broken.
- The `uv` bootstrap no longer dies with a TLS certificate error on python.org's macOS Framework builds, which ship no CA store until `Install Certificates.command` is run. It now falls back to curl and the system trust store.
- Conversion failures show the real error — `HTTPError: 429 Client Error: Too Many Requests` — instead of whatever slice of a Python traceback happened to fall in the last 500 characters.
- Startup no longer waits on the MarkItDown health check; it runs in the background and the window appears immediately.

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

[0.1.11]: https://github.com/thekiwidev/tomd/releases/tag/v0.1.11
[0.1.10]: https://github.com/thekiwidev/tomd/releases/tag/v0.1.10
[0.1.9]: https://github.com/thekiwidev/tomd/releases/tag/v0.1.9
[0.1.8]: https://github.com/thekiwidev/tomd/releases/tag/v0.1.8
[0.1.7]: https://github.com/thekiwidev/tomd/releases/tag/v0.1.7
[0.1.6]: https://github.com/thekiwidev/tomd/releases/tag/v0.1.6
[0.1.5]: https://github.com/thekiwidev/tomd/releases/tag/v0.1.5
[0.1.4]: https://github.com/thekiwidev/tomd/releases/tag/v0.1.4
[0.1.3]: https://github.com/thekiwidev/tomd/releases/tag/v0.1.3
[0.1.2]: https://github.com/thekiwidev/tomd/releases/tag/v0.1.2
[0.1.1]: https://github.com/thekiwidev/tomd/releases/tag/v0.1.1
[0.1.0]: https://github.com/thekiwidev/tomd/releases/tag/v0.1.0
