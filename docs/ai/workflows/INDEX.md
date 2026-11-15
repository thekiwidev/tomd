---
doc: workflows/INDEX
purpose: "Registry of the repeatable workflows and project skills agents run here — what triggers each, and its parameters"
authority: reference
hosts_rules: []
mirrors_rules: [RULE-CORE-004, RULE-KIND-001, RULE-KIND-002]
last_reviewed: "2026-11-15"
---

# Workflows — index

A registry, not a home: every workflow lives in `.agents/skills/<name>/SKILL.md` (`kind: workflow`, linked into `.claude/skills/`) and nothing else lives in this directory (RULE-KIND-001). Before classifying a task, match the request against the Triggers column; on a match, run that workflow as written (RULE-KIND-002). Create or update one with the `create-workflow` skill (`kiwi new workflow <name>` scaffolds it and adds its row); `kiwi doctor` checks shape and registration.

Resolved per `AGENT-CORE.md` § 8 (project copy → `~/.thekiwidev/skills/<name>` → your installed copy).

## Workflows

| Workflow | Scope | Triggers | Parameters |
| --- | --- | --- | --- |

No project workflows yet.

## Lifecycle skills (global)

| Skill | Vendored | Use it when |
| --- | --- | --- |
| `create-prd` | no | defining a new product capability (writes to `docs/ai/prd/`) |
| `feature-workflow` | no | any request that introduces new product behaviour |
| `bugfix-workflow` | no | any defect or regression |
| `create-workflow` | no | setting up or changing a workflow |
| `kiwi-author` | no | creating or updating a skill, rule, agent, plan or decision |
| `kiwi-system` | no | initializing / upgrading / auditing / amending this system |

## Skills (project)

| Skill | Use it when |
| --- | --- |
