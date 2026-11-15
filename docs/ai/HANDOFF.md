---
doc: HANDOFF
purpose: "The baton for unfinished work — what is happening now and what the next agent needs to continue"
authority: canonical
hosts_rules: []
mirrors_rules: [RULE-GIT-001]
last_reviewed: "2026-11-15"
---

# HANDOFF — tomd

## Status

**ACTIVE — tomd 0.2.0 is built and documented; owner hand checks, commit and release remain — see below.**

<!-- When active, one block per task, newest first (RULE-DOC-016):

## <Task>
**Objective:** (the idea, the user's goal, what it must do and not do)
**Why:** (the problem or reason behind it)
**Approach:** (how it is being achieved; mechanism, key functions)
**Decisions and rejected alternatives:**
**Findings:** (what was learned, with evidence)
**Current branch (read-only; never create/switch):**
**Work completed:**
**Files changed:** (path — why)
**Verification:** (what ran, result)
**Remaining work:**
**Known issues:**
**Owner decisions needed:**
**Next action:** (exact; a new agent can start here with no chat history)

Update this block as you go on long tasks (RULE-DOC-014); an interrupted session must still leave a usable baton.
-->

## tomd 0.2.0: release and remaining hand checks

**Objective:** Release tomd 0.2.0 for macOS: the Tauri v2 app over the Python sidecar, with the Finder Quick Action, the status toast and the drag modes.
**Why:** The owner wanted a lightweight, modern app; the three defects reported on 0.1.11 were in the Qt layer (NOTES N-001 to N-003).
**Approach:** done; see [`ARCHITECTURE.md`](./ARCHITECTURE.md), [`plans/completed/tauri-rewrite.md`](./plans/completed/tauri-rewrite.md), [`plans/active/finder-convert.md`](./plans/active/finder-convert.md), PRD [`prd/prd-finder-convert.md`](./prd/prd-finder-convert.md), [`decisions/ADR-001-tauri-shell-python-sidecar.md`](./decisions/ADR-001-tauri-shell-python-sidecar.md).
**Decisions and rejected alternatives:** ADR-001; per attempt in [`LOG.md`](./LOG.md) L-003 to L-016.
**Findings:** CHANGELOG v0.2.0 → Notes; MEMORY → Gotchas.
**Current branch (read-only; never create/switch):** `dev`
**Work completed:** all code and documentation for 0.2.0 (plan `tauri-rewrite` T0 to T5; plan `finder-convert` F1 to F7). `/Applications/tomd.app` on the owner's Mac is the release build from `dist/`.
**Files changed:** everything is uncommitted on `dev`; the list is CHANGELOG v0.2.0 → Files changed, plus `docs/ai/**`, `MEMORY.md`, `CHANGELOG.md`.
**Verification:** CHANGELOG v0.2.0 → Verification (what passed, what the owner confirmed, what is not verified).
**Remaining work:** (1) Owner hand checks not yet reported: the drag modes Shake to hide, Start small and Hold Option to hide; the "Convert to Markdown in Finder" switch; a failing file showing "Failed" in the toast; a file dropped on the main window with auto-convert off showing its name and select box (closes N-003); Settings switches, Repair and the YouTube dialog. (2) When those pass: move `plans/active/finder-convert.md` to `completed/`, set N-003 to resolved, put the release date in the CHANGELOG heading. (3) Owner: commit, tag `v0.2.0`, push (the tag triggers `release.yml`, which has not been run with the new script).
**Known issues:** shake thresholds in `src-tauri/src/shake.rs` are a first guess. On the owner's Mac, Vorssaint quits a tomd that has no window (MEMORY → Gotchas). `scripts/build_windows.ps1` and `assets/make_icon.py` are broken; `docs/index.html` has two stale claims (MEMORY → Open Questions).
**Owner decisions needed:** the three items under MEMORY → Open Questions; whether and when to enrol for signing (LOG L-013).
**Next action:** wait for the owner's hand-check results; a failure is a new LOG entry (attempt 2 of the task it belongs to) and a fix. With no failures, do Remaining work (2).

## Git status

No branch, stage, commit or history operation has been performed by an agent. Working tree: see the task block. `RESUME-EVIDENCE.md` is untracked, unrelated to this work and left untouched.
