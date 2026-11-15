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

**ACTIVE — Tauri rewrite (tomd 0.2.0) — see below.**

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

## Tauri rewrite (tomd 0.2.0)

**Objective:** Replace the PySide6 UI with a Tauri v2 shell and a React UI, keeping `backend.py` as a frozen Python sidecar; macOS first. Must fix the three reported defects (NOTES N-001, N-002, N-003) and cut the app from about 100 MB.
**Why:** The owner wants a lightweight, modern app, and all three defects are in the Qt layer.
**Approach:** [`plans/active/tauri-rewrite.md`](./plans/active/tauri-rewrite.md); decision record [`decisions/ADR-001-tauri-shell-python-sidecar.md`](./decisions/ADR-001-tauri-shell-python-sidecar.md).
**Decisions and rejected alternatives:** in ADR-001.
**Findings:** root causes of the three defects, in NOTES N-001 to N-003.
**Current branch (read-only; never create/switch):** `dev`
**Work completed:** plan approved by the owner on 2026-11-15; kiwi AI system adopted (T0).
**Files changed:** only the AI system files (`docs/ai/**`, `MEMORY.md`, entry points, `.caveman.json`).
**Verification:** `kiwi doctor --project`.
**Remaining work:** T1 to T5 of the plan; no application code has been written.
**Known issues:** the drag-pasteboard detection in T2 is unverified on macOS 27 (plan risk 1).
**Owner decisions needed:** none open.
**Next action:** start T1 of the plan: create `links.py` by moving the pure helpers out of `app.py:301-431`, then `sidecar.py` and its pytest tests.

## Git status

No branch, stage, commit or history operation has been performed by an agent. Working tree: see the task block. `RESUME-EVIDENCE.md` is untracked, unrelated to this work and left untouched.
