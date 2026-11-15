---
doc: LOG
purpose: "Append-only record of every prompt and session: what was asked, what was tried, what happened — the memory of attempts"
authority: reference
hosts_rules: [RULE-DOC-015]
mirrors_rules: [RULE-DOC-014]
last_reviewed: "2026-11-15"
---

# LOG — tomd

> Append-only (RULE-DOC-015). Every new prompt and every new session adds a new entry at the **top**, directly under this header (newest first, RULE-DOC-016); nothing already written is edited, reordered, merged, summarised or deleted unless the owner instructs it. A logged entry is context for the next agent, never a draft to improve. If an entry turns out to be wrong, add a new entry that says `Corrects L-###`. A retry, a second attempt or a "something is wrong" follow-up is a new entry that points at the earlier one (`Follows: L-###`), so the history reads: first attempt, what failed, second attempt, and so on.
>
> Read the top entries at session start and search this file for the topic of the task (`L-###` titles, file names) before starting work; before repeating an approach that is logged as failed, say what is different this time. Headings are unique (`L-###`); fields are bold labels, not sub-headings (RULE-DOC-012 spirit, MD024).

## L-017 — 2026-11-15 — Tauri rewrite T5 and Finder convert F7: closing documentation (attempt 1)

**Task:** docs-only · **Attempt:** 1 of tauri-rewrite T5 / finder-convert F7 · **Follows:** L-016 · **Outcome:** worked · **Related:** CHANGELOG v0.2.0, plans `tauri-rewrite`, `finder-convert`
**Prompt:** "Yes, do T5".
**What was tried:** Wrote CHANGELOG `v0.2.0 — unreleased` in the RULE-DOC-012 shape (older entries left in their Keep a Changelog shape). Rewrote MEMORY (current state of 0.2.0), ARCHITECTURE (whole document, now the Tauri app), ENGINEERING §§ 1 to 3 (Rust and TypeScript posture, naming, boundaries), VERIFICATION's state paragraph, HANDOFF (one block: remaining hand checks and release). NOTES: N-001 and N-002 resolved with a Resolution section; N-003 annotated and left open. Regenerated `docs/ai/context/{MEMORY,NOTES,CHANGELOG}.md` and stamped them. Moved `plans/active/tauri-rewrite.md` to `plans/completed/`, fixed the links to it (ADR-001, VERIFICATION, plans INDEX). `finder-convert` F7 marked done but the plan stays active.
**Result:** `kiwi ctx status`: all current. `kiwi doctor --project` result is in the session report that follows this entry.
**Why it did or did not work:** n/a.
**Decisions and rejected alternatives:** N-003 was not marked resolved: the pending state of a row has not been seen by the owner or captured. `finder-convert` was not moved to `completed/` for the same reason (drag modes, Finder switch, failure toast unconfirmed). The CHANGELOG date slot says `unreleased` until the owner tags.
**Not checked:** nothing in the app changed in this task.
**State left behind:** all of 0.2.0 uncommitted on `dev`.
**Next:** HANDOFF → Next action.

## L-016 — 2026-11-15 — Tauri rewrite T4: packaging and removal of the PySide6 app (attempt 1)

**Task:** refactor · **Attempt:** 1 of tauri-rewrite T4 · **Follows:** L-015 · **Outcome:** worked, owner hand checks pending · **Related:** plan `tauri-rewrite` T4, plan `finder-convert` F5
**Prompt:** "Start T4".
**What was tried:** Rewrote `scripts/build_macos.sh`: `uv sync`, `bun install --frozen-lockfile`, PyInstaller `--onedir` of `sidecar.py` into `build/sidecar/tomd-sidecar/`, `bun run tauri build --bundles app --config '{...}'` adding that folder as the resource `sidecar` and `signingIdentity: "-"`, then `ditto` to `dist/tomd.app` and `hdiutil` to `dist/tomd.dmg`. `release.yml`: Windows job removed, bun and Rust set up, only `tomd.dmg` attached. `docs/index.html`: Windows visitors get the `v0.1.11` `tomd.exe` link and the label "Windows (0.1.11)". README and CONTRIBUTING rewritten for the Tauri app. Deleted `app.py`, `native.py`, `dev.py`, `tomd.spec`; removed `pyside6`, `pyobjc-framework-Cocoa`, `watchfiles` from `pyproject.toml`; version 0.2.0.
**Result:** Build exit 0. `dist/tomd.app` 24 MB (sidecar 20 MB, shell binary 4 MB), `dist/tomd.dmg` 12 MB; signature ad hoc. Installed to `/Applications`: the process tree is `tomd` and `Contents/Resources/sidecar/tomd-sidecar`; `open -g -a /Applications/tomd.app sample.csv two.csv` wrote both `.md` files and put the toast window on screen; a capture of the main window shows both rows done with "Done: 2 converted". `uv run pytest` 25 passed after the dependency removal. The release build ran `migrate_login_item`: `~/Library/LaunchAgents/me.thekiwidev.tomd.plist` is gone and `tomd.plist` now starts `/Applications/tomd.app/Contents/MacOS/tomd`.
**Why it did or did not work:** The sidecar is added by `--config` in the script, not in `tauri.conf.json`, because Tauri requires resources to exist even for a debug build, which does not use them.
**Decisions and rejected alternatives:** One-folder sidecar, not one-file (a one-file build unpacks itself on every start). The DMG is made with `hdiutil` as before rather than Tauri's DMG bundler, which drives Finder to style the window and is fragile without a GUI session. Ad-hoc signing only; a Developer ID is deferred (LOG L-013).
**Not checked:** the DMG was not mounted and installed from; the GitHub Actions workflow was not run; Intel Macs (the build is for the build machine's architecture, arm64 here); the owner's hand checks on the release app. The owner's saved settings have `menu_bar_only: true`, so the window stays hidden at launch by design.
**State left behind:** `/Applications/tomd.app` is the release build, running. `scripts/build_windows.ps1` (builds the deleted `app.py`) and `assets/make_icon.py` (imports PySide6) are broken and untouched; `docs/index.html` still says "Intel Macs" and "Linux: run from source". `dist/tomd/` and `build/` hold old PyInstaller output. All uncommitted on `dev`.
**Next:** owner checks the release app; then T5 with F7.

## L-015 — 2026-11-15 — Owner confirms the Finder Quick Action (attempt 1)

**Task:** feature · **Attempt:** 1 of finder-convert, owner check · **Follows:** L-014 · **Outcome:** worked (part) · **Related:** plan `finder-convert` F1, F3, F4
**Prompt:** "Yes, works", answering: does right-click, Quick Actions, "Convert to Markdown" convert a PDF with the toast?
**What was tried:** Nothing changed.
**Result:** Owner confirms the entry appears in Finder, converts a PDF and shows the toast.
**Why it did or did not work:** n/a.
**Decisions and rejected alternatives:** none.
**Not checked:** not reported by the owner: several files at once, absence on a folder, the three drag modes, the Finder switch in Settings, the failure toast, clicking the toast.
**State left behind:** as L-014; uncommitted on `dev`.
**Next:** remaining owner checks, or T4 (packaging) on the owner's word.

## L-014 — 2026-11-15 — Finder convert F2 to F6 implemented; background launch was being quit by another app (attempt 1)

**Task:** feature · **Attempt:** 1 of finder-convert F2 to F6 · **Follows:** L-013 · **Outcome:** awaiting owner test · **Related:** plan `finder-convert`, PRD `prd-finder-convert`
**Prompt:** "Do everything that can be done without signing; only the things that require signing will be done later."
**What was tried:** F2: `src/queue.ts` gained `Row.background`, an `add` option `background` (converts at once and re-runs a listed row that is not converting), the action `seen`, and `toastOf(queue)`; three tests added first. F3: `lib.rs` handles `RunEvent::Opened` (paths pushed to the state `Opened`, event `sources-opened`), the command `take_opened`, and `--background` skips `show_main`; `MainWindow.tsx` takes the paths on mount and on the event. F4: third window `toast` (260 x 48) in `tauri.conf.json` and the capability; `windows.rs` `set_toast` / `get_toast` (the text is held in `Shell.toast` so the window can ask for it when it loads), placed by `anchor_position`, hidden while the drop zone is visible; `src/Toast.tsx`; timing in `MainWindow.tsx` (2 s after success, 4 s after a failure, then `seen`). F5: `src-tauri/src/quick_action.rs` writes the bundle from the templates `src-tauri/quick-action/{Info.plist,document.wflow}` (the F1 bundle with a command placeholder), only when running from an `.app` outside any `target/` folder; new setting `finder_action` (default on) drives install and removal through `settings::apply`; Settings switch. F6: setting `drag_mode` (`show`, `shake`, `small`, `option`); `src-tauri/src/shake.rs` (3 reversals of at least 60 physical px within 700 ms); `drag_watch.rs` rewritten around a `Drag` value that polls at 30 ms during a drag: Option hides while held, a shake hides until the drag ends, small resizes the window to a 132 x 40 pill and grows it while the pointer is within 360 physical px; `DropZone.tsx` shows the pill layout by a CSS `max-height` query; Settings select.
**Result:** `uv run pytest` 25 passed; `bun run test` 10 passed; `bun run typecheck` and `cargo clippy` clean; `cargo test` 8 passed; debug bundle 26.97 MiB, installed to `/Applications/tomd.app`. With tomd running, `open -g -a /Applications/tomd.app sample.csv two.csv` wrote both `.md` files with no window raised; a capture of the toast window shows a green check and "2 converted"; the toast was off screen 6 s later. With tomd quit, the same command plus `--args --background` started it with the main window off screen, the toast on screen for about 2 s, and both files converted. The installed bundle's command is `open -g -a "/Applications/tomd.app" "$@" --args --background` and passes `plutil -lint`.
**Why it did or did not work:** Three problems on the way. (1) Crash on a fresh launch with files: macOS delivers the open-document event before `setup`, the handler asked for `Shell`, which did not exist yet, and the panic aborted inside the Apple Event handler (`tomd-2026-11-15-2235*.ips`, `objc_exception_rethrow` under `dispatchRawAppleEvent`). Fixed by a separate `Opened` state managed on the builder. (2) After those crashes macOS showed "tomd unexpectedly quit while reopening windows" at every launch, which blocks a background start; tomd now sets `ApplePersistenceIgnoreState` at start (`ignore_saved_window_state`). (3) A background-launched tomd exited with code 0 a few seconds after converting. `lldb` on `-[NSApplication _handleAEQuit]` showed a Quit Apple Event whose sender pid was 914, `/Applications/Vorssaint.app`: another app on the owner's Mac quits tomd when it has no window. Not a tomd defect; conversion and the toast had already finished each time.
**Decisions and rejected alternatives:** Rejected ignoring Quit Apple Events in tomd: the Dock's Quit and logout use the same event. Disabling AppKit automatic and sudden termination was tried as a hypothesis for (3), made no difference, and was removed. The Finder entry is a setting rather than an install button, so removing it is remembered. A zone opened on purpose (pinned) ignores the drag modes.
**Not checked:** by hand, all the owner's: the Finder right-click entry (F1 still unanswered), each of the three drag modes, the new Settings controls, the failure toast, the setup-needed toast, clicking the toast. Shake thresholds are untuned.
**State left behind:** `/Applications/tomd.app` is the new debug build, running. The real Quick Action replaced the F1 probe. Everything uncommitted on `dev`.
**Next:** owner's checks; then F7 with T4 and T5.

## L-013 — 2026-11-15 — Owner asks about signing for a top-level Finder item, and what comes next (attempt 1)

**Task:** question · **Attempt:** 1 · **Follows:** L-012 · **Outcome:** blocked on owner decision · **Related:** PRD `prd-finder-convert` § 5, plan `finder-convert`, MEMORY → Deferred Work
**Prompt:** "I think I would prefer to sign the app, so it appears on the right-click context menu of any supported file. What is the next step? Is it releases?"
**What was tried:** Nothing run. Answered from knowledge of macOS, not verified on this machine.
**Result:** Told the owner: a top-level item needs a Finder Sync extension (a sandboxed app extension built as its own Swift target, embedded in `tomd.app`, enabled by the user in System Settings), which Tauri does not build, plus a Developer ID certificate (Apple Developer Program, a yearly fee: the owner's spending decision) and notarisation. Recommended order: finish F1 to F6 with the Quick Action, package and release 0.2.0 (T4, T5), then signing and the extension as a later release. Release is not the next step: the F1 right-click check, F2 to F6, T4 and T5 come first.
**Why it did or did not work:** n/a.
**Decisions and rejected alternatives:** none taken; the PRD's non-goal (no top-level item while unsigned) stands until the owner decides.
**Not checked:** whether Finder Sync extensions behave on macOS 27 as on earlier versions, and whether an ad-hoc signed extension loads locally; both would need a prototype.
**State left behind:** unchanged since L-012. The F1 right-click check is still unanswered.
**Next:** owner chooses: signing later (continue F2) or signing first (amend the PRD and plan, enrol in the Apple Developer Program).

## L-012 — 2026-11-15 — Finder convert F1: probe Quick Action installed (attempt 1)

**Task:** feature · **Attempt:** 1 of finder-convert F1 · **Follows:** L-011 · **Outcome:** awaiting owner test · **Related:** plan `finder-convert` F1
**Prompt:** "Approve, start F1" (plan approved with the recommended picks: ship in 0.2.0; a file dropped on the Dock icon converts in the background).
**What was tried:** Found a working reference on this machine: `~/Library/Services/Claude - codeHere.workflow`, a Finder-only, file-input, Run Shell Script Quick Action installed by another app without Automator. Wrote `~/Library/Services/Convert to Markdown.workflow` with Python `plistlib`: `Contents/Info.plist` (`NSServices`: `NSMessage` `runWorkflowAsService`, `NSRequiredContext` Finder, `NSSendFileTypes` 18 type identifiers) and `Contents/document.wflow` (the reference's action with `COMMAND_STRING` replaced by a probe that appends the date and its arguments to `/private/tmp/claude-501/-Users-thekiwidev-work-me-tomd/01d05e82-293c-4e00-aa31-aae4419b23f2/scratchpad/quick-action.log`, `inputMethod` 1 = as arguments, input type `com.apple.Automator.fileSystemObject`). Ran `/System/Library/CoreServices/pbs -update`.
**Result:** Both plists pass `plutil -lint`. `pbs -dump_pboard` lists the service with its bundle path and file types. `automator -i sample.csv "<bundle>"` ran the script: the log holds the date and the file's path. Type identifiers were resolved with `UTType(filenameExtension:)` for all 26 extensions in `links.SUPPORTED_EXTENSIONS`.
**Why it did or did not work:** The bundle format does not need Automator to have saved it; the services registry picked it up.
**Decisions and rejected alternatives:** `public.image` and `public.audio` are listed instead of each image and audio type, so the entry also shows on formats outside tomd's list (for example HEIC); tomd's own filter handles those. `.ipynb` and `.msg` have no declared system type on this Mac (dynamic `dyn.` identifiers), so the entry cannot be offered for them without offering it for every file (`public.data`); they stay convertible by drag and drop. Reported to the owner.
**Not checked:** the entry in Finder's right-click menu (an agent cannot right-click): that it appears on a PDF, not on a folder, and that a multiple selection arrives as several arguments.
**State left behind:** the probe bundle is installed and only writes a log line; F5 replaces its command. No repository code changed.
**Next:** owner right-clicks a PDF, Quick Actions, "Convert to Markdown" (and a multi-selection, and a folder); then F2.

## L-011 — 2026-11-15 — PRD approved; plan for Finder convert written (attempt 1)

**Task:** feature (plan) · **Attempt:** 1 of finder-convert · **Follows:** L-010 · **Outcome:** awaiting owner approval · **Related:** `docs/ai/plans/active/finder-convert.md`, PRD `prd-finder-convert`
**Prompt:** "Approve as written" (the PRD, with the assumed answers to its open questions).
**What was tried:** Marked the PRD approved. `kiwi new plan finder-convert`, then wrote the plan: seven tasks F1 to F7. Checked that Tauri 2.12 exposes `RunEvent::Opened { urls }`.
**Result:** Plan written and registered in `plans/INDEX.md`. No code.
**Why it did or did not work:** n/a.
**Decisions and rejected alternatives:** Files reach tomd through `open -g -a tomd "$@" --args --background` and the file-open event; rejected a `tomd://` scheme (extra plugin, URL-encoding in shell) and binary arguments (ignored when already running). The toast is a third window, not a mode of the drop zone window, so the two never fight over one window's size. Drag modes live in `drag_watch.rs`; "Start small" switches layout by CSS height, not an event. F1 proves the hand-written workflow bundle first because nothing else is worth building if Finder does not list it.
**Not checked:** nothing prototyped: whether a generated `.workflow` registers without Automator, and the UTI list, are unverified (plan risk 1).
**State left behind:** PRD approved; plan pending approval with two owner decisions (release 0.2.0 or 0.2.1; Dock-icon drop converts in the background).
**Next:** owner approves the plan and answers the two decisions; then F1.

## L-010 — 2026-11-15 — PRD for Finder convert and drop zone dismissal (attempt 1)

**Task:** feature (product definition) · **Attempt:** 1 of finder-convert · **Follows:** L-009 · **Outcome:** awaiting owner approval · **Related:** `docs/ai/prd/prd-finder-convert.md`
**Prompt:** Owner's answers: "1A, 2B, 3A, 4B, 5A, 6 I actually like all provided options, so I would like if user can select which one works for them in the settings."
**What was tried:** Wrote the PRD: Quick Action entry (1A), brief "Failed" toast with detail in the main window (2B), same queue as the main window (3A), files only (4B), starts in the menu bar when not running (5A), and a "When a drag starts" setting offering shake, start small, hold Option, or today's behaviour (6).
**Result:** `docs/ai/prd/prd-finder-convert.md`, indexed in `INDEX.md`, noted in MEMORY and HANDOFF.
**Why it did or did not work:** n/a.
**Decisions and rejected alternatives:** Assumptions put to the owner in L-009 and not contradicted are written as requirements: "Converting 2 of 5" for several files, an existing `.md` is replaced, clicking the toast opens the main window. One dismissal method active at a time (a single choice, as the owner asked), not a combination.
**Not checked:** technical feasibility of each route was not prototyped; the PRD's Technical Considerations are constraints, not a design.
**State left behind:** PRD is a draft. Three open questions in its § 9: default dismissal mode, automatic install of the Finder entry, and 0.2.0 versus 0.2.1.
**Next:** owner approves or amends the PRD and answers § 9; then the plan (`kiwi-author`), then the owner's plan approval.

## L-009 — 2026-11-15 — Owner test of the installed build; two new requests (attempt 1)

**Task:** feature (product definition) · **Attempt:** 1 of finder-convert · **Follows:** L-008 · **Outcome:** blocked on owner answers · **Related:** L-005, L-006, plan `tauri-rewrite` T2 / T3
**Prompt:** Owner tested `/Applications/tomd.app` and asked for two things: (1) a right-click "Convert to Markdown" entry in Finder for supported files that converts in the background with no window, shows a toast where the drop zone opens (running, then done, then gone) and writes the `.md` beside the file; (2) a way to get the drop zone out of the way mid-drag when the place the file should go is underneath it, for example by shaking.
**Owner feedback on the previous attempt:** The drop zone leaves no dead area; it appears as soon as a file is dragged (the L-005 polling watcher works); a dropped file converts; Copy, drag out, Reveal in Finder and opening the main window from the zone all work. "Everything else checks out." Not named one by one: main-window drop / Run / Stop / multi-select, Settings, Repair, the YouTube dialog, the setup page.
**What was tried:** Nothing implemented. A new capability goes through a PRD first (AGENT-CORE § 6, `create-prd`): clarifying questions put to the owner.
**Result:** Questions asked; no PRD yet.
**Why it did or did not work:** n/a.
**Decisions and rejected alternatives:** none yet. Constraint put to the owner: an unsigned app cannot add a top-level Finder context-menu item (that needs a signed Finder Sync extension; signing is deferred work); a Quick Action / Services entry is what is possible now.
**Not checked:** n/a.
**State left behind:** code unchanged since L-006.
**Next:** owner answers; write `docs/ai/prd/prd-finder-convert.md`; owner approves; plan.

## L-008 — 2026-11-15 — Remove the login item that started the build-folder copy (attempt 1)

**Task:** maintenance · **Attempt:** 1 · **Follows:** L-007 · **Outcome:** worked · **Related:** L-004, L-007
**Prompt:** "Yes, remove it" (the second login item reported in L-007).
**What was tried:** `launchctl bootout` of `~/Library/LaunchAgents/tomd.plist`, then deleted the file.
**Result:** Only `me.thekiwidev.tomd.plist` remains; it starts `/Applications/tomd.app`. The running app was not affected.
**Why it did or did not work:** n/a.
**Decisions and rejected alternatives:** none.
**Not checked:** an actual login. "Start at login" in the installed app (a debug build) would register `/Applications/tomd.app` under the plugin's own `tomd.plist` again, alongside the 0.1.x-format plist; the release build migrates the old plist (`migrate_login_item`), the debug build does not.
**State left behind:** one login item.
**Next:** owner's hand checks.

## L-007 — 2026-11-15 — Install the new build in /Applications for the owner's tests (attempt 1)

**Task:** maintenance · **Attempt:** 1 · **Follows:** L-006 · **Outcome:** worked · **Related:** plan `tauri-rewrite` T3
**Prompt:** Owner removed the 0.1.11 app and wants the new one installed, so a test is certain to be of the new app.
**What was tried:** Confirmed `/Applications/tomd.app` was absent and no tomd process ran. Copied the debug bundle with `ditto src-tauri/target/debug/bundle/macos/tomd.app /Applications/tomd.app` and opened it.
**Result:** Running process is `/Applications/tomd.app/Contents/MacOS/tomd`, bundle id `dev.thekiwidev.tomd`, version 0.2.0, with `sidecar.py` as its child.
**Why it did or did not work:** A debug build has the repository path compiled in and runs `sidecar.py` from the repository's `.venv`, so this copy works only on this machine while the repository stays where it is. It is not the release app (T4).
**Decisions and rejected alternatives:** none.
**Not checked:** the owner's hand checks (HANDOFF). Two login items exist in `~/Library/LaunchAgents`: `me.thekiwidev.tomd.plist` (starts `/Applications/tomd.app`, recreated in L-004) and `tomd.plist` (starts the `target/debug` bundle; inferred to come from the "Start at login" switch in a debug build). Both left in place; with both, two copies start at login. Reported to the owner.
**State left behind:** `/Applications/tomd.app` is a copy of the debug build and goes stale on every rebuild; reinstall with the same `ditto` command.
**Next:** owner's hand checks; owner decides on the two login items.

## L-006 — 2026-11-15 — Tauri rewrite T3: the React UI (attempt 1)

**Task:** refactor · **Attempt:** 1 of tauri-rewrite T3 · **Follows:** L-005 · **Outcome:** awaiting owner test · **Related:** plan `tauri-rewrite` T3, N-003
**Prompt:** "Space freed", then "Continue" (the disk-full stop of L-005).
**What was tried:** Rust: registered the `dialog`, `opener`, `clipboard-manager` and `drag` plugins in `lib.rs`; added the commands `copy_markdown` (reads a `.md` file and puts it on the clipboard; refuses any other extension so the webview gains no general file read) and `windows::show_main_window`; capability gained `dialog:allow-open`, `opener:allow-reveal-item-in-dir`, `drag:default`. `Cargo.toml` sets `[profile.dev] debug = 0` because debug info made `target/` several GB and filled the disk (L-005). Sidecar: `convert_file`'s `output` is optional, default the source path with `.md` (one test added). UI: `src/queue.ts` is the queue as a pure reducer (add, enqueue, start, finish, stop, clear, remove, select) with `src/queue.test.ts`; `src/useQueue.ts` runs it (one `convert_file` at a time) and emits `queue-changed`; `src/MainWindow.tsx` (toolbar, list, progress bar, toast, drop anywhere), `FileRow.tsx`, `SetupPage.tsx`, `SettingsPage.tsx`, `YouTubeDialog.tsx`, `DropZone.tsx`, `environment.ts`, `LogBox.tsx`, `ui.tsx`, `dragIcon.ts`, `app.css` (Tailwind v4 theme). `src/ipc.ts` request ids now carry the window label, because both windows hear every sidecar reply. `src/base.css` deleted.
**Result:** `bun run test` 7 passed; `bun run typecheck` clean; `uv run pytest` 25 passed; `cargo clippy` clean; `cargo test` 3 passed; `bun run tauri build --debug --bundles app` built a 26.82 MiB bundle. Launched it; `screencapture -l <window id>` of the main window shows the real UI (toolbar with Add files, YouTube, clear, Run, Settings; empty-state drop hint). `sidecar.py` running as its child. A CSV sent to `sidecar.py` with no `output` wrote `sample.md` beside it.
**Why it did or did not work:** Builds and renders. Nothing was clicked or dropped: no assistive access for agents on this machine.
**Decisions and rejected alternatives:** The main window owns the queue; the drop zone window holds none, sends drops to it (`sources-dropped`, `queue-run`) and renders the mirrored `queue-changed` state. Rejected: a queue per window (two runners, two lists). The row id is the source path or canonical URL, so adding a source twice is a no-op. Stop lets the running file finish and returns waiting rows to pending (as `QueueWorker` did). The setup page shows when the shallow report finds no MarkItDown; an unhealthy one shows a banner that opens Settings instead of blocking. One "Add files" button; folders are added by dropping them (no separate folder picker). The drag-out image is a generated 32 px PNG (`dragIcon.ts`) because the drag plugin requires one.
**Not checked:** every interaction: drop on the main window, Run, Stop, Copy MD, drag out, Reveal, multi-select, Settings toggles, Repair, the setup page (MarkItDown is installed here, so it never showed), the YouTube dialog, the drop zone's rows, and the L-005 drag summon. HTML5 `dragstart` for drag-out is assumed to fire with Tauri's own drop handler enabled (true on macOS per the plugin's example; not observed).
**State left behind:** debug app rebuilt and left running. T1 to T3 uncommitted on `dev`.
**Next:** owner walks through the features (HANDOFF lists them); fixes follow as attempt 2; then T4.

## L-005 — 2026-11-15 — Tauri rewrite T2: drag did not summon the drop zone (attempt 3)

**Task:** bug fix · **Attempt:** 3 of tauri-rewrite T2 · **Follows:** L-004 · **Outcome:** awaiting owner test · **Related:** plan `tauri-rewrite` T2, N-002
**Prompt:** Owner repeated the hand checks. (Written after the fact: the disk filled during this attempt and no file could be written until the owner freed space.)
**Owner feedback on the previous attempt:** Tray menu works without a crash, the corner is clickable, the drop zone opens from the tray and closes, a drop on it lands. Dragging a file from Finder does not summon the zone. The main window shows a bare "tomd shell (T2)" page (the placeholder, expected until T3).
**What was tried:** Read the system drag pasteboard during the owner's Finder drag: it did carry `public.file-url`, so the detection data was right and the miss was the global `NSEvent` monitor not being called. Rewrote `src-tauri/src/drag_watch.rs` to poll instead (every 120 ms): left button down (`NSEvent.pressedMouseButtons`) plus a changed drag-pasteboard `changeCount` that carries file URLs shows the zone; button up hides it after a 350 ms grace so the window's drop event can pin it first.
**Result:** `cargo clippy` clean. Not built in that session: the disk was full (`No space left on device`; `src-tauri/target` with debug info was the main contributor). Built in L-006.
**Why it did or did not work:** Inferred: macOS 27 does not deliver global mouse-drag events to a monitor without a permission tomd does not hold. Polling needs none.
**Decisions and rejected alternatives:** Rejected asking for Accessibility / Input Monitoring permission for a monitor. The plan's fallback (show on any drag near the anchor) was not needed since the pasteboard does identify file drags.
**Not checked:** the polling watcher in a running app.
**State left behind:** as L-006.
**Next:** owner drags a file from Finder with the rebuilt app.

<!-- Entry shape — newest first: insert each new entry directly under this header, above the previous one; the ID counts upward (L-008 above L-007); never reuse an ID:

## L-004 — 2026-11-15 — Tauri rewrite T2: blank windows after first owner test (attempt 2)

**Task:** bug fix · **Attempt:** 2 of tauri-rewrite T2 · **Follows:** L-003 · **Outcome:** awaiting owner test · **Related:** plan `tauri-rewrite` T2
**Prompt:** Owner tested the debug app.
**Owner feedback on the previous attempt:** The menu bar icon opens its menu and does not crash; "Open window view" shows the window after it was closed; Auto-convert toggles; Quit works. But the main window is blank white, "Open drop zone" shows nothing, and "Add YouTube video" and "Settings" only show the blank window.
**What was tried:** Looked at the built frontend: the JS bundle was 2,998 bytes. `src/main.tsx` held the placeholder component instead of the entry point: `src/Main.tsx` had been written after `src/main.tsx`, and on the case-insensitive macOS filesystem they are the same file, so nothing ever called `createRoot`. The transparent drop zone window with no content is invisible, which explains "nothing happens". Renamed the component file to `src/MainWindow.tsx` and restored `src/main.tsx`.
**Result:** Bundle is 241.50 kB. A capture of the tomd window alone (`screencapture -l <window id>`) shows the placeholder UI rendered, with the settings loaded and the sidecar's `environment_report` printed. `cargo clippy` and `bun run typecheck` clean.
**Why it did or did not work:** As above. The L-003 checks (process up, window on screen) could not tell a blank webview from a rendered one; a window capture can, and is now the check.
**Decisions and rejected alternatives:** A temporary error overlay was added to `index.html` for diagnosis and removed again.
**Side effect found and reverted:** The first launch in L-003 ran `migrate_login_item`: it deleted the owner's 0.1.x `~/Library/LaunchAgents/me.thekiwidev.tomd.plist` and registered `~/Library/LaunchAgents/tomd.plist` pointing at `src-tauri/target/debug/.../tomd`. Removed the new plist and recreated the old one in the format `native._set_login_item_mac` writes, with `/Applications/tomd.app/Contents/MacOS/tomd` as the program (the original file's exact bytes were not kept). `migrate_login_item` now returns early in debug builds.
**Not checked:** drop zone from the tray, drag detection, corner clickability, menu-bar-only: still the owner's hand checks.
**State left behind:** debug app rebuilt and running; T1 and T2 uncommitted.
**Next:** owner repeats the hand checks.

## L-003 — 2026-11-15 — Tauri rewrite T2: shell, tray, drag watcher (attempt 1)

**Task:** refactor · **Attempt:** 1 of tauri-rewrite T2 · **Follows:** L-002 · **Outcome:** awaiting owner test · **Related:** plan `tauri-rewrite` T2, ADR-001, N-001, N-002
**Prompt:** "Start T2".
**What was tried:** Scaffolded Tauri v2 with bun from the `react-ts` template (generated in a scratch directory, then written into the repository). Wrote `src-tauri/src/{lib,settings,sidecar,tray,windows,drag_watch}.rs` and a placeholder UI (`src/Main.tsx`, `src/DropZone.tsx`) over `src/ipc.ts` and `src/settings.ts`. Details per file: ARCHITECTURE § 9.
**Result:** `cargo check` and `cargo clippy` clean, `cargo test` 3 passed, `bun run typecheck` clean. `bun run tauri build --debug --bundles app` produced a 27.45 MiB unoptimised bundle. Launched it: the process stayed up, `sidecar.py` ran as its child, and a `CGWindowListCopyWindowInfo` listing showed the main window on screen and the 300 x 260 drop zone window at (1366, 776) **not** on screen. The same listing showed the running 0.1.11 app with a 116 x 116 window on screen at (1562, 912), layer 8: the hot-corner of N-002, observed directly.
**Why it did or did not work:** Builds and starts. Whether the tray menu opens without a crash and whether a Finder drag summons the zone is unknown: `osascript` has no assistive access on this machine, so an agent cannot click the menu bar or drag a file.
**Decisions and rejected alternatives:** Drag end is detected by polling `NSEvent.pressedMouseButtons` rather than a `leftMouseUp` monitor, because a global monitor does not see events delivered to tomd's own windows (a drop on the zone). The zone is shown on any file drag, not only when the pointer nears the anchor (simpler; the plan allowed it). Settings are owned by Rust, not the JS store plugin, so there is one writer. Vite outputs to `dist-ui/`. The `dialog`, `opener`, `clipboard-manager` and `drag` plugins were left for T3.
**Not checked:** tray menu, drag detection, drop pinning, all-Spaces and full-screen behaviour, menu-bar-only, start at login and the LaunchAgent migration (the owner's old plist was not touched because that code path only runs if the file exists; whether it exists was not looked at), the release build (no frozen sidecar yet).
**State left behind:** T1 and T2 uncommitted on `dev`. The debug app was left running for the owner's checks, alongside the owner's 0.1.11 app.
**Next:** owner hand checks; see HANDOFF.

## L-002 — 2026-11-15 — Tauri rewrite T1: Python sidecar (attempt 1)

**Task:** refactor · **Attempt:** 1 of tauri-rewrite T1 · **Follows:** L-001 · **Outcome:** worked · **Related:** plan `tauri-rewrite` T1, ADR-001
**Prompt:** same request as L-001; the approved plan's first code task.
**What was tried:** Moved `SUPPORTED_EXTENSIONS`, `collect_paths`, `parse_youtube_url`, `youtube_video_id`, `canonical_youtube_url`, `slugify`, `unique_output` from `app.py` into `links.py` (text moved, only `collect_paths` changed: it takes path strings instead of `QUrl`). Wrote `sidecar.py`: one JSON request per stdin line, a thread per request, `log` events then one `result` event; `sys.stdout` is redirected to stderr so stray prints cannot corrupt the protocol. Added pytest and `tests/`.
**Result:** `uv run pytest`: 24 passed. `echo '{"id":1,"method":"convert_file",...}' | uv run python sidecar.py` converted a CSV to a Markdown table. `import app` works under `QT_QPA_PLATFORM=offscreen`.
**Why it did or did not work:** First run failed one test (`KeyError: 1`): the sidecar called `os._exit(0)` when stdin closed, killing request threads before they replied. Changed to non-daemon threads and a plain return, so running requests finish first; this also avoids killing an install halfway.
**Decisions and rejected alternatives:** `youtube_plan` stays in Python (called per keystroke for the filename preview) rather than porting the URL rules to TypeScript, so there is one copy of the validation. Install and repair results carry the managed `markitdown` path, and `environment_report` carries `venv_dir`, so the UI needs no path logic.
**Not checked:** the PySide6 app was not run by hand after the move; the frozen (PyInstaller) sidecar build is T4.
**State left behind:** T1 files uncommitted on `dev`; see HANDOFF.
**Next:** owner review, then T2.

## L-001 — YYYY-MM-DD — <short title> (attempt N)

**Task:** feature | enhancement | bug fix | refactor | maintenance | investigation | question · **Attempt:** N of <topic> · **Follows:** L-### or none · **Outcome:** worked | partial | failed | blocked | investigated | awaiting owner test · **Related:** CHANGELOG vX.Y.Z, N-###, ADR-###, plan
**Prompt:** what the owner asked, in their words, shortened
**Owner feedback on the previous attempt:** (retries only) what they tested, what was wrong, verbatim where useful
**What was tried:** approach and mechanism; the files and functions touched and why
**Result:** what happened, with evidence — commands, output, errors, test results
**Why it did or did not work:** the cause, as far as known; mark inference as inferred
**Decisions and rejected alternatives:**
**Not checked:**
**State left behind:** what is true in the code now; what is uncommitted; link to HANDOFF if work continues
**Next:** the exact next action, or "none"
-->

## L-001 — 2026-11-15 — Adopt kiwi; analyse three defects; plan the Tauri rewrite (attempt 1)

**Task:** maintenance + investigation · **Attempt:** 1 of tauri-rewrite · **Follows:** none · **Outcome:** partial · **Related:** N-001, N-002, N-003, ADR-001, plan `tauri-rewrite`
**Prompt:** Install the kiwi AI system and commit it, then analyse everything that needs doing and make a detailed plan: make the app lightweight and modern (Tauri, Python kept in the background); the floating drop zone leaves a dead area where it is anchored; a dropped file renders a broken row until Convert is pressed; clicking the menu bar icon closes the app.
**What was tried:** Read `app.py`, `backend.py`, `native.py`, the build scripts and the changelog; parsed the two crash reports from today in `~/Library/Logs/DiagnosticReports`. Asked the owner four decisions, wrote a plan, got it approved, then ran `kiwi agent` (ADOPT) and wrote the `docs/ai` system from the templates.
**Result:** Root causes recorded in N-001 (Qt plugin assertion on macOS 27, evidenced by the crash report), N-002 (permanent sensor window) and N-003 (layout, inferred). Owner chose: Tauri now without patching Qt, React + TypeScript + Tailwind, frozen Python sidecar, macOS first. Kiwi decisions: all rules adopted with testing overridden, caveman ultra, context docs for MEMORY / NOTES / CHANGELOG, Tier 0 + 1 plus an ADR and a plan.
**Why it did or did not work:** Investigation and adoption complete; no application code written yet.
**Decisions and rejected alternatives:** see ADR-001.
**Not checked:** N-003 was not reproduced (no screenshot arrived, and running the app would write the owner's QSettings); whether a newer PySide6 fixes N-001; the drag-pasteboard technique on macOS 27.
**State left behind:** only AI system files added; `RESUME-EVIDENCE.md` untouched.
**Next:** T1 of the plan (`links.py`, `sidecar.py`, pytest).
