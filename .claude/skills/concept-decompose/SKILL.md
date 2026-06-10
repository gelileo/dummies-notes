---
name: concept-decompose
description: >-
  Take ONE concept and break it down one level: a canonical identity, a plain
  definition, an atomicity verdict, and its direct prerequisites — the ideas you
  must understand first. Use this whenever someone wants to know what a concept
  rests on rather than how to draw it. Trigger on phrases like "what do I need to
  know first to understand X", "break down this concept", "find the prerequisites
  of X", "is X atomic enough to illustrate", "what are the building blocks of X",
  or any request to map a concept's immediate dependencies. Produces a single
  `decomposition.json`: the machine-readable input the dummies-notes Workflow
  recurses over and feeds to the illustrator.
---

# Concept decompose

Take ONE concept and look exactly one level down. The output is a single
`decomposition.json`: a canonical identity, a plain definition, an atomicity
verdict, and the direct prerequisites — the ideas the audience must already
understand for this concept to make sense.

**One level only — never recurse.** You decompose the concept you are handed and
stop at its direct prerequisites. Walking *their* prerequisites, detecting cycles
across the graph, and deduplicating against the registry belong to the
dummies-notes Workflow, not here. Doing one thing well is what keeps each
decomposition reviewable.

The output schema — every field, the atomicity rule, and a worked example — lives
in `references/decomposition-json.md`. Read it before your first run.

## Workflow

Follow these steps in order. The judgment lives in steps 2 and 3 — what counts as
atomic, and which prerequisites are genuinely load-bearing.

1. **Canonicalize.** Give the concept a kebab-case slug
   (`^[a-z0-9]+(-[a-z0-9]+)*$`) and a plain one-or-two-sentence `definition`
   written for the audience — default "a curious adult with no domain
   background". The definition is the contract: a curious adult should be able to
   read it once and repeat it back. On a meaning collision, qualify the slug
   (`mean-average` vs `mean-unkind`); the definition disambiguates.

2. **Run the atomicity test.** A concept is **atomic** when BOTH hold:
   - one figure of ≤ ~6 frames could make its mechanism click *without* needing a
     sub-figure, AND
   - the remaining ideas it leans on are common knowledge for the audience.

   Record the verdict in `atomic` and a plain `atomic_reason` (one or two
   sentences). Atomic ⇒ `prerequisites: []`. Not atomic ⇒ at least one
   prerequisite.

3. **List the direct prerequisites** (only when not atomic — typically 2–4). Each
   is a concept object: `slug` + `name` + plain `definition` + a `why` stating
   what the parent cannot be understood without it.

   **The jargon rule.** Any term in *your* definitions the audience wouldn't know
   must itself become a prerequisite — never lean on an unexplained word. Jargon
   is a decomposition signal, not an aside: if the definition needs it, the reader
   needs a picture of it first.

4. **Reuse covered slugs.** If the caller supplies already-covered slugs (from the
   concept registry), reuse those exact slugs for matching concepts. Reuse means
   referencing: link to the existing identity, don't rename it or coin a near-duplicate.

5. **Validate.** Every decomposition must pass the validator before you hand it back:
   ```
   python3 scripts/validate_decomposition.py path/to/decomposition.json
   ```
   It must print `OK     clean`. Fix every ERROR; review every WARN.

## Quality bar

- **Definitions a curious adult could repeat back.** Plain words, one or two
  sentences, no jargon smuggled in. If a term needs explaining, it is a
  prerequisite (step 3), not a parenthetical.
- **Prerequisites are load-bearing.** Each one is something the concept genuinely
  cannot be understood without — and its `why` says so. Drop the nice-to-knows:
  simplicity wins, verbose is boring. A list of six "related" ideas is a failed
  decomposition.
- **No cycles.** A concept never lists itself as its own prerequisite, directly.
  (Cross-node cycle detection across the wider graph is the Workflow's job.)
- **Clean validation.** `OK     clean`, every run.

## Files in this skill

- `references/decomposition-json.md` — the full output schema: field tables, the
  atomicity rule, slug rules, and a worked example. The source of truth for the
  shape of `decomposition.json`.
- `scripts/validate_decomposition.py` — zero-dependency validator. Importable
  (`validate(data)` → `(level, message)` tuples) and runnable as a CLI; exits
  non-zero on any ERROR.
- `examples/rsa-encryption/decomposition.json` and
  `examples/modular-arithmetic/decomposition.json` — the two golden
  decompositions to pattern yours on: the first non-atomic (with prerequisites),
  the second atomic (the clock metaphor, `prerequisites: []`). They share the
  `modular-arithmetic` identity (same slug + definition) to show reuse.
