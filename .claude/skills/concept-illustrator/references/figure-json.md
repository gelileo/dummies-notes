# figure.json

Every figure directory contains a `figure.json` plus its frame SVGs.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `concept_slug` | string | yes | canonical slug of the concept this figure teaches |
| `title` | string | no | human-readable title |
| `archetype` | string | yes | `illustrative` \| `flowchart` \| `structural` \| `chart` |
| `playback` | string | yes | `static` (N=1) or `slideshow` (N>1) |
| `frames` | array | yes | ordered array of per-frame objects; see per-frame fields below |

### Per-frame fields

Each item in `frames`:

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `file` | string | yes | the frame's SVG filename |
| `caption` | string | yes | terse subtitle shown under the frame in the HTML viewer |
| `runbook` | string | yes | build-spec for the frame: what/why/how it is drawn; the ground truth a fidelity review diffs the SVG against; human-editable for re-runs |
| `commentary` | string | yes | rich narration for slides/video. Accessible, simple sentences. Caption is the viewer subtitle; commentary is narration-only and is NOT rendered in the HTML viewer. |

Rules:
- `frames` is non-empty; `static` figures have exactly one frame.
- Every `file` must exist in the directory and lint clean.
- **Frame-consistency:** all frames share the same `viewBox` so the sequence reads
  as evolution, not jump-cuts.

**runbook-first:** write each frame's `runbook` before drawing its SVG, then draw
from it, then write the `caption` (terse viewer subtitle) and `commentary`
(narration). The `caption`, `runbook`, and `commentary` fields are three different
texts and need not match each other or the in-SVG annotation.

## Progressive reveal (optional)

A frame may reveal its content one element at a time, driven by `data-reveal`
attributes in the SVG and a `beats` array in `figure.json`.

### SVG groups

Wrap each progressively-introduced element in a `<g>` with two attributes:

- `data-reveal="k"` — a **1-based integer** giving the reveal step at which this
  group becomes visible. Groups without `data-reveal` form the always-visible
  backdrop.
- `data-anim="rise|draw|fade"` — the entrance animation. Default is `rise`
  (element lifts in from below). Use `draw` for `<line>` elements and arrows
  (the path is stroked in progressively in the HTML player and "popped" via
  `visibility:hidden` in the MP4 cumulative-state rasterization). `fade` for a
  simple opacity cross-fade. The `data-anim` attribute is optional when `rise` is
  desired.

### `beats` array

A frame in `figure.json` may carry an optional `beats` key:

```
"beats": [
  { "caption": "short viewer subtitle for beat 1", "narration": "spoken sentence(s)" },
  { "caption": "…", "narration": "…" },
  …
]
```

- Each object in `beats` corresponds to one reveal index, in order (beat 0 ↔
  `data-reveal="1"`, beat 1 ↔ `data-reveal="2"`, …).
- `len(beats)` **must equal** `max(data-reveal)` across the frame's SVG. The
  validator (`render.py`) enforces this with an ERROR.
- `data-reveal` indices must be gap-free `1..N` with no missing values (also
  enforced).
- A frame with neither `data-reveal` groups nor `beats` is a single beat —
  the existing behavior is fully backward-compatible.

The `build_video.py` manifest builder expands a beat-carrying frame into one
manifest slide per beat, each with `transition: "reveal"` (except the first) and
`reveal_to: k+1`. The HTML player groups beat-slides sharing one figure image into
a single container div — the SVG is inlined **once**, with the JS animating
`[data-reveal]` group entrances per beat. The MP4 path uses `_reveal_svg` to
produce a cumulative-state SVG for each beat, hiding groups whose `data-reveal`
exceeds `reveal_to`.

**Canonical example:** `.claude/skills/concept-illustrator/examples/tcp-handshake-reveal`
— a single-frame illustrative figure with 6 beats (two box rises + three arrow draws
+ one badge rise).

Example:

```json
{
  "concept_slug": "quicksort",
  "title": "Quicksort partitions around a pivot",
  "archetype": "illustrative",
  "playback": "slideshow",
  "frames": [
    {
      "file": "frame-01.svg",
      "caption": "Pick the last element as the pivot.",
      "runbook": "Draw the unsorted array [3,1,4,1,5,2] with the last element (2) highlighted as the pivot. Label it 'pivot'. Show no movement yet — this is the starting state.",
      "commentary": "Quicksort begins by choosing a pivot. Here we always pick the last element. Everything else will be sorted relative to it."
    },
    {
      "file": "frame-02.svg",
      "caption": "Smaller values shuffle left of it.",
      "runbook": "Show the same array after one partition pass: elements less than 2 (1,1) on the left, pivot (2) in its final sorted position, elements greater than 2 (3,4,5) on the right. Use a bracket or color band to mark each region.",
      "commentary": "After partitioning, the pivot is in its final position. Values smaller than it are to its left; larger values are to its right. The pivot never moves again."
    }
  ]
}
```
