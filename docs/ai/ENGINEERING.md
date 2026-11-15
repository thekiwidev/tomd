---
doc: ENGINEERING
purpose: "Code-writing standards that actually apply in this repository: language, types, naming, boundaries, validation, errors, security, data, dependencies, testing, review"
authority: canonical
hosts_rules: []
mirrors_rules: [RULE-GIT-001]
last_reviewed: "2026-11-15"
---

# ENGINEERING — tomd

> Only standards that are real project requirements. Where this document is silent, the global rules in `~/.thekiwidev/rules/` apply (coding-style, testing, security, patterns, performance, git-workflow); where it speaks, it wins. Competing conventions found in the code are resolved here (canonical pattern) and recorded in `NOTES.md` (legacy pattern, status: `legacy, do not extend` / `migration in progress` / `tolerated`).

## 0. Global rules in force

The owner's global rules live in `~/.thekiwidev/rules/` and are **pointed to, never copied**. Adopted rules update themselves when the global file changes; overrides stay until amended here. To change a row, say "amend rule: …" in this project.

| Global rule | Status | Project statement / reason |
| --- | --- | --- |
| `~/.thekiwidev/rules/agents.md` | adopted | — |
| `~/.thekiwidev/rules/caveman.md` | adopted | level for this project is `ultra` (`.caveman.json`) |
| `~/.thekiwidev/rules/coding-style.md` | adopted | — |
| `~/.thekiwidev/rules/continuity.md` | adopted | — |
| `~/.thekiwidev/rules/docs-format.md` | adopted | applies to new `CHANGELOG.md` entries; the 0.1.x entries keep their Keep a Changelog shape |
| `~/.thekiwidev/rules/git-workflow.md` | adopted | RULE-GIT-001 is canonical in AGENT-CORE.md § 5 |
| `~/.thekiwidev/rules/hooks.md` | adopted | — |
| `~/.thekiwidev/rules/kinds.md` | adopted | — |
| `~/.thekiwidev/rules/patterns.md` | adopted | — |
| `~/.thekiwidev/rules/performance.md` | adopted | — |
| `~/.thekiwidev/rules/security.md` | adopted | — |
| `~/.thekiwidev/rules/task-scope.md` | adopted | — |
| `~/.thekiwidev/rules/testing.md` | overridden | RULE-ENG-001, § 7 below |

Decided by the owner on 2026-11-15.

## 1. Language and type posture

Python 3.12 (`requires-python = ">=3.12"`), type hints on public functions, no type checker configured. The Tauri rewrite adds Rust and TypeScript (strict); their posture is recorded here when that code lands.

## 2. Naming

Python: `snake_case` functions, `PascalCase` classes, module-level `UPPER_CASE` constants, a leading underscore for module-private helpers (as in `backend.py`).

## 3. Module boundaries

`backend.py` holds everything that touches the system (finding Python, installing and repairing MarkItDown, running a conversion) and imports only the standard library; it must stay free of any UI import so it can run as a sidecar. UI code calls it and never shells out itself.

## 4. Validation and errors

Input from the user (dropped paths, YouTube links) is validated before it reaches MarkItDown. A failure shown to the user is a sentence a person can act on; `backend._readable_error` is the single place raw MarkItDown errors are translated.

## 5. Security and data handling

No secrets exist in this project. Subprocesses are started with argument lists, never a shell string. Downloads (the `uv` bootstrap) use the system trust store.

## 6. Dependencies

`uv` and `uv.lock`. MarkItDown is a development dependency only and is never bundled into the app. A new runtime dependency needs a reason; one that adds significant size needs the owner's approval (CONSTITUTION § 4).

## 7. Testing expectations

RULE-ENG-001 (overrides the global `testing` rule): new non-trivial logic ships with a test, pytest for Python and vitest for TypeScript; a bug fix ships with its regression test where the path can be automated. No coverage percentage gate and no mandatory E2E suite. Tray, drop zone and drag-and-drop behaviour is verified by hand in the built app (VERIFICATION.md § 2).

## 8. Review expectations

Solo project: the owner reviews the working tree before committing. Agents run the `code-reviewer` agent on non-trivial changes.

## 9. Git conventions

Owner-controlled (RULE-GIT-001, `AGENT-CORE.md` § 5). Work happens on `dev`; `main` is the release branch; releases are `v*` tags that trigger `.github/workflows/release.yml`. Existing history uses plain imperative subjects; commits an agent is authorised to make use conventional commits per the global `git-workflow` rule.
