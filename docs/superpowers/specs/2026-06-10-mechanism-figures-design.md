# Phase 5 — self-sufficient mechanism figures — design

- **Date:** 2026-06-10
- **Status:** approved (design); to be planned next
- **Scope:** enhancement across the decompose skill, the illustrator contract, the workflow, and the deterministic tools. One implementation plan.
- **Parent spec:** `docs/superpowers/specs/2026-06-09-dummies-notes-design.md`
- **Motivation:** two end-to-end runs (RSA, TCP connection lifecycle) had clean per-figure reviews but failing chain reviews with the same root cause — a concept that is *not a decomposition leaf* never gets its own figure, even when its own mechanism is figure-sized. `best-effort-delivery` is the canonical case: its decomposition literally says "the mechanism itself fits in one short figure," yet it was flagged non-atomic (it needs `data-packets`) and so was never drawn.

## Governing principle

**Every illustration teaches its own concept standalone — atomic or not.** A figure never assumes the reader has already absorbed its prerequisites' figures. When a concept is built on fundamentals that *also* have their own figures, those are surfaced as **optional "go deeper" references** — not as building blocks the figure depends on. Composition ("how the parts snap together") is **not** a requirement and is **retired**: the right answer is a self-sufficient figure of the concept itself; structure is already carried by `map.html` and the explainer's "Builds on:" links.

## The two-axis contract

`decomposition.json` currently has one boolean, `atomic`, that conflates two independent questions. Phase 5 splits them:

| Field | Question | Drives |
|-------|----------|--------|
| `atomic` | Are the remaining prerequisites common knowledge — should we **stop decomposing**? | recursion (unchanged) |
| `mechanism_figurable` (new, required bool) | Can **this** concept's own mechanism be taught self-sufficiently in **one figure**, regardless of prerequisites? | **whether the concept gets a figure** |

Examples:

| Concept | atomic | mechanism_figurable | outcome |
|---------|--------|---------------------|---------|
| modular-arithmetic | true | true | leaf; drawn (unchanged) |
| best-effort-delivery | false | true | **non-leaf, now drawn** ← the fix |
| tcp-connection-lifecycle | false | true | **non-leaf, now drawn** |
| a broad umbrella field | false | false | caption-only (no figure) |

The decompose skill already reasons about both — it just collapsed them into `atomic`. `mechanism_figurable` makes the second axis explicit.

## Component changes

### 1. Decompose contract
- `references/decomposition-json.md`: document `mechanism_figurable` as a required top-level boolean; explain the two-axis distinction.
- `scripts/validate_decomposition.py`: require `mechanism_figurable` is present and a bool. (A non-atomic concept with `mechanism_figurable: false` is valid — a genuine umbrella; an atomic concept should normally be figurable, but the validator does not force it — judgment is the skill's, the validator only checks the type/presence.)
- decompose `SKILL.md`: a section on the two axes and how to judge `mechanism_figurable` ("does this concept's own mechanism fit one figure, *assuming* the prerequisites are understood elsewhere?").
- Golden examples: set the field — `rsa-encryption` (atomic false, **figurable true**), `modular-arithmetic` (atomic true, figurable true).

### 2. Illustrator contract (`concept-illustrator/SKILL.md`)
- **Self-sufficiency rule:** a figure must teach its concept on its own. It must not require the reader to have seen prerequisite figures; it may *name* a prerequisite in passing but illustrates this concept's own mechanism.
- **Commentary cross-references:** when the concept builds on fundamentals that have their own figures, the commentary includes optional pointers ("for the clock-math underneath this, see the modular-arithmetic figure") — referencing, not re-teaching. Reader-facing pointers remain the explainer's "Builds on:" links; the commentary pointers serve the narration/transcript layer.
- **Retire `compose-from-children`:** remove the "Composition figures" section. It was a Phase-4 workaround the chain reviews proved wrong; self-sufficient mechanism figures replace it. Its contract test is replaced by a self-sufficiency-rule test.

### 3. Workflow (`.claude/workflows/dummies-notes.js`)
- Thread `mechanism_figurable` from each decomposition into `nodes`.
- **Illustrate filter:** `mechanism_figurable === true` (replacing `atomic === true`), still skipping already-`illustrated` covered concepts. This now includes a figurable root and figurable intermediates like `best-effort-delivery`.
- **Delete the Assemble compose step.** The root, when figurable, is illustrated as a normal mechanism figure during the Illustrate pass. A non-figurable root simply has no figure (caption-only) — there is no composition fallback.
- The illustrate prompt for a node with prerequisites instructs: make the figure self-sufficient for this concept; add commentary "go deeper" pointers to any prerequisite that is covered/illustrated.

### 4. graph_check (`scripts/graph_check.py`)
- `load_graph` reads `mechanism_figurable`.
- `--require-illustrated` requires a figure for every **figurable** node (not just atomic). Non-figurable nodes are exempt.

### 5. assemble.py
- No structural change — `build_explainer` already embeds whatever figure a node has. Tweak the "Figure pending" branch to key off `mechanism_figurable` instead of `atomic` (a figurable node missing its figure is the "pending" case; a non-figurable node is legitimately caption-only). "Builds on:" links are unchanged (they are the reader-facing references).

## Data flow (unchanged shape, one filter changed)

Decompose → Illustrate (**now: every figurable node**) → Review → Finalize → Assemble (**no compose step**) → ChainReview. The chain review is the acceptance signal: a self-sufficient figure for each figurable concept should close the "broken arc / unmet prerequisite / leap" gaps the RSA and TCP runs surfaced.

## Acceptance — close the TCP loop

Re-running an already-illustrated topic is complicated by the deferred **figure-invalidation** question: the workflow skips concepts whose registry status is already `illustrated`, so it would keep the stale composition figure for the TCP root. Acceptance therefore performs a **one-time manual reset** of exactly the two stale entries:

- Delete `registry/tcp-connection-lifecycle/figure/` and `registry/best-effort-delivery/figure/` (if present) and reset those entries to `registered` (or delete the entries so the run re-registers them).
- **Keep** `communication-protocol` and `data-packets` illustrated — they prove reuse (covered-link-stop) and stay untouched.

Then re-run `dummies-notes {topic: "TCP connection lifecycle", maxDepth: 2}`. Expected:
- `best-effort-delivery` (figurable) gets the "unreliable mail" mechanism figure (loss / duplication / late / shuffled).
- `tcp-connection-lifecycle` (figurable) gets a **self-sufficient** lifecycle figure (handshake → data + confirmation → two-sided goodbye), with commentary pointing at packets / protocol / best-effort for depth.
- `communication-protocol` and `data-packets` are linked, not redrawn.
- The chain review's first three gaps (broken arc, unmet prerequisite, handshake leap) close; any residual gap is documented honestly.

The manual reset is an explicit stand-in for proper figure invalidation, which remains the one deferred open question.

## Non-goals (YAGNI)

- **No figure invalidation/versioning.** Still deferred; the acceptance reset is a manual stand-in.
- **No multiple figures per concept.** One self-sufficient figure per concept; the registry model is unchanged.
- **No re-illustration of RSA in this phase.** TCP is the acceptance case; RSA can be reset and re-run later the same way if desired.
- **No new illustrator archetype.** A mechanism figure is a normal `concept-illustrator` figure of the concept; no new drawing mode is added (compose-from-children is removed, not replaced).

## Open question (carried forward)

- **Figure invalidation/versioning:** when a concept's definition (or understanding) changes, or when the system gains the ability to draw a previously-undrawn node, how does it detect a stale/missing figure and re-illustrate without a manual reset? Phase 5 makes this more pressing (re-running a topic to pick up the new figurable behavior currently needs the manual reset) but does not solve it.
