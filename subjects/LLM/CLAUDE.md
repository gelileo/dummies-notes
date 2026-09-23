# CLAUDE.md — `subjects/LLM/`

How to work on this curriculum. `01-tokenizer/` is the reference implementation: when a rule here
is unclear, look at what that folder actually does.

## Scope

This file governs **study work under `subjects/LLM/`** — chapter READMEs, articles, demo scripts.
The repo root `CLAUDE.md` governs the `dummies_notes` *product* (skills, workflow, `knowledge/`).
Study material is reference content: it does **not** trigger the living-doc rule and needs no
`knowledge/` article or `log.md` entry.

Illustration via the `dummies-notes` workflow comes **after** the learning. Don't shape chapters
for it yet.

## Who the reader is

**A working programmer who is not a data scientist.** Assume fluency in: data structures, dicts
and arrays, loops, complexity, memory hierarchy, parsing, APIs, debugging. Assume nothing about:
linear algebra notation, statistics, gradient-based optimization, ML vocabulary.

The reader is going **top-down**: they chose each chapter because of where it sits in the
pipeline, and they drill until they can comfortably explain a leaf. Respect that — never demand
they accept something now "to be explained later". If a prerequisite is needed, either explain it
in place or link the chapter that owns it (see the shared-prerequisites table in `curriculum.md`).

---

## Rules

### 1. Run it, don't assert it

**Every number, table and trace in a chapter must come from executed code**, not from memory.
Write a script, run it, paste the real output.

This is the most important rule here, and not for tidiness — it has already caught real errors.
Claims in `01-tokenizer` that looked obviously right and were wrong when executed:

- "`' quokka'` borrowed `' tok'`" — the trace showed it merged *nothing*, and the real reason
  (`('o','k')` was never a merge on its own) was the better teaching point.
- "the training loop carries an `if not pairs: break` guard" — it didn't; the script crashed with
  `IndexError` when the budget was raised past 41.

If something genuinely cannot be executed here (no model weights, no network), **say so plainly**
and mark it as reasoning rather than measurement. Never dress an estimate as a measurement.

### 2. Plain language

Short sentences. One idea per paragraph. Concrete before abstract.

- **Define a term at its first use, in a sentence, before leaning on it.** Not "the logits" —
  "the raw scores the last layer produces, one per vocabulary entry (*logits*)".
- **No unexplained acronyms.** Expand on first use, every chapter, even obvious ones.
- **Prefer the plain phrase over the term of art** when both fit: "the table that maps ids to byte
  strings" reads better than "the vocab" the first three times.
- **Cut hedging and filler.** "It is important to note that" carries no information.

A test: could a competent backend engineer who has never read an ML paper follow this paragraph
without stopping? If not, rewrite it.

### 2a. Every chapter has a Terminology table

Rule 2 says define a term at first use. That handles the reader going *forwards*. A **Terminology**
section handles them coming *back* — hitting an unfamiliar word three weeks later and needing one
place to look.

List **every piece of technical jargon the chapter introduces**, in a two-column table, with a
plain-language explanation that stands on its own. Rules:

- **One sentence, no jargon inside the jargon.** If the explanation needs another undefined term,
  that term needs its own row.
- **Include the aliases.** `d_model` is also `hidden_size`, `n_embd`, `hidden_dim`. Readers meet
  whichever name their codebase uses.
- **Include notation**, not just words: `[T, d_model]`, `Q · Kᵀ`, `√d_head`.
- **Mark terms owned elsewhere** with a chapter link rather than re-explaining them.
- Order by **when the chapter first uses them**, not alphabetically — it doubles as a reading path.

### 2b. Say what the chapter's code actually computes

Where a chapter has a primary function — and most do — state it as a **signature plus four plain
sentences**, before any explanation of how it works:

```
encode(text: str) -> list[int]
```

- **Input** — what you hand it, in plain words.
- **Output** — what you get back, in plain words.
- **Goal** — what it is *for*; why this function exists in the pipeline at all.
- **What it does NOT do** — the boundary. This one prevents more confusion than the other three
  combined: chapter 02's forward pass does no sampling, no looping and no learning, and saying so
  explicitly stops a reader assuming generation happens there.

A programmer reads a signature faster than a paragraph. Give them the signature first.

### 2c. Maths a high-school graduate would stumble on goes in `essentials/`

The reader is a programmer, not a data scientist. Any concept in a chapter that would block a
capable high-school graduate is a **hard stop** — without it the chapter degrades into
symbol-shuffling — so it gets its own self-contained article under the chapter's `essentials/`
folder, **one folder per concept**:

```
NN-topic/essentials/
  README.md                        index: "read this one when X stops making sense"
  vectors-and-dot-products/
    README.md                      the article
    demo.py                        runnable, stdlib-only, prints the evidence
  matrices-as-functions/
    README.md
    demo.py
```

What counts: vectors, dot products, matrix multiplication, softmax, probability distributions,
mean/variance, normalization, high-dimensional geometry, rotation and trigonometry, linear vs
non-linear, gradients, expectation, entropy. What does not: anything a working programmer already
has — loops, complexity, caches, parsing.

Each article must:

- **assume only high-school maths**, and define every symbol it uses
- **say at the top what it is needed for**, naming the exact sentence in the parent chapter that
  stops making sense without it
- **prove its claims by running code**, per rule 1. The `√d_head` article does not assert that
  scores grow with `√d` — it measures the spread at six different sizes and shows `std/√d` flat
  at 1.0
- **end with a terminology table**, per rule 2a
- be **skippable and self-contained**. The index is a lookup table, not a reading list: readers
  arrive mid-chapter, read one article, and go back

These are shared across the curriculum, not chapter-local. Whichever chapter first needs a
concept owns the article; later chapters link to it rather than re-explaining — the same
ownership rule as the shared-prerequisites table in `curriculum.md`.

**There is a skill for this.** `drill-down-essentials` (in `.claude/skills/`) carries the full
process — how to inventory what a chapter assumes, how to filter to genuine blockers, why the
demo script gets written *before* the article, and the article template. Invoke it when adding
essentials to a chapter. Its `scripts/verify_essentials.py <chapter-dir>` checks structure,
runs every demo, resolves every link and validates mermaid blocks; run it before calling a
chapter done.

### 3. Anchor on what the reader already knows

Map each new idea onto a programming concept before naming it. This carried `01-tokenizer` almost
entirely:

| Instead of | Say |
| --- | --- |
| "the vocabulary" | a dict with integer keys: `{256: b' t', 257: b'ok'}` |
| "BPE merge priority" | a priority queue keyed on merge id |
| "attention is O(n²)" | every token compares against every other — a nested loop |
| "the KV cache" | memoizing results that can't change, because of the causal mask |

Reach for the reader's expertise (caches, indexes, parsers, queues) before reaching for a
physical-world metaphor.

### 4. Show the thing, then name it

Example first, terminology second. `01-tokenizer` shows a printed merge table, *then* says "this
is the vocabulary". Not the other way round.

### 5. Analogies — use them, and say where they break

A good analogy is worth a page of prose. An unmarked one silently teaches a wrong model, so
**always note the limit**: "backprop is a manager walking the assembly line backwards assigning
blame — but unlike a factory, every station is adjusted simultaneously and by a precise amount."

Prefer an analogy that explains a *mechanism* over one that merely conveys a mood.

### 6. Diagrams — mermaid for structure, ASCII for state

Both render in this setup: the `markdown-preview-enhanced` extension renders mermaid in the IDE
preview, and GitHub renders it in `.md` files. Pick by what the diagram is *of*.

**Use mermaid** when the content is **structure or flow** — a pipeline, a dependency graph, a
sequence of interactions over time, a state machine, how components relate. Auto-layout is worth
more than character control here, and the result reads far better than ASCII art. The reference
example is the pipeline at the top of `01-tokenizer/README.md`.

**Use ASCII in a fenced code block** when the content is **data or state**, specifically:

- anything with **aligned columns** — mermaid cannot do the `merges | vocab` side-by-side layout
  in `bpe-workflow.md`
- **tensor shapes** flowing through layers, where `[batch, seq, d_model]` must line up
- **anything a script generates.** Rule 8 says generate the evidence; traces and tables must come
  out of the generator, and mermaid is awkward to emit and wrong for exact state
- memory layouts, byte layouts, before/after snapshots

A rough test: if the diagram would still be correct with the numbers changed, it is structure →
mermaid. If the specific values *are* the point, it is state → generated ASCII.

**Mermaid practicalities** (learned by rendering, not guessing):

- **Quote every label** — `A["..."]` — and use `#quot;` for a literal double quote. Labels full of
  `[`, `]`, `(`, `'` are constant in this curriculum and will break the parse unquoted.
- `<br/>` for line breaks; `<i>` and `<b>` work; `&nbsp;` for spacing inside a label.
- Put the operation on the **edge** (`A -->|"1 · do the thing"| B`) and the data in the **node**.
  That separation is what makes these diagrams readable.
- Keep to ~10 nodes. Past that auto-layout degrades and you should split the diagram.
- Don't hardcode colors — GitHub and the IDE preview each apply their own light/dark theme.
- **Validate before committing**: `npx -y @mermaid-js/mermaid-cli -i d.mmd -o d.png` renders it,
  and a syntax error fails loudly instead of silently showing a broken block to the reader.

### 7. Always land on real scale

A toy example teaches the mechanism; it must then be anchored to production, or the reader
calibrates wrongly. Every worked example ends with the equivalent at GPT-2 / Llama-3 / GPT-4
scale, with the arithmetic shown — vocabulary sizes, parameter counts, FLOPs, token counts,
dollars. State the model and version you're quoting.

### 8. Generate the article when it contains tables or traces

If a document is mostly step-by-step state, **write the generator, not the document**.
`bpe_workflow.py` → `bpe-workflow.md` means the article can never drift from the algorithm, and
the reader can change a parameter and regenerate.

Generator rules:
- runnable as `python3 script.py` from its own chapter folder, with **no install step and no
  network**
- **deterministic** — seed every random source, so re-running reproduces the article exactly
- hardcoded commentary must be re-checked whenever the parameters change (a wrong comment beside
  correct generated output is worse than no comment)

Hand-write the prose; generate the evidence.

#### Dependencies by chapter

Verified environment: **Python 3.14.7, numpy 2.4.4**. torch, matplotlib and scipy are *not*
installed.

| Chapters | Allowed | Why |
| --- | --- | --- |
| **01–03** | **stdlib only** | Here the loops *are* the lesson. A hand-written matmul or softmax over a 4×8 toy model teaches more than a vectorised one-liner, because every index is visible. |
| **04 onward** | **stdlib + numpy** | Autograd, RL, profiling, quantization and contrastive training need real arrays. Writing those in pure Python buries the idea under bookkeeping. |

Still forbidden everywhere: a dependency that is not installed. If a chapter genuinely needs
torch or a plotting library, **say so and ask** — do not silently add an install step, and do not
quietly shrink the example to dodge the question. Prefer numpy plus a saved `.txt`/ASCII plot over
pulling in matplotlib.

### 9. Correct plainly, in place

When something recorded turns out to be wrong, fix the file and say what changed in one sentence.
No throat-clearing, no ceremony. A wrong line in a study note is worse than a gap, because the
reader has no way to know it's wrong.

---

## Chapter layout

```
NN-topic/
  README.md               scope, drill list, cross-refs, done-when checklist, Q&A, Notes
  <topic>.md              deep-dive articles (generated where possible)
  <topic>.py              generators and runnable demos
  essentials/             the maths this chapter assumes - see rule 2c
    README.md             index: which article to read when
    <concept>/
      README.md           the article
      demo.py             runnable, stdlib-only
```

`README.md` section order is fixed:

1. header (stage, read-after, feeds, twelve-ideas mapping)
2. **Why this chapter exists**
3. **The whole chapter in one picture** — mermaid, per rule 6
4. **What this chapter computes** — signature + input/output/goal/not-this, per rule 2b
5. **Terminology** — per rule 2a
6. **Files in this chapter**
7. **Drill list**
8. **Shared prerequisites** — what this chapter owns for others
9. **Build it**
10. **You're done when you can…**
11. **Q&A** — grows as questions come
12. **Notes** — left empty, for the reader

## Q&A protocol

When the reader asks a question about the current chapter:

1. **Answer it in the conversation** — that's what they read.
2. **Record it in that chapter's `## Q&A`**, question as an `### Q:` heading, phrased the way they
   asked it.
3. Include the evidence (real output), the cross-references, and the counter-intuitive bit if
   there is one.
4. If the answer contradicts something already written, fix that too.

Questions are the actual curriculum. A chapter's Q&A ends up more valuable than its drill list,
because it records what was genuinely unclear rather than what was predicted to be unclear.

## Before finishing a response

- [ ] Every number came from running something.
- [ ] Every term was defined at first use.
- [ ] Toy example anchored to production scale.
- [ ] Q&A recorded in the chapter README.
- [ ] Any claim about a file verified by reading that file — not inferred from a sibling.
