---
doc: VERIFICATION
purpose: "The completion gates — the project's real commands, what else a change may require, and the definition of done"
authority: canonical
hosts_rules: [RULE-VERIF-001, RULE-VERIF-002]
mirrors_rules: []
last_reviewed: "2026-11-15"
---

# VERIFICATION — tomd

## 1. The gates (RULE-VERIF-001)

| Gate | Command | Precondition |
| --- | --- | --- |
| Typecheck | none configured | — |
| Lint | none configured | — |
| Test | none configured (the repository has no tests) | — |
| Build | `bash scripts/build_macos.sh` | macOS, `uv` on PATH |

State at adoption (2026-11-15): the PySide6 app has no automated gate except the build. The Tauri rewrite (`plans/active/tauri-rewrite.md`) adds `uv run pytest`, `bun run test`, `bun run tsc --noEmit` and `cargo check`; each is added to this table in the task that creates it, never before it exists.

All gates run before any task is reported complete; the report shows each command and its actual result.

## 2. When the change calls for more *(if applicable)*

- A change to the menu bar icon, the drop zone or drag and drop is checked by hand in the built app on macOS: these paths have no automated coverage and are where the reported defects were.
- After any change touching the tray or windows, confirm no new `tomd-*.ips` file appeared in `~/Library/Logs/DiagnosticReports`.
- Long-running dev servers are run by the owner; ask rather than start one.

## 3. Tests ship with the logic

New behaviour arrives with its tests; a bug fix arrives with the regression test that failed before the fix.

## 4. Never weaken a gate (RULE-VERIF-002)

No test is skipped, deleted or loosened, no lint rule disabled, no type check relaxed, no threshold lowered, to make work appear complete. If a gate is wrong, that is a separate owner-approved change.

## 5. Definition of done — the checklist

```text
[ ] Requirement matches the authoritative product documentation
[ ] Acceptance criteria satisfied
[ ] Existing implementation searched for reuse; no unnecessary abstraction or dependency
[ ] Tests written/updated where required
[ ] All gates pass (actual output in the report)
[ ] Security requirements intact
[ ] Documentation impact review run against the diff; affected layers updated
[ ] Plan updated; changelog updated when required; handoff accurate or cleared
[ ] Derived context docs regenerated and stamped for every changed source (`kiwi ctx status` clean)
[ ] No unauthorised Git operation; owner told it is ready for commit
```
