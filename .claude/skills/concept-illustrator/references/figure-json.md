# figure.json

Every figure directory contains a `figure.json` plus its frame SVGs.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `concept_slug` | string | yes | canonical slug of the concept this figure teaches |
| `title` | string | no | human-readable title |
| `archetype` | string | yes | `illustrative` \| `flowchart` \| `structural` \| `chart` |
| `playback` | string | yes | `static` (N=1) or `slideshow` (N>1) |
| `frames` | array | yes | ordered; each item `{ "file": "frame-01.svg", "caption": "..." }` |

Rules:
- `frames` is non-empty; `static` figures have exactly one frame.
- Every `file` must exist in the directory and lint clean.
- **Frame-consistency:** all frames share the same `viewBox` so the sequence reads
  as evolution, not jump-cuts.

Example:

```json
{
  "concept_slug": "quicksort",
  "title": "Quicksort partitions around a pivot",
  "archetype": "illustrative",
  "playback": "slideshow",
  "frames": [
    { "file": "frame-01.svg", "caption": "Pick the last element as the pivot." },
    { "file": "frame-02.svg", "caption": "Smaller values shuffle left of it." }
  ]
}
```
