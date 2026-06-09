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
  standalone .svg files that render correctly on their own (light and dark mode) and
  export cleanly to PNG for slides, blogs, and video.
---

# Concept illustrator

Convert an idea into a clean SVG figure. The output is deliberately restrained:
a small palette, two type sizes, thin strokes, sentence case, lots of whitespace.
The elegance comes from constraint and from choosing the *right kind* of figure —
not from decoration.

Everything produced is **self-contained**: the stylesheet and arrow marker are baked
into each SVG, so it renders correctly opened directly in a browser, embedded in a
blog, dropped in a slide, or rasterized to PNG. There is no dependency on any host
theme. Light and dark mode are both handled automatically via an embedded media query.

## Workflow

Follow these steps in order. Don't skip the routing decision — it's where most figures
succeed or fail.

1. **Read the concept and pick ONE archetype.** Decide *what kind* of figure the idea
   wants before drawing anything. Use the routing table below. When unsure, read
   `references/archetypes.md` — it has a worked example of each.

2. **Plan coordinates on paper first.** Before emitting any SVG, decide box positions,
   widths (from the longest label — see the width rule below), and the canvas height.
   Diagrams fail almost entirely from coordinate mistakes, not from style.

3. **Start from the template.** Copy `assets/template.svg` to your output path. It already
   contains the embedded stylesheet, the arrow marker, and the `cd-svg` wrapper class.
   Fill in `<title>`, `<desc>`, the `viewBox` height, and the content. Never hand-write
   the `<style>` block — it lives in the template and in `assets/_style.css`.

4. **Use the design system.** Colors, classes, and type rules are in
   `references/design-system.md`. The short version is in "Core rules" below.

5. **Validate before delivering.** Run the linter — it is dependency-free and catches
   clipped content, labels past the edge, unclassed text, and leftover placeholders:
   ```
   python3 scripts/render.py <your-file>.svg
   ```
   Fix every ERROR and review every warning. A clean lint is required before handing the
   figure to the user.

6. **Export PNG only if asked.** For slides/video the user may want a raster:
   ```
   python3 scripts/render.py figure.svg --png figure.png --theme light --scale 2
   ```
   (`--theme dark` forces the dark palette; static rasterizers don't evaluate the media
   query, so the theme must be chosen at export time. Needs `cairosvg` or `rsvg-convert`.)

7. **Deliver the .svg file**, not pasted SVG source. If the user is writing for the web,
   inline SVG keeps the dark-mode media query live; an `<img>` tag or PNG freezes one theme.

## Routing: which figure does the idea want?

Route on the **verb**, not the noun. The same subject becomes a different figure
depending on whether the user wants to *document* it or *understand* it.

| The idea is about… | Archetype | What you draw |
|---|---|---|
| Steps in sequence, a decision branching, a pipeline | **Flowchart** | Boxes connected by arrows, one flow direction |
| Things contained in other things; architecture; where data lives | **Structural** | Nested rounded rectangles, regions inside regions |
| Building *intuition* — "how does X actually work", a mechanism, a metaphor | **Illustrative** | A drawing of the mechanism: a spatial metaphor where position and color carry the meaning |
| Quantities, distributions, "compare these numbers" | **Chart** | A chart. See `references/archetypes.md` |
| A database schema / entity relationships | **ERD (mermaid)** | mermaid `erDiagram`, not hand-placed SVG |

Decision heuristics:
- "Walk me through…" / "what are the steps" → flowchart.
- "What's inside…" / "how is it organized" / "the architecture" → structural.
- "How does X *work*" / "I don't get X" / "give me intuition for X" → **illustrative**.
  This is the default for an unqualified "explain X", and it's the most valuable and most
  underused. Don't retreat to a flowchart because it feels safer. A transformer's attention
  is a fan of weighted lines, not three labeled boxes; recursion is a stack growing and
  unwinding; a hash map is keys falling into buckets. Invent the spatial metaphor that makes
  the mechanism *visible*.

Don't mix archetypes in one figure. If the idea needs both intuition and a precise
reference, make two figures (intuition first), each a separate file.

## Core rules (the look)

These are the rules that produce the clean aesthetic. Full detail in
`references/design-system.md`; this is the load-bearing subset.

- **Canvas.** `viewBox="0 0 680 H"`. Keep width 680 (it's calibrated so 1 SVG unit = 1px;
  center narrow content rather than shrinking the viewBox). Set `H` to the bottom of the
  lowest element + ~40px — no large empty margin, no clipping.
- **Two type sizes only.** `class="th"` (14px medium) for titles, `class="t"` (14px) for
  body labels, `class="ts"` (12px) for subtitles and captions. Never any other size.
- **Sentence case everywhere.** Never Title Case, never ALL CAPS — including labels.
- **Color encodes meaning, not sequence.** Pick 2–3 ramps and assign one per *category*
  (all consumers teal, all sources coral, structure gray). Don't rainbow through colors
  step by step. Apply a ramp by putting `class="c-teal"` (etc.) on a `<g>` or directly on a
  shape; child text recolors automatically. Available: c-purple, c-teal, c-coral, c-pink,
  c-gray, c-blue, c-green, c-amber, c-red. Prefer purple/teal/coral/pink for neutral
  categories; reserve blue/green/amber/red for genuinely informational/success/warning/error
  meaning (in illustrative figures they may map to physical properties like heat).
- **Thin strokes.** `stroke-width="0.5"` on box borders. Refined, not heavy.
- **Box width comes from the longest label.** `width ≥ max(title_chars × 8, subtitle_chars × 7) + 24`.
  A 100px box holds a ~10-char subtitle. Undersized boxes overflow — the most common failure.
- **Arrows.** Use `class="arr" marker-end="url(#arrow)"` (marker is in the template). An arrow
  must never cross an unrelated box or a label — route around with an L-bend `<path>` if needed.
- **Every `<text>` needs a class** (`t`/`ts`/`th`). An unclassed text element is the tell that
  the class was forgotten; the linter flags it.
- **Connector paths need `fill="none"`** or they render as filled blobs.
- **Center text in boxes** with `text-anchor="middle"` and `dominant-baseline="central"`,
  with `y` at the vertical center of the slot (not the box) it sits in.
- **No gradients, shadows, glows, or emoji.** One `<linearGradient>` is allowed *only* in an
  illustrative figure to show a continuous physical property (a temperature gradient in a tank).

## Files in this skill

- `assets/template.svg` — start here. Self-contained SVG with embedded style + arrow marker.
- `assets/_style.css` — the source of truth for the embedded stylesheet (palette + classes,
  light and dark). Already inlined in the template; here for reference/regeneration.
- `references/design-system.md` — full palette table, class reference, type-width table,
  standalone-vs-inline notes, dark-mode mechanics.
- `references/archetypes.md` — detailed how-to and a worked example for each archetype.
- `references/example-binary-search.svg` — a finished, lint-clean illustrative example.
- `scripts/render.py` — dependency-free linter; optional PNG export.

## Quality bar

A good figure works with the labels removed — the *layout* already carries the meaning.
Before delivering, check: does the figure pass the linter clean, does it read at a glance,
is color used for category (not decoration), and would it still make sense in dark mode?
