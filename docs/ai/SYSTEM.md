---
doc: SYSTEM
purpose: "The manifest of the AI system itself: what built it, what exists, what was deliberately not built, what the owner overrode, what is still unconfirmed"
authority: reference
hosts_rules: []
mirrors_rules: [RULE-AGENT-001]
last_reviewed: "2026-11-15"
initializer_version: "v3 (kiwi 3.6.0)"
initializer_source: "~/.thekiwidev/skills/kiwi-system/INITIALIZER.md"
kiwi_version: 3.6.0
global_system: ~/.thekiwidev
prd_dir: docs/ai/prd/
vendored: []
context_docs: [MEMORY, NOTES, CHANGELOG]
caveman: "ultra"
generated_at: "2026-11-15"
last_upgraded_at: null
last_amended_at: null
canonical_core: "docs/ai/AGENT-CORE.md"
package_manager: "uv"
mode_history:
  - { date: "2026-11-15", mode: "ADOPT", note: "Tier 0 + 1, plus one ADR and one active plan for the Tauri rewrite" }
agents:
  - { name: "AGENTS.md",                       link: "symlink" }
  - { name: "CLAUDE.md",                       link: "symlink" }
  - { name: "GEMINI.md",                       link: "symlink" }
  - { name: ".github/copilot-instructions.md", link: "symlink" }
  - { name: ".agents/rules/00-agent-core.md",  link: "pointer", reason: "Antigravity workspace rules directory" }
modules:
  present:
    - AGENT-CORE
    - INDEX
    - SYSTEM
    - RULES
    - CONSTITUTION
    - WORKFLOW
    - VERIFICATION
    - MEMORY
    - HANDOFF
    - LOG
    - NOTES
    - CHANGELOG
    - ARCHITECTURE
    - ENGINEERING
    - decisions
    - plans
    - workflows/INDEX
    - context
  pruned:
    - { module: "UPGRADES.md",   reason: "created lazily on the first upgrade" }
    - { module: "AMENDMENTS.md", reason: "created lazily on the first amendment" }
  not_applicable:
    - { module: "domains", reason: "one small app; no separate domains" }
    - { module: "archive", reason: "nothing superseded at adoption" }
verification_commands:
  typecheck: "bun run typecheck && (cd src-tauri && cargo check)"
  lint: "cd src-tauri && cargo clippy"
  test: "uv run pytest && bun run test && (cd src-tauri && cargo test)"
  build: "bash scripts/build_macos.sh"
customizations:
  - { id: "CUST-001", what: "testing rule overridden (RULE-ENG-001)", where: "ENGINEERING.md § 0, § 7" }
  - { id: "CUST-002", what: "caveman ultra for this project", where: ".caveman.json" }
open_confirmations:
  - "Product intent, out-of-scope list and prohibited technologies were not asked at adoption; see MEMORY.md Open Questions"
---

# SYSTEM — the manifest

> This document describes the **AI system**, not the product. Project knowledge never lives here. If the manifest and the repository disagree, the repository wins and this file is corrected. Written **last** in every mode, after the changes it describes have landed.

## What this system is

Generated on 2026-11-15 by `kiwi` 3.6.0 in ADOPT mode over an existing repository: a single-developer Python desktop app (PySide6) with 30 commits, 12 releases, no tests and no previous agent instruction files.

Its purpose is that any coding agent can open the repository, read the entry point and the current-state documents, and continue the work without the previous agent's conversation. It was adopted immediately before the Tauri rewrite, so `MEMORY.md` and `ARCHITECTURE.md` describe the PySide6 app as it is and point to the plan that replaces it.

## Initialization / adoption summary

- **Mode evidence:** no `docs/ai/AGENT-CORE.md`; `pyproject.toml` and `uv.lock` present; 30 commits on `dev`.
- **Tier:** 0 + 1, plus `decisions/` and `plans/` because real planned work exists (the rewrite) `[owner: 2026-11-15]`.
- **Derived facts `[verified]`:** uv is the package manager; Python 3.12; PySide6 6.11; PyInstaller build via `scripts/build_macos.sh` and `scripts/build_windows.ps1`; release workflow on `v*` tags; no test, lint or typecheck tooling; version 0.1.11.
- **Convention conflicts:** none recorded; the UI code is being replaced, so it was not surveyed for competing patterns.
- **Migration ledger:** `CHANGELOG.md` KEEP (integrated as is, Keep a Changelog style; new entries follow RULE-DOC-012); `README.md`, `CONTRIBUTING.md`, `docs/specs/*`, `tomd-interview-guide.md`, `docs/index.html` KEEP + INDEX. Nothing archived. No hand-written agent instruction files existed.
- **Rules decision `[owner: 2026-11-15]`:** all global rules adopted; testing overridden (RULE-ENG-001). Caveman: ultra. Context docs: MEMORY, NOTES, CHANGELOG. No vendoring.
- **In-flight work found:** `RESUME-EVIDENCE.md` untracked at the repository root (a read-only audit dated 2026-11-02); left untouched.

## Source-of-truth hierarchy in force

See [`AGENT-CORE.md`](./AGENT-CORE.md) § 3 — including 6a, the global system.

## Module decisions and their rationale

`domains/` is absent because the app is one small codebase; it becomes applicable if the Tauri app grows separately owned areas. `UPGRADES.md` and `AMENDMENTS.md` are created on first use.

## Owner customizations and why they are protected

**CUST-001 — testing override.** The global 80% coverage and mandatory E2E expectations do not apply; see RULE-ENG-001. Protected because the owner chose it at adoption; an upgrade must not restore the default.

**CUST-002 — caveman ultra.** `.caveman.json` sets `ultra` for this project; chat only, never documents.

## Outstanding confirmations

Product intent, the out-of-scope list and prohibited technologies were not asked at adoption (the owner asked for the system to be installed and the rewrite planned). They are listed in `MEMORY.md` → Open Questions and are asked when a task needs them.

## How to upgrade this system

`kiwi upgrade` in the repository root repairs entry points and vendored copies and prints the UPGRADE prompt; the agent then follows INITIALIZER §24 (dry-run delta table → owner approval → additive execution → `UPGRADES.md` entry → this manifest last). Scaffolding may change; project knowledge never does.

## How to amend a rule in this system

State the rule to any agent ("AMEND: …"). It normalizes it (actor / trigger / obligation / exception / proof), reads [`RULES.md`](./RULES.md) first, cascades to every mirror and executable artifact, checks for orphaned old instructions, appends `AMENDMENTS.md`, and updates this manifest (INITIALIZER §25).
