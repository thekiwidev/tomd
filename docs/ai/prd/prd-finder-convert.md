---
doc: prd-finder-convert
purpose: "Product requirements: Convert to Markdown from Finder's right-click menu, a status toast, and a way to move the drop zone aside mid-drag"
authority: canonical
status: approved by the owner 2026-11-15
last_reviewed: "2026-11-15"
---

# PRD — Convert to Markdown from Finder, and drop zone dismissal

## 1. Introduction / Overview

Today a file is converted by dragging it onto tomd. The owner wants to convert a file where it already is: right-click it in Finder, choose "Convert to Markdown", and get the `.md` beside it without any tomd window opening. Progress is shown by a small toast at the screen position where the drop zone opens.

The same request covers one problem found while testing 0.2.0: the drop zone appears as soon as any file drag starts, so it can cover the place the file was meant to go. The owner wants a way to get it out of the way during a drag, and wants to choose the method in Settings.

Owner's answers that fix the scope (2026-11-15): 1A, 2B, 3A, 4B, 5A, and for question 6 all three methods offered as a setting.

## 2. Goals

- Convert one or more supported files from Finder's right-click menu in two clicks, with no window shown.
- Show that a conversion is running and when it has finished, at the drop zone's anchor, then get out of the way without any action from the user.
- Keep the result reachable afterwards (Copy, Reveal, retry) in the main window.
- Let a drag reach a target that lies under the drop zone, using a method the user picks.

## 3. User Stories

- As a user, I right-click a PDF in Finder, choose Quick Actions, "Convert to Markdown", and a `.md` with the same name appears beside it.
- As a user, I select five files, choose the same entry once, and see "Converting 2 of 5" and then "Done" in a small toast that disappears by itself.
- As a user, when a conversion fails I see "Failed" briefly and can open tomd's main window later to read why and retry.
- As a user, I can use the entry when tomd is not running; it starts in the menu bar without opening a window.
- As a user dragging a file to a folder that sits under the drop zone, I shake the pointer (or use the method I chose in Settings) and the drop zone moves out of the way for that drag.

## 4. Features / Tasks

- **Finder Entry**:
  - FE01: Provide a Finder Quick Action named "Convert to Markdown", reached by right-click, Quick Actions (also listed under Services).
  - FE02: The entry is offered for files only, not folders.
  - FE03: The entry is offered for the file types tomd supports (the `SUPPORTED_EXTENSIONS` set in `links.py`); it accepts one file or a multiple selection.
  - FE04: tomd installs the entry itself (no manual step in Automator or System Settings beyond what macOS itself requires) and keeps it in step with the installed app; Settings shows whether it is installed and offers to install or remove it.
  - FE05: Choosing the entry while tomd is not running starts tomd with only its menu bar icon: no main window, no Dock bounce that brings a window forward.
  - FE06: Choosing the entry never opens or raises the main window or the drop zone panel.

- **Background Conversion**:
  - BC01: Files sent from Finder are added to the same queue the main window uses and start converting at once, whatever the auto-convert setting is.
  - BC02: The Markdown is written beside the source, same name with `.md`, replacing an existing file of that name (the behaviour of every other conversion in tomd).
  - BC03: Each file appears as a row in the main window list with its usual state and actions (Copy MD, drag out, Reveal, retry by Run).
  - BC04: A file already in the list is not added twice; if it has finished or failed it is converted again.
  - BC05: If MarkItDown is not installed, nothing converts; the toast says setup is needed and clicking it opens the main window on the setup page.

- **Status Toast**:
  - ST01: A small toast appears at the drop zone's anchor position (the Position setting) when a Finder conversion starts; it does not take focus from the app in use and shows on every Space.
  - ST02: While running it reads "Converting <file name>" for one file and "Converting 2 of 5" for several.
  - ST03: On success it reads "Done" (with the count when more than one) and disappears after about two seconds.
  - ST04: On failure it reads "Failed" (or "3 converted, 2 failed") for about four seconds, then disappears; the reason stays on the row in the main window.
  - ST05: Clicking the toast opens the main window.
  - ST06: The toast is shown for Finder conversions only; conversions started in the main window or the drop zone keep their own progress display. It works when the drop zone feature is switched off.

- **Drop Zone Dismissal**:
  - DZ01: A new setting, "When a drag starts", under the drop zone settings, with four choices: "Show the drop zone" (today's behaviour), "Shake to hide", "Start small", "Hold Option to hide".
  - DZ02: Shake to hide: moving the pointer rapidly from side to side during a drag hides the drop zone until that drag ends.
  - DZ03: Start small: the drop zone appears as a small pill at the anchor and grows to full size only when the dragged file comes near it; it shrinks back when the file moves away.
  - DZ04: Hold Option to hide: while the Option key is held during a drag the drop zone is hidden; releasing the key shows it again.
  - DZ05: In every mode, a hidden or small drop zone does not block a drop on whatever is underneath it.
  - DZ06: The setting is disabled when the drop zone is switched off, and applies immediately.

## 5. Non-Goals (Out of Scope)

- A top-level item in Finder's right-click menu. That needs a signed Finder Sync extension; tomd is unsigned (signing is deferred work). Revisit when the app is signed.
- Converting folders from Finder (owner's answer 4B). Folders are still converted by dropping them on tomd.
- A choice of output folder or file name for Finder conversions.
- YouTube links from Finder or the Services menu.
- A notification-centre notification, sound, or history beyond the main window list.
- Windows (tomd 0.2.0 is macOS only).
- Combining dismissal methods at once (one choice is active at a time).

## 6. Design Considerations

- The toast uses the existing dark theme (`src/app.css`): one line of text, a state icon (spinner, check, alert), rounded pill, about 240 x 44 px, at the anchor with the same margin as the drop zone.
- If the drop zone panel is open at the anchor when a Finder conversion starts, the rows already show progress there; the toast is not drawn over it.
- The "Start small" pill is the drop zone window at a reduced size, so it lands in the same corner and grows in place.
- Settings: the new choice sits directly under Position; the Finder entry gets its own short section ("Finder") with its status and one button.

## 7. Technical Considerations

- Finder entry: an Automator Quick Action (`.workflow` bundle in `~/Library/Services`) that passes the selected files to tomd is the route that works unsigned. How the files reach a running tomd (a `tomd://` URL, a file-open event, or a command-line hand-off) is for the plan; it must not look like "Open with tomd" and must not raise a window (FE06).
- Only one tomd may run: a second launch from the Quick Action must hand its files to the running one.
- The queue lives in the main window's webview (`src/queue.ts`, `src/useQueue.ts`); that webview exists while the window is hidden, so background conversion needs no second runner. The `add` action already supports "enqueue at once".
- Toast: either a third small window or the existing drop zone window in a toast mode; both are shown without activating the app (`windows::order_front`).
- Dismissal: the drag watcher (`src-tauri/src/drag_watch.rs`) already polls every 120 ms; pointer position and the Option key state can be read in the same poll. Shake detection needs a faster poll or direction-reversal counting tolerant of 120 ms samples.
- The release build (plan `tauri-rewrite` T4) must ship or generate the workflow; a debug build should not install a Quick Action that points into `target/`.
- Supported file types are declared once in `links.py`; the Quick Action's accepted types should come from that set rather than a second list.

## 8. Success Metrics

- Right-click, Quick Actions, "Convert to Markdown" on a PDF produces the `.md` beside it with no tomd window appearing, with tomd running and with tomd quit.
- Five selected files produce five `.md` files and one toast sequence ending in "Done".
- A file MarkItDown cannot convert shows "Failed" in the toast and its reason on the row in the main window.
- With each of the three dismissal modes, a file can be dropped on a Finder window located under the drop zone's anchor.
- With "Show the drop zone" selected, behaviour is identical to today.

## 9. Open Questions

Resolved on approval (2026-11-15, "Approve as written"): the default drag mode stays "Show the drop zone"; the Finder entry is installed automatically and removable in Settings. Still open: the release it ships in (asked in the plan).

- Default for "When a drag starts": this PRD assumes "Show the drop zone" stays the default so nothing changes for a user who never opens Settings. Owner may prefer "Shake to hide".
- Should the Finder entry be installed automatically on first launch, or only when the user presses the button in Settings? This PRD assumes automatically, with the button to remove it.
- Should this ship in 0.2.0 (before packaging, T4) or as 0.2.1 after the rewrite is released?
