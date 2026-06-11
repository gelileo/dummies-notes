# Knowledge Base Index

Grouped by subject area. Each article is a standalone reference. Connections at the bottom analyze how multiple concepts interact.

## dummies_notes (this repo)

| Article | Summary | Updated |
| --- | --- | --- |
| [concepts/dummies-notes/concept-decomposition.md](concepts/dummies-notes/concept-decomposition.md) | Single-level decompose skill (`.claude/skills/concept-decompose/`): decomposition.json schema, atomicity rule, jargon rule, slug+definition identity, validator gate, golden RSA + modular-arithmetic examples; graph walk is Phase 3 | 2026-06-10 |
| [concepts/dummies-notes/illustration-engine.md](concepts/dummies-notes/illustration-engine.md) | Shipped skill at `.claude/skills/concept-illustrator/`: runbook-first workflow, runbook + commentary required per frame, linter, figure validator, slideshow viewer, golden quicksort example; self-sufficiency rule (Phase 5): every figure teaches standalone; compose-from-children retired | 2026-06-10 |
| [concepts/dummies-notes/atomic-illustration-catalog.md](concepts/dummies-notes/atomic-illustration-catalog.md) | Shipped registry (`scripts/concept_registry.py` + `registry/`): slug+definition addressing, registered→illustrated lifecycle, four CLI verbs, corrupt-entry error contract, seeded with quicksort (illustrated) + modular-arithmetic; versioning/invalidation is Phase 3+ | 2026-06-10 |
| [concepts/dummies-notes/orchestration-workflow.md](concepts/dummies-notes/orchestration-workflow.md) | Full pipeline (all five phases shipped): BFS decompose → illustrate every figurable node → review → finalize → assemble → chain review; produces `output/<topic>/index.html` + `map.html` + `chain-review.json`; TCP re-run chain review **passed** (Phase 5 acceptance); deterministic tools: `graph_check.py`, `assemble.py` | 2026-06-10 |

## External Systems

| Article | Summary | Updated |
| --- | --- | --- |
| _(populate as integrations are added)_ | | |

## Connections

| Article | Summary | Updated |
| --- | --- | --- |
| _(populate as cross-cutting articles emerge)_ | | |
