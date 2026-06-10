# concept-illustrator: runbook + commentary — design (Phase 1.5)

- **Date:** 2026-06-09
- **Status:** approved (design); to be planned next
- **Scope:** a focused enhancement to the already-shipped `concept-illustrator` skill (`.claude/skills/concept-illustrator/`). One implementation plan.
- **Parent spec:** `docs/superpowers/specs/2026-06-09-dummies-notes-design.md`

## Goal

Each figure should carry, per frame, two new text artifacts beyond the in-SVG
annotation and the viewer caption:

- a **runbook** — the build-spec for the frame (what/why/how it is drawn). It
  drives generation, is the ground truth for drift review, and stays editable so a
  human can adjust it and re-run.
- a **commentary** — rich, accessible narration tied to the frame, for keynote
  slides and YouTube/video transcripts.

Both also strengthen the end-of-workflow self-review.

## Text-layer model

Four per-frame text layers, each with one job:

| Layer | Where it lives | Role | Shown in viewer? |
|---|---|---|---|
| annotation | inside the SVG | terse spatial labels on the drawing | n/a (it's the drawing) |
| caption | `figure.json` `frames[].caption` | short subtitle under the frame | yes (unchanged) |
| runbook | `figure.json` `frames[].runbook` | build-spec: what/why/how the frame is drawn | no |
| commentary | `figure.json` `frames[].commentary` | rich narration for slides/video | no |

The figure's existing `title` carries the figure-level intent; no new top-level
field is added.

## figure.json schema change

`frames[]` gains two **required, non-empty string** fields, `runbook` and
`commentary`, alongside `file` and `caption`:

```json
{
  "file": "frame-02.svg",
  "caption": "Scan left; smaller values move into the left zone.",
  "runbook": "6 cells fixed at x=100..450. Pivot 3 is coral at index 5. Scan pointer j (c-teal) at index 3 (value 1). Value 2 settled gray at index 0. Pointer i at index 1. No swap arrow this frame.",
  "commentary": "Now the real work starts. We walk left to right. The pivot is our yardstick. Every value smaller than it slides into a growing zone on the left. It is like flipping through a stack of mail and dropping each small bill into one pile."
}
```

`caption`, `runbook`, and `commentary` are three different texts and need not match
each other or the in-SVG annotation.

## Generation workflow (runbook-first)

The existing storyboard step *becomes* the runbook. Per frame, in this order:

1. **Write the runbook** — plan the frame: which primitives, fixed coordinates,
   colour roles, what changed from the previous frame, honoring the
   frame-consistency rule.
2. **Draw the SVG** from the runbook.
3. **Write the caption** (terse subtitle) and the **commentary** (narration).

The runbook is persisted in `figure.json`, so it is both the plan and the build
record. A human reviewer can edit a frame's runbook and re-run generation to
redraw that frame from the edited spec.

## Commentary voice

Commentary follows `references/voice-and-metaphor.md`, but is longer-form than the
one-line caption (a short narration paragraph). Rules:

- **Prefer simple sentences.** One idea per sentence. Avoid nested clauses and
  compound-complex constructions. Short sentences, plain words.
- Vibrant and engaging through **vivid metaphor and rhythm**, not through long
  sentences.
- Accessible: no unexplained jargon (an obscure term is a prerequisite, not an
  aside).
- Faithful to what the frame actually shows.
- Transcript-ready: reads naturally aloud for narration.

## Review reconciliation

Two reconciliations at the end of the workflow, each with its own reference text.
(The automated agent loop is Phase 3; Phase 1.5 documents this in
`references/review-protocol.md` for manual/subagent use.)

1. **Fidelity critic — runbook ↔ SVG (drift).** Diff each rendered frame against
   its runbook. A mismatch is drift. Two repair branches:
   - *SVG is wrong* → regenerate that frame from its runbook.
   - *Runbook is wrong or outdated* (e.g. a human changed the concept) → fix the
     runbook, then re-run.
   The runbook is the ground truth of intent, so "drift" is a concrete diff (cell
   count, colour roles, pointer positions) rather than a guess.
2. **Blind-reader — picture ↔ intent (comprehension).** The blind-reader **stays
   blind**: it sees only the rendered figure (and at most the terse caption), never
   the runbook or commentary. Its "what this teaches" is compared against the
   commentary's intent. Divergence = a comprehension gap the drawing did not close.
3. **Commentary quality pass.** Check the commentary is accessible, vibrant, uses
   simple sentences, and is faithful to the frame. Flag run-on or
   compound-complex sentences.

## Implementation surface

- `references/figure-json.md` — document the two new required fields and the
  runbook-first role.
- `scripts/render.py` `validate_figure` — require non-empty `runbook` and
  `commentary` for every frame; report an ERROR when either is missing or blank.
  Add unit tests (valid figure passes; missing/blank runbook or commentary errors).
- `SKILL.md` — update the workflow to runbook-first storyboard, then write caption
  + commentary; update the output-contract description to list the new fields.
- `references/voice-and-metaphor.md` — add the commentary guidance (longer-form,
  simple sentences, transcript-ready).
- `references/review-protocol.md` — add the runbook↔SVG drift reconciliation;
  clarify the blind-reader stays blind; add the commentary comparison + quality
  pass.
- `examples/quicksort/figure.json` — regenerate with `runbook` + `commentary` for
  all four frames (the golden example must satisfy the new contract).
- Knowledge: update `knowledge/concepts/dummies-notes/illustration-engine.md`
  (figure.json contract now includes runbook + commentary; the review model) and
  append a `knowledge/log.md` entry.

## Non-goals (YAGNI)

- **No `commentary.md` / transcript export yet.** Storage is `figure.json` fields
  only; a markdown/transcript exporter can be added later if needed.
- **No viewer change.** The HTML viewer still shows only the caption; commentary is
  not displayed.
- **No automated review agents in this change.** The runbook-drift and comprehension
  reconciliations are documented for manual/subagent use; the autonomous loop lands
  in Phase 3 (the `dummies-notes` Workflow).
- **No figure-level runbook/commentary field.** `title` covers figure-level intent.

## Open questions (resolve during planning, not blocking)

- Whether `validate_figure` should also warn when `commentary` is suspiciously
  short (e.g. < N characters) or identical to `caption` — or leave length/quality
  entirely to the review pass.
