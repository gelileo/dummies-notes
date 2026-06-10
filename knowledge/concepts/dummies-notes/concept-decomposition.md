---
title: Concept decomposition engine
type: concept
area: dummies-notes
updated: 2026-06-10
status: mature
affects:
  - ".claude/skills/concept-decompose/SKILL.md"
  - ".claude/skills/concept-decompose/scripts/validate_decomposition.py"
references:
  - "concepts/dummies-notes/illustration-engine.md"
  - "concepts/dummies-notes/atomic-illustration-catalog.md"
---

# Concept decomposition engine

Given a target concept, the decomposition engine discovers the **dependency
concepts** required to understand it — the prerequisites on the reasoning
toolchain — until each leaf is **atomic**: small enough that a single figure
explains it clearly.

The ultimate output is a **directed dependency graph** (a concept points to the
concepts it depends on), not a tree — concepts are shared, so the same atomic
node is reached from many parents. Sharing is the whole point: it is what makes
[[atomic-illustration-catalog]] reuse possible. Graph assembly and traversal are
**Phase 3 (Workflow)**. Phase 2 ships the single-level primitive that each node
in that graph is produced by.

## Why divide-and-conquer

Explaining a hard concept end-to-end produces a wall of prose nobody absorbs.
Instead we explain the smallest understandable pieces and compose them. The
learner walks the graph bottom-up; each step adds exactly one new idea on top
of already-illustrated foundations.

## The shipped primitive (Phase 2)

The decomposition skill lives at `.claude/skills/concept-decompose/`. Its
contract is **single-level**: ONE concept in → a canonical slug + plain
definition + atomicity verdict + direct prerequisites out, emitted as a
`decomposition.json`. The skill never recurses — that is the Workflow's job.

### decomposition.json schema

Defined in `references/decomposition-json.md`; enforced by
`scripts/validate_decomposition.py`. Top-level fields:

| Field | Notes |
|---|---|
| `concept` | object — `slug`, `name`, `definition` |
| `audience` | who this is for (default: "a curious adult with no domain background") |
| `atomic` | boolean verdict |
| `atomic_reason` | one or two plain sentences justifying the verdict |
| `prerequisites` | array of concept objects with an extra `why` field; `[]` when atomic |

### Atomicity rule

A concept is **atomic** when BOTH hold:
- one figure of ≤ ~6 frames could make its mechanism click without needing a
  sub-figure, AND
- the remaining ideas it leans on are common knowledge for the audience.

Atomic ⇒ `prerequisites: []`. Non-atomic ⇒ at least one prerequisite.

### Jargon rule

Any term in a definition the audience wouldn't know must itself become a
prerequisite — never lean on an unexplained word. Jargon is a decomposition
signal, not an aside.

### Identity: slug + definition

Two concepts are the same node when their **slug and definition are identical**.
Same slug + same definition → idempotent (no-op re-registration). Same slug +
different definition → `RegistryError`; the caller must coin a qualified slug
(e.g. `mean-average` vs `mean-unkind`). The definition is the contract. The
kebab-case slug regex is **intentionally duplicated** between this skill's
validator and `scripts/concept_registry.py` (each tool stays zero-dependency
and self-contained); keep the two copies in sync.

### Validator gate

Every decomposition must pass before handoff:
```
python3 scripts/validate_decomposition.py path/to/decomposition.json
```
Must print `OK     clean`. The validator exits non-zero on any ERROR; WARNs are
reviewed but do not block.

### Golden examples

Two reference decompositions under `.claude/skills/concept-decompose/examples/`:

- **`rsa-encryption`** — non-atomic, with three load-bearing prerequisites
  (`modular-arithmetic`, `prime-numbers`, `asymmetric-cryptography`). Shows the
  jargon rule in action: definitions use only plain language; technical terms
  become prerequisites.
- **`modular-arithmetic`** — atomic, `prerequisites: []`. The clock-face
  metaphor fits one figure. Its `concept` slug + definition are byte-identical
  to the `modular-arithmetic` prerequisite entry in the RSA example,
  demonstrating slug + definition = identity.

## What is Phase 3

Walking prerequisites recursively, deduplicating against the [[atomic-illustration-catalog]],
detecting cycles **across the graph**, and assembling the full dependency graph
are all Workflow responsibilities deferred to Phase 3. Single-node cycle
detection (a concept listing itself) is enforced in the validator today;
cross-node cycle detection across the wider graph is an explicit Phase 3 open
question.
