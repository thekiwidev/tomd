---
doc: CONSTITUTION
purpose: "Enduring engineering principles that do not change with the task"
authority: canonical
hosts_rules: [RULE-YAGNI-001]
mirrors_rules: [RULE-GIT-001, RULE-VERIF-002]
last_reviewed: "2026-11-15"
---

# CONSTITUTION — tomd

## 1. YAGNI governs (RULE-YAGNI-001)

Create only what has a real purpose now. The ladder — stop at the first rung that works:

1. Does this need to exist?
2. Does something already do it?
3. Can an existing thing be reorganised instead of duplicated?
4. Can a smaller structure satisfy it?
5. Only then create the new file, abstraction, or dependency.

YAGNI forbids: speculative abstraction, "future-proofing", configuration for flexibility nobody asked for, service/repository layers by default, documents for their own sake. YAGNI does **not** excuse: skipping validation, skipping tests, skipping security, or skipping documentation of what was actually built.

In this project: tomd adds no Markdown post-processing and no converters of its own; MarkItDown is not bundled; there is no plugin system, no CLI and no API.

## 2. Reuse over creation; smallest correct change

Search the codebase before writing. The smallest change that is correct beats the most elegant one that is larger. Correctness before cleverness.

## 3. Mandatory, always

- Security: no secrets in code or docs; validate every input; authorise at every boundary, server-side.
- Tests accompany the logic they test.
- Fixed decisions are not relitigated (RULE-AUTON-002).
- Documentation describes reality; when reality changes, the documentation changes in the same task.
- The owner controls Git (RULE-GIT-001, canonical in `AGENT-CORE.md` § 5).
- No gate is ever weakened to pass (RULE-VERIF-002, canonical in `VERIFICATION.md`).

## 4. Project-specific principles *(if applicable)*

- **Lightweight.** The app should be small and feel native; a dependency that adds tens of megabytes needs the owner's approval. Reason: the 100 MB PySide6 build is why the rewrite exists `[owner: 2026-11-15]`.
- **Honest attribution.** tomd is a wrapper; text and docs never imply it does the conversion itself.
- **Failures explain themselves.** An error shown to the user says what went wrong and what to do, never a raw traceback (see `backend._readable_error`).
