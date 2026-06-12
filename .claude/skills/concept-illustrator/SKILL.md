---
name: concept-illustrator
description: >-
  Turn a concept, narrative, algorithm, process, or system into a clean, elegant,
  self-contained SVG illustration in a minimal flat editorial style — the kind of
  figure that explains an idea better than a paragraph. Use this whenever the user
  wants to *visualize* or *illustrate* an idea rather than just describe it: explaining
  how something works (binary search, attention, TCP, gradient descent, the call stack,
  a Krebs cycle), drawing a process or workflow, diagramming an architecture or data
  structure, or making teaching figures for computer science, math, or physics. Trigger
  on phrases like "illustrate", "diagram", "draw", "visualize", "show me how X works",
  "make a figure/graphic for", "explain visually", or any request to convert text or a
  narrative into a picture — even when the user doesn't say the word "SVG". Produces
  a figure directory (figure.json + SVG frames) that renders correctly in light and dark
  mode and exports cleanly to PNG for slides, blogs, and video.
---

# Concept illustrator

Convert an idea into a clean SVG figure. The output is deliberately restrained:
a small palette, two type sizes, thin strokes, sentence case, lots of whitespace.
The elegance comes from constraint and from choosing the *right kind* of figure —
not from decoration.

Every figure is a **figure directory**: a `figure.json` manifest plus one or more
`frame-NN.svg` files with per-frame captions. Single static figures have exactly one
frame; animated sequences have many. The format is described in `references/figure-json.md`.

Everything produced is **self-contained**: the stylesheet and arrow marker are baked
into each frame SVG, so it renders correctly opened directly in a browser, embedded in
a blog, dropped in a slide, or rasterized to PNG. Light and dark mode are both handled
automatically via an embedded media query.

## Workflow

Follow these steps in order. The routing and storyboard decisions are where most figures
succeed or fail — don't rush past them.

1. **Read the concept and pick ONE archetype.** Decide *what kind* of figure the idea
   wants before drawing anything. Use the routing table below. When unsure, read
   `references/archetypes.md` — it has a worked example of each.

2. **Storyboard: static or sequence?** Decide whether the concept needs multiple frames.
   A single illustrative frame is right for most concepts; prefer static unless the idea
   is genuinely about *change over time* (sorting steps, recursion unwinding, a network
   handshake). If a sequence: plan every frame now. Write down the stable layout —
   element positions, box sizes, labels — that all frames will share. Only highlights,
   color classes, and pointer positions will move between frames. This is the
   **frame-consistency rule**: shared `viewBox`, stable coordinates, moving highlights.

   **End with the result.** A process/sequence figure must close with a frame showing
   the end state. For recursive or iterative algorithms, a final fast-forward frame is
   fine: collapse the remaining iterations and show the finished result, so the reader
   sees the mechanism AND that it worked.

   For each frame — including a single static frame — work in this order:
   1. Write the **runbook** (what/why/how this frame is drawn, honoring the
      frame-consistency rule). The runbook is the build-spec for the frame: it captures
      the archetype layout, box positions and coordinates (plan them here, before any
      SVG — `width ≥ max(title_chars × 8, subtitle_chars × 7) + 24` for each box),
      colour roles, and what changes from the previous frame. The runbook is persisted
      in `figure.json` and is human-editable for re-runs; it is the ground truth a
      fidelity review diffs the rendered SVG against.
   2. Draw the **SVG** from the runbook.
   3. Write the **caption** (terse subtitle shown in the HTML viewer) and the
      **commentary** (short narration paragraph for slides/video, per the
      `## Commentary` section of `references/voice-and-metaphor.md`).

   > **Coordinate planning** is done when you write the runbook (above), before
   > emitting SVG — see the box-width rule in step 1 and in "Core rules" below.
   > Coordinate mistakes are the most common layout failure mode.

3. **Start from the template.** Use `assets/template.svg` as the starting point for each frame file. It already
   contains the embedded stylesheet, the arrow marker, and the `cd-svg` wrapper class.
   Fill in `<title>`, `<desc>`, the `viewBox` height, and the content. Never hand-write
   the `<style>` block — it lives in the template and in `assets/_style.css`.

4. **Use the design system.** Colors, classes, and type rules are in
   `references/design-system.md`. The short version is in "Core rules" below.
   Voice and metaphor guidance is in `references/voice-and-metaphor.md`;
   vocabulary for common primitives (cells, pointers, graph nodes) is in
   `references/visual-vocabulary.md`.

5. **Validate before delivering.** Run the linter — it is dependency-free and catches
   clipped content, labels past the edge, unclassed text, and frame-consistency errors.
   ```
   # one frame
   python3 scripts/render.py path/to/frame.svg
   # whole figure directory
   python3 scripts/render.py path/to/figure-dir
   # whole figure + build the slideshow viewer
   python3 scripts/render.py path/to/figure-dir --viewer path/to/figure.html
   ```
   Fix every ERROR and review every WARN. A clean lint is required before handing the
   figure to the user.

6. **Review.** Run the protocol in `references/review-protocol.md`: blind-reader test
   (give only the rendered figure to a fresh reader, check comprehension) and fidelity
   critic (give concept definition + figure, check correctness). The automated review
   loop arrives in Phase 3; during development, run both checks manually or as a
   subagent. A figure with a comprehension gap gets regenerated with the critique as a
   constraint — captions are context, not a crutch.

7. **Export PNG only if asked.** For slides or video:
   ```
   python3 scripts/render.py path/to/frame.svg --png out.png --theme light --scale 2
   ```
   PNG export currently rasterizes the document's default (light) rendering; the `--theme`
   flag is reserved — forced dark-theme rasterization is a future enhancement (static
   rasterizers don't evaluate the dark-mode media query). Needs `cairosvg` or `rsvg-convert`.

8. **Deliver the figure directory**, not pasted SVG source. The directory contains
   `figure.json` and `frame-NN.svg` files; include the generated `figure.html` viewer
   when the figure has multiple frames.

## Routing: which figure does the idea want?

Route on the **verb**, not the noun. The same subject becomes a different figure
depending on whether the user wants to *document* it or *understand* it.

| The idea is about… | Archetype | What you draw |
|---|---|---|
| Steps in sequence, a decision branching, a pipeline | **Flowchart** | Boxes connected by arrows, one flow direction |
| Things contained in other things; architecture; where data lives | **Structural** | Nested rounded rectangles, regions inside regions |
| Building *intuition* — "how does X actually work", a mechanism, a metaphor | **Illustrative** | A spatial metaphor where position and color carry the meaning |
| Quantities, distributions, "compare these numbers" | **Chart** | A chart drawn in SVG — see `references/archetypes.md` |
| A process or trace that evolves step by step (sorting, recursion, a handshake) | **Sequence** | Multiple frames of the *same* visual archetype (usually illustrative) — set `playback: "slideshow"`; `archetype` stays the visual kind. Shared layout, moving highlights only. |
| A database schema / entity relationships | **ERD (mermaid)** | Produces a mermaid `erDiagram` (markup, not SVG frames) — outside this skill's figure.json/SVG output. Use only when a precise entity-relationship reference is needed. |

Decision heuristics:
- "Walk me through…" / "what are the steps" → flowchart.
- "What's inside…" / "how is it organized" / "the architecture" → structural.
- "How does X *work*" / "I don't get X" / "give me intuition for X" → **illustrative**.
  This is the default for an unqualified "explain X", and it is the most valuable and most
  underused. Don't retreat to a flowchart because it feels safer. A transformer's attention
  is a fan of weighted lines, not three labeled boxes; recursion is a stack growing and
  unwinding; a hash map is keys falling into buckets. Invent the spatial metaphor that makes
  the mechanism *visible*.
- "Show me step by step" / "trace the algorithm" / "animate this process" → **sequence**.
  Default to a single illustrative frame; escalate to sequence only when the concept is
  genuinely about change over time. If a single frame captures the idea, set `playback: "static"` — the sequence treatment does not require multiple frames.

Don't mix archetypes in one figure. If the idea needs both intuition and a precise
reference, make two figures (intuition first), each a separate directory.

## Progressive reveal

When a scene **builds up additively** — one new element appears at each step and
everything prior stays on screen — use progressive reveal instead of separate
frames. This keeps the layout stable (one `viewBox`, one figure inline in the
HTML player) while walking the reader through the sequence beat by beat.

**How to author:**

1. Identify the elements that enter in explanation order (backdrop first, then
   progressively-introduced groups).
2. Leave the always-visible backdrop untagged. Wrap each progressively-introduced
   element in `<g data-reveal="k" data-anim="…">` where `k` starts at 1 and
   increments by 1 per step (gap-free).
   - Shapes and boxes → `data-anim="rise"` (the default; lifts in from below).
   - `<line>` elements and arrows → `data-anim="draw"` (path stroked in; use this
     for any directed edge to show flow visually).
   - Cross-fade → `data-anim="fade"`.
3. Write exactly one short, plain-language **narration beat** per step into the
   `beats` array in `figure.json`, in the same order as the `data-reveal` indices.
   Each beat has a `caption` (terse viewer subtitle) and a `narration` (one or two
   spoken sentences — human, plain, no jargon).
4. `len(beats)` must equal `max(data-reveal)` — the validator (`render.py`) flags
   any mismatch as an ERROR.

**State mutation** between major scene shifts stays across frames as usual — use
separate frames when the scene *changes* rather than *grows*. Progressive reveal
is for additive build-up within one scene; cross-frame changes are for before/after
states.

**Protocol acronyms in labels** (SYN, ACK, FIN, TCP, UDP, …) are allowed. The
caps lint checks an acronym allowlist and exempts known technical tokens, so
protocol-accurate uppercase labels will pass without error.

See `examples/tcp-handshake-reveal` for the canonical worked example (6 beats:
two box rises, three arrow draws, one badge rise — all in one frame).

## Output contract

The output is a **figure directory** containing:

- `figure.json` — manifest (see `references/figure-json.md`): `concept_slug`, `archetype`,
  `playback` (`static` or `slideshow`), and an ordered `frames` array where each entry
  has `file`, `caption`, `runbook`, and `commentary` (all required). `caption` is the
  only text shown in the HTML viewer; `commentary` is narration for slides/video and is
  not rendered in the viewer. In `figure.json`, `archetype` is one of the four visual
  kinds — `illustrative`, `flowchart`, `structural`, `chart`. A multi-frame figure is
  NOT a separate archetype: keep `archetype` as the visual kind (usually `illustrative`)
  and set `playback: "slideshow"`.
- `frame-01.svg`, `frame-02.svg`, … — one SVG per frame, each a complete standalone file
  built from `assets/template.svg`.

For a static figure, `playback` is `"static"` and `frames` has exactly one entry.
For a sequence, `playback` is `"slideshow"` and every frame shares the same `viewBox`.

Machine-callable interface: input = concept slug + concept name + definition;
output = a figure directory at the path of your choice.

## Self-sufficient figures

Every figure must teach its own concept STANDALONE. A reader who lands on this
figure cold — without having seen any prerequisite's figure — should still grasp
the concept's mechanism. Illustrate THIS concept's own mechanism; you may name a
prerequisite in passing, but never require the reader to have studied it.

A concept with prerequisites is illustrated the same way as a leaf — the only
difference is the **commentary**: when the concept builds on fundamentals that
have their own figures, add a short "go deeper" pointer in the commentary, e.g.
"for the clock-math underneath this, see the modular-arithmetic figure." It is a
reference, not a dependency — the figure stands on its own; the pointer is for the
curious. (Reader-facing prerequisite links live in the assembled explainer's
"Builds on" list; these commentary pointers serve the narration/transcript.)

## Core rules (the look)

Full detail in `references/design-system.md`; this is the load-bearing subset.

- **Canvas.** `viewBox="0 0 680 H"`. Width 680 is fixed (center narrow content rather
  than shrinking the viewBox). Set `H` to the bottom of the lowest element + ~40px.
- **Three type classes only.** `class="th"` (14px medium) for titles; `class="t"` (14px)
  for body labels; `class="ts"` (12px) for subtitles and captions. No inline `font-size`.
- **Sentence case everywhere.** Never Title Case, never ALL CAPS — including labels.
  The linter rejects violations.
- **Color encodes category, not sequence.** Assign one ramp per semantic role and hold it
  for the life of the figure. In illustrative and sequence figures: teal = active/under
  consideration, gray = eliminated/inactive, coral = target/goal. In structural and
  flowchart figures: use ramps for pure category (purple, blue, pink for neutral roles).
  Available ramps: `c-purple`, `c-teal`, `c-coral`, `c-pink`, `c-gray`, `c-blue`,
  `c-green`, `c-amber`, `c-red`. Apply by placing the class on a `<g>` or shape.
- **Thin strokes.** `stroke-width="0.5"` on box borders.
- **Box width from the longest label.** `width ≥ max(title_chars × 8, subtitle_chars × 7) + 24`.
  Undersized boxes are the most common layout failure.
- **Arrows.** Use `class="arr" marker-end="url(#arrow)"` (marker is in the template).
  Arrow paths must set `fill="none"`. Route around unrelated boxes; never cross a label.
- **Every `<text>` needs a class** (`t`/`ts`/`th`). Unclassed text is flagged by the linter.
- **No gradients, shadows, glows, or emoji.** One `<linearGradient>` is allowed only in
  an illustrative figure to show a continuous physical property.

## Files in this skill

- `assets/template.svg` — start here. Self-contained SVG with embedded style + arrow marker.
- `assets/_style.css` — source of truth for the embedded stylesheet (palette, classes,
  light and dark). Already inlined in the template; here for reference and regeneration.
- `assets/slideshow.template.html` — HTML template used by `scripts/render.py` (with
  the `--viewer` flag) to produce a browsable slideshow from a figure directory.
- `references/design-system.md` — full palette table, class reference, type-width table,
  standalone-vs-inline notes, dark-mode mechanics.
- `references/archetypes.md` — detailed how-to and a worked example for each archetype,
  including the Sequence frame-consistency rule.
- `references/visual-vocabulary.md` — reusable primitives: array cells, pointers, graph
  nodes, state styles.
- `references/voice-and-metaphor.md` — tone guidelines and a bank of proven spatial
  metaphors.
- `references/review-protocol.md` — blind-reader test and fidelity critic procedures;
  repair loop with bounded retries.
- `references/figure-json.md` — full schema for `figure.json` with an annotated example.
- `scripts/render.py` — dependency-free linter, figure validator, viewer generator,
  and optional PNG exporter.

## Quality bar

A good figure works with the labels removed — the *layout* already carries the meaning.
Before delivering, verify: the figure passes `python3 scripts/render.py` clean, it reads
at a glance, color is used for category or state (not decoration), and it makes sense in
dark mode. If the blind-reader test produces a comprehension gap, fix the figure — do not
compensate with a longer caption.
