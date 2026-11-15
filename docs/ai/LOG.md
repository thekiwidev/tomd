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

<!-- Entry shape — newest first: insert each new entry directly under this header, above the previous one; the ID counts upward (L-008 above L-007); never reuse an ID:

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
