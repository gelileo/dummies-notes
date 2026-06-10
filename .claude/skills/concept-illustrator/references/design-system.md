# Design system

The shared rules that make every figure a family member, not a custom drawing.
Read this before touching a single SVG attribute. Full authority: `assets/_style.css`.

---

## Palette

Nine named ramps. Each ramp has a light hex and a dark hex (the CSS media query
switches automatically). Color encodes category, not sequence — pick one ramp per
semantic role and hold it for the life of the figure.

| Ramp | CSS class | Light fill | Light stroke | Dark fill | Dark stroke |
|------|-----------|-----------|--------------|-----------|-------------|
| Purple | `c-purple` | `#EEEDFE` | `#534AB7` | `#3C3489` | `#AFA9EC` |
| Teal | `c-teal` | `#E1F5EE` | `#0F6E56` | `#085041` | `#5DCAA5` |
| Coral | `c-coral` | `#FAECE7` | `#993C1D` | `#712B13` | `#F0997B` |
| Pink | `c-pink` | `#FBEAF0` | `#993556` | `#72243E` | `#ED93B1` |
| Gray | `c-gray` | `#F1EFE8` | `#5F5E5A` | `#444441` | `#B4B2A9` |
| Blue | `c-blue` | `#E6F1FB` | `#185FA5` | `#0C447C` | `#85B7EB` |
| Green | `c-green` | `#EAF3DE` | `#3B6D11` | `#27500A` | `#97C459` |
| Amber | `c-amber` | `#FAEEDA` | `#854F0B` | `#633806` | `#EF9F27` |
| Red | `c-red` | `#FCEBEB` | `#A32D2D` | `#791F1F` | `#F09595` |

Apply a ramp by placing `class="c-teal"` on a `<g>` group or directly on a shape.
Child `<text>` elements inherit the correct ink color automatically.

**Rule: color encodes category, not sequence.** Assigning a different ramp to each
step in a 6-step algorithm is decoration. Assign one ramp to "nodes under
consideration" and another to "eliminated nodes" — that is meaning.

---

## Color-role conventions

Fixed role → ramp mapping applied across every figure so the same color means the
same thing everywhere:

| Role | Ramp | Why |
|------|------|-----|
| Under consideration / active | `c-teal` | Positive action, "looking here" |
| Eliminated / inactive / visited | `c-gray` | Faded, done, no longer live |
| Target / goal / answer | `c-coral` | Destination, the thing we found |
| Neutral structure (boxes, containers, edges) | `c-gray` or plain `box` | Background scaffolding |

Reserve blue/green/amber/red for genuine semantic meaning:
- `c-blue` — informational; or a physical property that is literally blue (sky, water)
- `c-green` — success / correct / positive signal
- `c-amber` — warning / caution / slow path
- `c-red` — error / failure / danger

Purple and pink are neutral accent ramps for category differentiation when teal,
coral, and gray are already spoken for.

These role→ramp meanings (teal = under-consideration/active, gray = eliminated/inactive, coral = target/goal) apply to **illustrative** and **sequence** figures, where elements carry state. **Structural, flowchart, and chart** figures instead use ramps for pure *category* — prefer purple / blue / pink for neutral categories there, and avoid teal/coral/gray so a reader never misreads a category as a state.

---

## Type

Three classes only. No inline `font-size`. No other sizes.

| Class | Size | Weight | Typical use |
|-------|------|--------|-------------|
| `th` | 14 px | medium (500) | Box title, node label, heading |
| `t` | 14 px | regular (400) | Body label, caption, description |
| `ts` | 12 px | regular (400) | Subtitle, secondary label, index |

Sentence case everywhere — the linter rejects ALL CAPS and warns on Title Case.
First word capitalised, rest lower, except proper nouns.

---

## Canvas & geometry

- **ViewBox:** always `viewBox="0 0 680 H"`. Width 680 is fixed. Set `H` using
  `H = y_max + 40`, where `y_max` is the bottom edge of the lowest element. Do not shrink the width for narrow
  content — center it instead.
- **Box width from label length:** `width ≥ max(title_chars × 8, subtitle_chars × 7) + 24`.
  A 100 px box fits roughly a 10-character subtitle. Undersized boxes are the most
  common layout failure.
- **Stroke weight:** `0.5` on all box borders. Refined and light; heavier strokes
  make figures feel busy.
- **Text placement:** use `text-anchor="middle"` and `dominant-baseline="central"`,
  with `y` at the vertical center of the slot. Never guess vertical offset by eye.
- **Arrows:** `class="arr" marker-end="url(#arrow)"` from the template. Arrow paths
  must set `fill="none"` — an omitted fill renders as a filled shape. Route around
  boxes with an L-bend `<path>` rather than crossing unrelated elements.

---

## Banned

The following make figures feel designed-for-impact rather than drawn-for-clarity.
The linter flags violations:

- **Gradients** — one `<linearGradient>` is permitted only in an illustrative figure
  to depict a continuous physical property (e.g., a temperature gradient along a rod).
  In every other context, gradients are banned.
- **Shadows and glows** — no `<filter>` elements.
- **Emoji** — the linter rejects them in `<text>` content.
- **Jargon** — unknown terms get decomposed into their own prerequisite node;
  they are never assumed in labels or captions.
- **Inline colors** — no `fill="#abcdef"` or `style="color:…"` on elements. All color
  must come from palette CSS classes or be `none`/`inherit`/`transparent`/`currentColor`.
- **Mixed archetypes** — a flowchart and an illustrative metaphor do not share a canvas.
  Make two separate figures.
