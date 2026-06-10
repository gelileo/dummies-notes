# Review protocol

Every figure goes through fresh-eyes review before entering the registry. The
generator knows what it meant; the reviewer does not — that asymmetry is the point.
The automated loop lives in Phase 3 of the Workflow. This document describes the
same procedure as a manual or subagent process for use during development.

---

## Blind-reader test

**Purpose:** check comprehension — does the figure carry the concept on its own?

**Procedure:**
1. Render the figure to PNG (or export the SVG frames as a slideshow).
2. Give a fresh agent — or a colleague who has not seen the storyboard — **only the
   rendered figure and its caption**. Do not share the concept definition, the
   storyboard plan, or any generation notes. The blind-reader sees ONLY the rendered
   figure (and at most the terse caption) — never the runbook or commentary; its read
   is compared against the `commentary`'s intent, and divergence is a comprehension
   gap.
3. Ask: "What does this teach? What is the mechanism it is showing? What is
   confusing or unclear?"
4. Compare the agent's answer to the **intended concept**. If the agent describes a
   different mechanism, identifies the wrong goal, or cannot state the key insight,
   that is a **comprehension gap**.

**Comprehension gap → repair:** the figure failed to convey the idea without
surrounding context. Regenerate with the critique as a constraint — the critique
identifies what was ambiguous, missing, or misleading. Do not explain the gap away
by adding a caption paragraph; fix the figure so the image works alone.

---

## Fidelity critic

**Purpose:** check correctness — is anything wrong, misleading, or silently assumed?

**Procedure:**
1. Give a fresh agent the **concept definition** and the **figure** (rendered PNG or
   SVG frames + caption).
2. Ask: "What is wrong, misleading, or silently assumed in this figure? What would
   confuse or misinform a reader who takes it at face value? Are there missing
   prerequisites — terms or mechanisms the figure uses but does not explain?"
3. Collect the verdict: a list of specific claims or visual choices that are
   incorrect, imprecise, or assume knowledge the target reader may not have.

**Fidelity gap → repair:** incorrect claims are fixed directly in the figure.
A silently assumed prerequisite (a term or mechanism the figure uses but never
explains) is flagged as a **missing prerequisite node** — return it to
`concept-decompose` to add the node to the graph, rather than patching the caption.

### Commentary quality

Check that the frame's `commentary` is accessible, vibrant, uses simple sentences,
and is faithful to the frame's visual content. Flag run-on or compound-complex
sentences — commentary that requires several re-reads to parse will not survive the
blind-reader test.

---

## Repair loop

**Bounded retries — exactly two:**

1. **Figure-level gap** (comprehension or fidelity issue that the figure itself can
   fix): regenerate the figure with the critique as a constraint; re-run both blind-
   reader and fidelity critic on the new version. This counts as retry 1.

2. **If the revised figure still fails:** regenerate once more with both the original
   and retry-1 critiques. This is retry 2.

3. **Missing-prerequisite gap** (the critic identifies a concept the figure assumes
   but the graph has not illustrated): return to `concept-decompose` to add the
   prerequisite as a new node. The prerequisite node itself goes through the full
   illustrate → review cycle. The original figure is then revised to reference it
   rather than assume it. This repair counts against the same retry budget.

4. **If unresolved after exactly two retries:** register the figure with a
   `flagged: true` field in `figure.json` and log the outstanding gap. Do not block
   the pipeline on a figure that is close enough — ship flagged rather than silently
   wrong, and surface the gap report alongside the output. A flagged figure is
   better than no figure; it is not better than a passing figure. After two failed retries, register the figure **flagged** and log the gap (or escalate to a human) — do not keep retrying.

**What does not count as repair:** adding a long explanatory caption to compensate
for a figure that does not work visually. Captions are context, not a crutch. If the
image alone fails the blind-reader test, fix the image.

---

## Runbook drift

Each frame's `runbook` (in `figure.json`) is the ground truth of intent. The
fidelity critic diffs the rendered SVG against its runbook: cell count, colour
roles, pointer positions, what changed from the previous frame. A mismatch is
drift. Two repair branches:

- **SVG is wrong** → regenerate that frame from its runbook.
- **Runbook is wrong or outdated** (the concept changed) → fix the runbook, then
  re-run; regeneration redraws from it.
