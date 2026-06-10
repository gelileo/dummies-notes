# Archetypes

Pick the archetype before drawing anything — it determines every layout decision.
Route on the **verb**, not the noun: what does the reader need to *do* with the figure?
One archetype per figure; if you need two, make two files.

---

## Flowchart

**When to use:** The concept is a sequence of decisions or steps: "walk me through the
algorithm", "what happens during a network request", "show the compilation pipeline".
The reader needs to follow a path, not build a mental model of a mechanism.

**How to draw:** Boxes connected by directional arrows, one dominant flow direction
(top-to-bottom or left-to-right). Decision diamonds have two outgoing edges labelled
"yes" and "no". All boxes share the same width. Arrows route around boxes, never
through them.

**Worked example — insertion sort one pass:**
Three states arranged top-to-bottom: "Pick next unsorted element" → diamond "Smaller
than predecessor?" → yes branch: "Swap left" (loops back to diamond) → no branch:
"Element in place" (advances to next). Each box `class="box"`, the condition diamond
is a `<polygon>`, edges are `class="arr"` paths.

**Avoid:** More than two branch directions from a single node; mixing narrative flow
with spatial metaphor in the same canvas.

---

## Structural

**When to use:** The concept is containment, architecture, or membership: "what's
inside a Linux process", "show the OSI stack", "how are namespaces organized in
Kubernetes". The reader needs to understand *what lives where*.

**How to draw:** Nested rounded rectangles, each region labelled. Outer region =
larger container; inner regions = components. Use `c-gray` or plain `box` for
scaffolding; apply a ramp only to components that carry distinct semantic roles.
Horizontal or vertical banding for layered architectures (OSI, kernel/user space).

**Worked example — a process's address space:**
A tall `viewBox="0 0 680 320"` rectangle representing the process. Inside, stacked
horizontal bands from top: "Stack" (`c-purple`), "Heap" (`c-blue`), "BSS / data"
(`c-gray`), "Text (code)" (`c-blue`). Each band is a `<rect class="box">` with a
`<text class="th">` label aligned left at `x="20"`. A vertical axis arrow on the
left labelled "high address" at top and "low address" at bottom.

**Avoid:** Overlapping regions (ambiguous containment); more than four nesting levels
(unreadable at any reasonable size).

---

## Illustrative

**When to use:** The reader needs *intuition* for a mechanism — "how does binary
search work", "I don't get recursion", "explain a hash map to me". This is the strong
default for any unqualified "explain X". Retreat to flowchart or structural only when
the concept genuinely is a process or containment.

**How to draw:** Invent a **spatial metaphor** where position and color carry the
meaning — make the mechanism *visible*. The archetype produces the most valuable and
most reused figures; it is also the most underused because flowchart feels safer. A
hash map is keys falling into labeled mailboxes, not three boxes labelled "key",
"hash", and "bucket".

**Spatial metaphor examples:** Binary search → a sorted row of cells with a shrinking
window; recursion → a stack of frames each holding a smaller sub-problem; a heap →
a pyramid where the largest item is always at the apex; gradient descent → a ball
rolling down a bowl toward the lowest point.

**Worked example — binary search midpoint check:**
A `viewBox="0 0 680 120"` canvas. Eight equal-width cells in a row, each `class="box"`,
labelled with sorted values. Cells outside the current window get `class="c-gray"` to
show "eliminated". The current midpoint cell gets `class="c-teal"` ("under
consideration"). The target cell gets `class="c-coral"` ("goal"). A down-pointing
`class="arr"` arrow from a label "mid" lands on the midpoint cell. The reader sees at
a glance: gray = out, teal = checking, coral = goal.

This is a slideshow figure: frame 1 shows the full array with mid at index 4; frame 2
shows the right half eliminated (gray) and mid moved to index 6; frame 3 shows the
target found (coral). The canvas size is identical across all three frames —
frame-consistency rule in action.

**Avoid:** Decorating the metaphor with gradients, drop-shadows, or color-steps-not-meaning.
The vividness comes from the metaphor, not the styling.

---

## Chart

**When to use:** The concept is a quantity, distribution, comparison, or trend: "how
does cache miss rate scale with working set size", "compare the growth rates of O(n)
vs O(n²)", "show the distribution of request latencies". The reader needs to see
*how big* or *how fast*.

**How to draw:** A proper chart — bar, line, scatter — drawn directly in SVG. Axes
with labelled ticks. A legend if two series are shown. Keep it minimal: no grid lines
(or one light horizontal reference), no fill under line charts unless area is
meaningful, no 3-D effects.

**Worked example — O(n) vs O(n²) growth comparison:**
A `viewBox="0 0 680 240"` canvas. X-axis labelled "Input size n", Y-axis labelled
"Operations". Two paths: a near-flat line (`c-teal`) labelled "O(n)" and a steeply
rising curve (`c-coral`) labelled "O(n²)". Axis lines are plain `class="box">rect`
borders; tick labels use `class="ts"`. A brief annotation at the crossover point:
"paths diverge fast".

**Avoid:** Pie charts (almost never the right encoding); rainbow color assignments
(two series = two colors, both chosen from the role conventions, not a rainbow);
chart junk (3-D bars, unnecessary gridlines, decorative fills).

---

## Sequence

**When to use:** The concept is a **process or trace** that evolves over time —
sorting an array step by step, a recursive call unwinding, a network handshake,
gradient descent iterations. The reader needs to see *change* frame by frame, not
just the end state. This is the multi-frame archetype.

**How to draw:** Design as a slideshow (multiple SVG frames, same `viewBox` across
all). Before drawing frame 1, plan the stable layout that every frame shares: element
positions, box sizes, labels. Only **highlights and pointers move** between frames;
the structural elements stay put. This is the **frame-consistency rule** — shared
canvas, stable positions, moving highlights. The figure reads as evolution, not
jump-cuts, and can be animated by the viewer.

**Worked example — quicksort partitioning:**
A row of eight cells with values to be sorted, `viewBox="0 0 680 140"` for all
frames. Frame 1: all cells `class="box"`, pivot cell (last element) highlighted
`class="c-coral"`, a label "pivot" above it. Frame 2: values less than pivot
shift left, those cells becoming `class="c-teal"` ("placed left of pivot"), others
remain `class="box"`. Frame 3: pivot swaps into its final position, turning
`class="c-coral"` with a "sorted position" annotation; cells on each side labelled
"< pivot" and "> pivot". The pivot cell's x-coordinate is the same in every frame —
it changes color but stays in place until the final swap.

**Frame-consistency rule (stated explicitly):** All frames in a sequence figure must
share the same `viewBox` dimensions and keep shared elements at identical coordinates.
Only color classes, pointer positions, and annotation text change between frames. The
linter enforces this: inconsistent viewBox values across frames trigger an ERROR.

**Avoid:** Changing the canvas size between frames; repositioning stable elements;
making a sequence figure when a single illustrative frame suffices (N=1 is valid —
default to static unless the concept is genuinely about change).
