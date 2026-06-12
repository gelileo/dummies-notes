# Visual vocabulary

Copy-paste primitives for recurring shapes. This is the **only place literal SVG
reuse lives** — copy a primitive into your figure, don't import a whole figure.
Every snippet below is classed with palette classes only, uses no inline colors,
and is lint-clean. Adjust `x`, `y`, `width`, and text content; keep the classes.

---

## List / array cell

Use for: a single slot in an array, list, or sequence; combine in a row for the full
structure.

```xml
<!-- Single array cell at (x=20, y=40), width=60, height=36 -->
<g class="box">
  <rect x="20" y="40" width="60" height="36" rx="2" stroke-width="0.5"/>
  <text x="50" y="58" class="th" text-anchor="middle" dominant-baseline="central">7</text>
</g>
```

Highlight states: replace `class="box"` with `class="c-teal"` (under consideration),
`class="c-gray"` (eliminated), or `class="c-coral"` (target/found). The child `<text>`
recolors automatically.

---

## Pointer

Use for: an arrow pointing down at a cell or node to label a position (e.g., "mid",
"pivot", "head"). The arrowhead comes from the template's `#arrow` marker.

```xml
<!-- Pointer arrow pointing down to y=40 from y=16, centered at x=110 -->
<path class="arr" d="M110,16 L110,36" marker-end="url(#arrow)"/>
<text x="110" y="10" class="ts" text-anchor="middle" dominant-baseline="central">mid</text>
```

For a horizontal pointer (left-to-right), rotate the path coordinates accordingly.
Never add `fill` to a pointer path — the `arr` class already sets `fill:none`.

---

## Graph node

Use for: a vertex in a graph, tree, or network. A circle with a centred label.

```xml
<!-- Graph node at centre (cx=100, cy=80), radius=20 -->
<g class="c-teal">
  <circle cx="100" cy="80" r="20" stroke-width="0.5"/>
  <text x="100" y="80" class="th" text-anchor="middle" dominant-baseline="central">A</text>
</g>
```

For the start/active node use `c-teal`; reserve `c-coral` for the goal/target node. For visited/done nodes use `c-gray`.
Radius 20–24 fits a two-character label comfortably at 14 px.

---

## Edge

Use for: a directed edge between two graph nodes or two boxes. Two variants:
straight arrow and dashed leader (no arrowhead, for annotation lines).

```xml
<!-- Directed edge from (120,80) to (180,80) -->
<path class="arr" d="M120,80 L176,80" marker-end="url(#arrow)"/>

<!-- Undirected / annotation leader -->
<path class="leader" d="M120,80 L180,80"/>
```

For an L-bend edge (routing around a box):
```xml
<path class="arr" d="M200,60 L200,100 L240,100" marker-end="url(#arrow)"/>
```

---

## Container / set

Use for: a region that groups related elements — a set boundary, a namespace, a
partition. A rounded rectangle with a label in the top-left corner.

```xml
<!-- Container box spanning (x=20,y=20) to width=300, height=120 -->
<g class="c-gray">
  <rect x="20" y="20" width="300" height="120" rx="6" stroke-width="0.5"/>
  <text x="32" y="38" class="ts" dominant-baseline="central">partition A</text>
</g>
```

Nest container primitives for containment hierarchies; outer container first in the
SVG source so inner elements render on top.

---

## Stack frame

Use for: one frame on a call stack — a flat rectangle with a function name on the
left and a return value or local variable label on the right.

```xml
<!-- Stack frame at (x=140, y=60), width=200, height=32 -->
<g class="box">
  <rect x="140" y="60" width="200" height="32" rx="2" stroke-width="0.5"/>
  <text x="156" y="76" class="th" dominant-baseline="central">factorial(3)</text>
  <text x="326" y="76" class="ts" text-anchor="end" dominant-baseline="central">n=3</text>
</g>
```

Stack frames are stacked vertically (each 32–40 px tall). The active/top frame gets
`class="c-teal"`; completed frames below it get `class="c-gray"`.

---

## Function box

Use for: a named operation in a flowchart or pipeline — a wider rectangle than an
array cell, with a title and optional subtitle.

```xml
<!-- Function box at (x=200, y=80), width=160, height=48 -->
<g class="box">
  <rect x="200" y="80" width="160" height="48" rx="4" stroke-width="0.5"/>
  <text x="280" y="98" class="th" text-anchor="middle" dominant-baseline="central">Merge sort</text>
  <text x="280" y="116" class="ts" text-anchor="middle" dominant-baseline="central">O(n log n)</text>
</g>
```

Width must satisfy `width ≥ max(title_chars × 8, subtitle_chars × 7) + 24`.
"Merge sort" (10 chars) needs `max(10×8, 11×7)+24 = max(80,77)+24 = 104 px` minimum;
160 px is comfortable.

---

## State styles

Use for: switching a node or cell between states in a sequence figure. Apply these
classes to the wrapping `<g>` — the shape fill and text ink update automatically.

| State | Class | Meaning |
|-------|-------|---------|
| Active / under consideration | `c-teal` | "Looking here right now" |
| Eliminated / visited / done | `c-gray` | "No longer in play" |
| Target / goal / found | `c-coral` | "This is the answer" |

```xml
<!-- Same cell, three states: copy the snippet, change only the class -->
<g class="c-teal"><!-- under consideration -->
  <rect x="20" y="40" width="60" height="36" rx="2" stroke-width="0.5"/>
  <text x="50" y="58" class="th" text-anchor="middle" dominant-baseline="central">7</text>
</g>

<g class="c-gray"><!-- eliminated -->
  <rect x="20" y="40" width="60" height="36" rx="2" stroke-width="0.5"/>
  <text x="50" y="58" class="th" text-anchor="middle" dominant-baseline="central">7</text>
</g>

<g class="c-coral"><!-- target/found -->
  <rect x="20" y="40" width="60" height="36" rx="2" stroke-width="0.5"/>
  <text x="50" y="58" class="th" text-anchor="middle" dominant-baseline="central">7</text>
</g>
```

In a sequence figure, the class is the only thing that changes between frames —
the coordinates stay identical (frame-consistency rule).

---

## Reveal order and entrance styles

When a scene builds up additively, wrap each progressively-introduced element in
`<g data-reveal="k" data-anim="…">` where `k` is a gap-free 1-based integer
giving the reveal step. Leave the always-visible backdrop untagged. Choose the
entrance animation by element type: `rise` (default) for boxes, labels, and
shapes that pop into view; `draw` for `<line>` elements and arrows so the stroke
animates in progressively; `fade` for cross-fades. Write one plain-language
`beats` entry in `figure.json` per reveal step — caption and narration — matching
the order of the `data-reveal` indices. The validator checks that
`len(beats) == max(data-reveal)`. See the `examples/tcp-handshake-reveal` figure
for a complete worked example (6 beats, two `rise` boxes, three `draw` arrows,
one `rise` badge).
