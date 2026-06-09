# dummies_notes — architecture design

- **Date:** 2026-06-09
- **Status:** approved (architecture); Phase 1 to be planned next
- **Runtime:** Claude Code skills + a Workflow script (no standalone app)

## Vision

Given a topic, teach it with **intuitive illustrations + captions** instead of prose.
Recursively break the topic into its prerequisite concepts down to an **atomic**
level — small enough that one figure explains it — illustrate each, and assemble
the result into a bottom-up explainer doc and an interactive concept map.

## Governing principles

1. **Reuse = referencing, not asset reuse.** A concept is illustrated once and
   *linked* thereafter ("RSA → see Modular arithmetic"). Figures are drawn fresh
   in context; they are never imported wholesale from another concept.
2. **Consistency is engineered, not inherited from reuse.** Because figures are
   drawn fresh, a shared style system keeps them a family (see Style system).
   Literal reuse survives only at the *primitive* level (a cell shape, a pointer) —
   that is the consistency mechanism, not a goal in itself.
3. **Vivid metaphor, plain words, restrained visuals.** Engagement comes from bold
   spatial metaphors and friend-explaining-it captions — not from decoration. The
   clean minimalist look is preserved: no gradients/shadows/emoji, no jargon.
4. **Simplicity wins, verbose is boring.** Short captions, uncluttered figures,
   lean notes. A figure that needs a paragraph failed. Notes that repeat
   themselves mean the reference graph failed.

## Components

Each piece is atomic, reusable, and independently testable — the system mirrors
its own philosophy.

| Component | Type | Responsibility | Scope of awareness |
|---|---|---|---|
| `concept-illustrator` | skill | One concept → one **figure** (1…N self-contained SVG frames + plain captions + playback metadata), drawn in the shared style, lint-gated. | Only the single concept handed to it |
| `concept-decompose` | skill | One concept → canonical slug, plain definition, **atomicity verdict**, direct prerequisites (slug + definition each). | Only one level down |
| `concept-registry` | script (zero-dep Python) | Slug-based reference graph. "Covered already? → return a link and stop recursing." Stores figure metadata; drives cross-references. | Identity + linking rules only |
| `concept-reviewer` | review agent(s) (fresh context) | Judges a generated artifact against the concept with **eyes that never saw the generation reasoning**. Two roles: blind-reader (comprehension) and fidelity critic (correctness). Returns a structured verdict + gaps. | Only the artifact (blind) / artifact + concept (critic) |
| `dummies-notes` | Workflow | The only recursive/stateful piece. Orchestrates decompose → register/link → illustrate → review → assemble → chain-review. Caps depth/breadth and review retries; `log()`s anything capped. | The whole graph |
| viewer | static HTML/JS | `slideshow.html` plays a figure's frames (prev/next/autoplay, light/dark); `map.html` renders the concept graph. | Rendering only |

## Data model

- **Concept** — `{ slug, name, definition, prerequisites: [slug], atomic: bool }`
- **Figure** (the unit a concept maps to) —
  `{ concept_slug, archetype, playback: "static" | "slideshow", frames: ["frame-01.svg", …], captions: [...] }`.
  Single-frame is just N = 1.
- **Decomposition graph** — a DAG. Nodes = concepts, edges = "depends on".
- **Registry on disk** — `registry/<slug>/` holding `figure.json` + `frame-NN.svg`
  + `caption.md`; a top-level `registry/index.json`. One figure per slug.

### Concept identity

Canonical **slug + one-line definition**. Reuse/linking keys on the slug; the
definition disambiguates collisions ("mean: average" vs "mean: unkind"). On slug
collision with a differing definition, append a qualifier. Identity answers *"have
I already covered this, so I can link to it?"* — not *"can I reuse this SVG?"*.

### Atomicity

A concept is **atomic** when (a) one figure of ≤ ~6 frames explains its mechanism
without needing a sub-figure, and (b) its remaining prerequisites are common
knowledge for the target audience. Audience level is a parameter; default is
"a curious adult with no domain background." Jargon in a definition is a signal to
decompose, never to assume — an obscure term becomes its own prerequisite node.

## Data flow (the `dummies-notes` Workflow)

1. **Seed** — canonicalize the target topic → slug + definition.
2. **Decompose (recursive fan-out)** — for each non-atomic concept, call
   `concept-decompose`; recurse on new prerequisites. Before recursing into a node,
   check `concept-registry`: if already covered, record a **reference link** and
   **stop** (treat as a citation). Cap depth/breadth as a runaway backstop and
   `log()` anything capped. Result: the DAG.
3. **Illustrate (fan-out over atomic nodes not already in the registry)** —
   `concept-illustrator` storyboards → renders frames → lints. Atomic (leaf) nodes
   only; intermediate nodes are handled at assembly (step 5).
4. **Review each figure (fresh-eyes gate, before registering)** — a separate
   `concept-reviewer` agent runs the blind-reader test and the fidelity critic on
   the artifact. On a gap, loop back (bounded ≈2 retries): regenerate the figure
   with the critique, or — if the gap is a missing prerequisite — return to
   `concept-decompose` to add the node. Only a passing figure enters the registry;
   if retries are exhausted, register it **flagged** and `log()` the gap.
5. **Assemble** — topologically sort atomic-first; emit **both**:
   - a bottom-up explainer doc — each concept's figure + caption, ordered so every
     idea builds on already-illustrated ones; already-covered prerequisites are
     **linked, not re-inlined**. **Intermediate (non-leaf) nodes render
     caption-only** — a short paragraph that links up to its children's figures —
     **except the target**, which gets a **composition figure**: a light figure
     built *from* the already-illustrated children, showing how they snap together
     (produced via `concept-illustrator`'s compose-from-children mode). The target
     is the payoff, so it earns a real "here's how it all assembles" picture;
   - an interactive concept map — nodes carry figure thumbnails, edges are the
     dependency/reference links — over the same registry.
6. **Chain review (end-to-end, fresh agent)** — a `concept-reviewer` agent reads
   the *assembled* notes bottom-up and reports graph-level gaps: leaps between
   concepts, a prerequisite the chain assumes but never illustrates, or a path that
   doesn't actually reach the target. Findings either trigger a bounded repair
   (add/redraw a node) or surface as a gap report alongside the output.
7. **Validate** — lint every SVG, assert the graph is a DAG, assert every atomic
   node has a figure.

## Style system (how consistency is engineered)

Strongest (deterministic) to softest:

1. **Shared stylesheet + template** — every figure embeds the same `_style.css`
   and starts from `template.svg`: fixed palette, two type sizes, sentence case,
   0.5 strokes, named color ramps. Handles color/type/spacing baseline.
2. **Visual-vocabulary library** — `references/visual-vocabulary.md` plus small
   reusable SVG snippets for recurring primitives: array/list cell, pointer, graph
   node, edge, container/set, stack frame, function box, and state styles (active,
   eliminated/greyed, target). Makes a list *look like a list* everywhere. This is
   the only place literal reuse lives (primitive level).
3. **Color-role conventions** — a documented role→ramp mapping applied across all
   figures (e.g. under-consideration = teal, eliminated = gray, target = coral), so
   color *means* the same thing everywhere.
4. **Style linter as a gate** — `scripts/render.py` extended to reject off-palette
   colors, wrong type sizes, non-sentence-case, wrong canvas width. Every figure
   passes before entering the registry.
5. **Example gallery** — canonical figures (the binary-search example) the
   illustrator reviews before drawing, to anchor the aesthetic.

## Voice & metaphor

A `references/voice-and-metaphor.md` guideline + a bank of worked metaphors keeps
the writing consistent the way the style system keeps the visuals consistent.
Captions read like a knowledgeable friend explaining it: concrete, warm, short,
metaphor-first (recursion = nested Russian dolls; a stack = plates pushed on and
popped off the top; a hash map = keys dropped into labeled mailboxes). The
**illustrative-metaphor archetype is the strong default**; retreat to
flowchart/structural/chart only when the concept genuinely is a process,
containment, or quantity.

## Multi-frame figures

An atomic illustration is **one figure = an ordered sequence of 1…N self-contained
SVG frames**. Process/trace concepts (sorting, traversal, gradient descent, a
handshake, recursion unwinding) become sequences; static concepts are N = 1.

- **Storyboard step:** before rendering, decide static vs sequential; if
  sequential, plan what changes between frames.
- **Frame-consistency rule:** frames share canvas size and element positions so the
  sequence reads as *evolution*, not jump-cuts — cells stay put; only highlights and
  pointers move. This is what also makes them animatable.
- **Playback:** separate frame SVGs (each individually reusable, light/dark,
  PNG-exportable) sequenced by the HTML viewer (prev/next + autoplay). Frames are
  the source of truth; compiling to GIF/MP4 is a possible later add-on, not in scope.

## Verification — fresh-eyes review

The generator suffers the **curse of knowledge**: it knows what it meant, so it
reads its own figure as correct even when the figure alone doesn't carry the idea.
Every review is therefore done by a **separate agent that never saw the generation
reasoning** — in Workflow terms, a distinct `agent()` call with a clean context.

Two complementary checks per figure:

- **Blind-reader test (comprehension).** The agent sees *only the figure + caption*
  — not the concept definition, not the storyboard — and answers "what does this
  teach, and what's confusing?" Its answer is compared to the intended concept;
  divergence means the picture fails to convey the idea.
- **Fidelity critic (correctness).** The agent sees the concept and adversarially
  hunts for what's wrong, misleading, or silently assumed (including a missing
  prerequisite).

**Repair loop, not just a verdict.** A failed review feeds back, bounded to ≈2
retries: a figure-level gap → regenerate with the critique; a missing-prerequisite
gap → re-decompose to add the node. If still failing, register the figure flagged
and log the gap rather than ship a silent error.

**Two altitudes.** Per-figure review gates entry to the registry (Phase 1).
End-to-end chain review reads the assembled notes for graph-level gaps the
per-figure check can't see — leaps, unmet prerequisites, a path that never reaches
the target (Phase 4).

## Making the existing skill actionable

The current `example/concept-illustrator-SKILL.md` references files that do not
exist. Becoming real means authoring them and extending the contract:

- **Author the promised assets:** `assets/template.svg`, `assets/_style.css`,
  `references/design-system.md`, `references/archetypes.md`, and `scripts/render.py`
  (the dependency-free linter + PNG export the SKILL.md already describes).
- **Add new assets:** `references/visual-vocabulary.md` (+ primitive snippets) and
  `references/voice-and-metaphor.md`.
- **Extend the contract:** storyboard step, sequence archetype, frame-consistency
  rule, multi-frame `figure.json` output.
- **Compose-from-children mode:** given a concept plus its already-illustrated
  children, produce a light composition figure showing how the children snap
  together. Used for the target node at assembly (step 5); lands in Phase 4 since it
  needs child figures to exist.
- **Machine-callable I/O:** input = concept slug/name/definition; output = a figure
  directory the Workflow can register.

## Proposed directory layout

```text
.claude/skills/concept-illustrator/   # SKILL.md, assets/, references/, scripts/render.py
.claude/skills/concept-decompose/     # SKILL.md
.claude/workflows/dummies-notes.*     # the orchestrator Workflow
scripts/concept-registry              # registry CLI (lookup/put/index)
registry/<slug>/                      # figure.json, frame-NN.svg, caption.md  (+ index.json)
viewer/                               # slideshow.html, map.html
output/<topic>/                       # generated notes.html + map.html
```

## Build phases

Each phase is its own spec → plan → build cycle.

- **Phase 1 — `concept-illustrator`, made real.** Complete the promised assets, add
  the style/vocabulary/voice references and the linter gate, add multi-frame +
  storyboard + frame-consistency, the **per-figure fresh-eyes review** (blind-reader
  and fidelity critic) with its bounded repair loop. **Viewer scope: only
  `slideshow.html`** — the single-figure player, needed to even view a multi-frame
  figure standalone. (The concept map and doc assembly are Phase 4.) *Independently
  useful; the foundation everything else calls.* **Plan this next.**
- **Phase 2 — `concept-decompose` + `concept-registry`.** Single-level decomposition
  primitive and the reference graph.
- **Phase 3 — `dummies-notes` Workflow.** Wire the recursion: decompose → link →
  illustrate → review.
- **Phase 4 — assembly + map viewer + chain review.** Bottom-up explainer doc and
  the interactive concept map (`map.html`) over the registry; the
  compose-from-children mode for the target's composition figure; the end-to-end
  chain review.

## Non-goals (YAGNI)

- No standalone web app / API — Claude Code skills + Workflow only.
- No semantic/embedding concept matching at first — canonical slug + definition;
  a semantic matcher can be swapped into the registry interface later if it earns it.
- No GIF/MP4 compilation in scope — separate frames + HTML viewer.
- No relaxing of the minimalist visual constraints — vividness comes from metaphor.
- No literal whole-figure reuse across concepts — referencing instead.

## Open questions (resolve during planning, not blocking)

- Exact `concept-decompose` ↔ `concept-illustrator` ↔ Workflow I/O schemas
  (JSON shapes).
- Where the registry lives relative to the living-doc `knowledge/` base (sibling
  `registry/` vs under `knowledge/`).
- Audience-level parameter surface (single default vs selectable).
- Review calibration: how strict the blind-reader/intended-concept comparison is
  (who judges the match, what counts as "diverged"), and the exact retry bound.
