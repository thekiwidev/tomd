---
doc: plans/finder-convert
purpose: "Finder Quick Action 'Convert to Markdown', a status toast at the anchor, and a setting for moving the drop zone aside mid-drag"
authority: canonical
hosts_rules: []
mirrors_rules: []
last_reviewed: "2026-11-15"
---

# finder-convert

**Status:** active · **Classification:** new feature + enhancement · **Source:** [`../../prd/prd-finder-convert.md`](../../prd/prd-finder-convert.md) (approved 2026-11-15) · **Owner approval:** 2026-11-15

## Objective

Implement the PRD: convert files from Finder's right-click menu in the background with a toast at the drop zone's anchor, and let the user choose how the drop zone gets out of the way during a drag.

## Scope

PRD tasks FE01 to FE06, BC01 to BC05, ST01 to ST06, DZ01 to DZ06, on macOS, in the Tauri app.

## Non-goals

As PRD § 5: no top-level Finder item (needs signing), no folders from Finder, no output-folder choice, no Windows. No new dependency: no deep-link or single-instance plugin (see Approach).

## Dependencies

Plan `tauri-rewrite` T1 to T3 (done, uncommitted). Nothing new to install. macOS pieces used: Automator service bundle format, `open(1)`, `/System/Library/CoreServices/pbs`.

## Approach

- **How files reach tomd.** The Quick Action runs one shell line: `open -g -a "<tomd.app>" "$@" --args --background`. macOS delivers the files to tomd as a file-open event whether it is running or not (Tauri: `RunEvent::Opened { urls }`), `-g` keeps it in the background, and `--background` is seen only on a fresh launch, where it stops `lib.rs` from showing the main window (FE05). macOS itself keeps a single instance for `open -a`. Rejected: a `tomd://` URL scheme (needs the deep-link plugin and URL-encoding paths in shell) and passing arguments to the binary (ignored when the app is already running; a second process otherwise).
- **Side effect, accepted:** any file opened with tomd (for example dropped on its Dock icon) converts the same way. tomd declares no document types, so it does not appear in "Open With".
- **The Quick Action** is a generated bundle `~/Library/Services/Convert to Markdown.workflow` (`Contents/Info.plist` with `NSServices`, `Contents/document.wflow` with one Run Shell Script action). Its accepted types are a UTI list (PDF, Word, Excel, PowerPoint, images, audio, HTML, text, CSV, JSON, XML, EPUB, ZIP, Outlook message) kept next to the generator; tomd still filters through `collect_paths`, so a wrong UTI can only show the entry on a file that then reports "Not supported". Installed at launch when the app runs from an `Applications` folder and the bundle is missing or points elsewhere; never from a path containing `/target/`.
- **Queue.** `Row` gains `background: boolean`. A new `add` option re-queues an existing finished or failed row (BC04). Rust forwards opened paths to the main webview as the event `sources-opened`; `MainWindow.tsx` adds them with `enqueue: true`.
- **Toast.** A third window `toast` (260 x 48, transparent, borderless, non-activating, all Spaces), placed by the existing `anchor_position`. `Toast.tsx` derives its text from the mirrored queue (`queue-changed`): the background rows of the current run. The main window asks Rust to show it when a background run starts and to hide it 2 s after success or 4 s after a failure; not shown while the drop zone panel is open.
- **Drag modes.** New setting `drag_mode`: `show` (default), `shake`, `small`, `option`. All in `drag_watch.rs`, which polls at 30 ms while a drag is active (120 ms idle, as now). `option`: `NSEvent.modifierFlags`. `shake`: a pure function counts horizontal direction reversals (at least 3 within 600 ms, each leg at least 40 px) and hides the zone until the drag ends. `small`: the drop zone window is resized to a 132 x 40 pill and grows to full size while the pointer is within 180 px of it; the React side switches layout with a CSS height media query, no extra event.

## Ordered tasks

| ID | Task | Acceptance criteria | Status |
| --- | --- | --- | --- |
| F1 | Prove the Quick Action route before building on it: hand-written workflow bundle in `~/Library/Services` whose script appends its arguments to a file; `pbs -update` | Owner sees "Convert to Markdown" under right-click, Quick Actions on a PDF and not on a folder; the file lists the chosen paths. If the hand-written bundle is not picked up, stop and report (fallback: build it once in Automator and ship that file) | agent half done 2026-11-15 (LOG L-012): bundle written, listed by `pbs -dump_pboard`, script runs through `automator -i`. Owner confirmed on 2026-11-15 that the entry shows and converts a PDF with the toast (LOG L-015). `.ipynb` and `.msg` have no system type and cannot be offered the entry |
| F2 | Queue: `background` flag and re-queue of finished / failed rows in `src/queue.ts`; tests first | `bun run test` passes with new cases for BC01 and BC04 | done 2026-11-15 (10 tests) |
| F3 | Rust: handle `RunEvent::Opened` (emit `sources-opened`), `--background` skips `show_main`; `MainWindow.tsx` listens and enqueues | With tomd running, `open -g -a /Applications/tomd.app file.csv` writes `file.md`, no window appears; with tomd quit, the same plus `--args --background` starts it with no window | done 2026-11-15, both cases run by the agent (LOG L-014) |
| F4 | Toast window: `tauri.conf.json` window, `windows.rs` show / hide / place commands, `src/Toast.tsx`, timing in `MainWindow.tsx`; setup-needed text (BC05) | Window capture shows "Converting …" then "Done"; it is gone after about 2 s; a failing file shows "Failed" for about 4 s; clicking opens the main window | code done 2026-11-15; "2 converted" captured and gone after 6 s. Failure text, setup text and the click are owner checks |
| F5 | Quick Action generator and installer in Rust (`quick_action.rs`), commands for status / install / remove, "Finder" section in `SettingsPage.tsx` | Unit test: generated plists parse and contain the app path and UTI list; the installed app creates the bundle at launch; Settings shows "Installed" and Remove deletes it; a debug run from `target/` installs nothing | code done 2026-11-15: unit tests pass, the installed app wrote the bundle (`plutil -lint` OK). Shipped as a Settings switch (`finder_action`), not a button. Owner check: the switch removes and restores the entry |
| F6 | Drag modes: `drag_mode` setting (validation, store), shake detector with unit tests, Option and small modes in `drag_watch.rs`, pill layout in `DropZone.tsx`, "When a drag starts" control in Settings | `cargo test` covers the shake detector and the setting's validation; owner confirms each mode lets a file be dropped on a Finder window under the anchor, and `show` behaves as before | code done 2026-11-15: `cargo test` covers the detector and validation. All behaviour is the owner's check; thresholds untuned |
| F7 | Documentation: MEMORY (features, settings), ARCHITECTURE § 9, VERIFICATION if a gate changed, CHANGELOG entry with the release it ships in, LOG, context docs; this plan to `completed/` | `kiwi doctor --project` clean; cold-start test passes | done 2026-11-15 (LOG L-017), except the move to `completed/`, which waits for the owner's checks of F4 to F6 |

The owner reviews after F1 (go / no-go on the route) and after F6.

## Verification

`uv run pytest`, `bun run test`, `bun run typecheck`, `cargo clippy`, `cargo test`, debug bundle build. Agents cannot right-click in Finder, drag files or press Option on this machine: F1, the Finder half of F3, and all of F6's behaviour are the owner's hand checks. Agent-checkable: `open -g -a` conversions (F3), window captures of the toast (F4), the generated bundle on disk (F5).

## Documentation impact

F7. `MEMORY.md` → Features and Environment; `ARCHITECTURE.md` § 9 (third window, `sources-opened`, `quick_action.rs`, drag modes); `CHANGELOG.md` under the version chosen below; plan `tauri-rewrite` T4 gains "ship the Quick Action from the release build" if this lands in 0.2.0.

## Owner decisions required

Both decided by the owner on 2026-11-15 as recommended (0.2.0; accept the Dock icon side effect).

1. **Release:** in 0.2.0 before packaging (T4), or 0.2.1 after 0.2.0 ships? Recommended: 0.2.0, because T4 is where the installed app path the Quick Action points at becomes final, and doing it once avoids reworking the installer.
2. **Dock icon side effect:** a file dropped on tomd's Dock icon will convert in the background like a Finder conversion. Accept, or should that open the main window instead?

Risks: (1) a hand-written workflow bundle may not register without Automator having saved it; F1 exists to find out first. (2) Shake detection is tuned by feel; thresholds may need a second pass after the owner tries it. (3) `RunEvent::Opened` during startup arrives after `setup`; the webview may not be listening yet, so opened paths are held in Rust until the main window reports ready.
