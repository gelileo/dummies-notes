---
name: drill-down-essentials
description: >-
  Find the concepts a study chapter leans on but never explains — the maths,
  statistics or theory that would stop a capable high-school graduate — and expand
  each into a self-contained article plus a runnable script under `essentials/`.
  Use this whenever a chapter, tutorial, explainer or study note assumes background
  its reader may not have: when someone says a document "needs more depth", "assumes
  too much", "loses me at the maths", "explain the prerequisites", "what do I need to
  know to follow this", "drill down into the sub-concepts", "expand the fundamentals",
  or asks to make technical material readable for a non-specialist. Also use it
  proactively after writing or reviewing a technical chapter, before the reader hits
  the wall — an unexplained symbol is a hard stop, not a speed bump. Produces
  `essentials/<concept>/README.md` + `demo.py` per concept, an index, and links wired
  back into the parent chapter.
---

# Drill down into essentials

A study chapter is written by someone who already understands it. That makes it
almost impossible to notice the ideas you are *using* rather than *teaching* — the
dot product, the softmax, the variance argument behind a division. For a reader
without that background these are not speed bumps, they are hard stops: the chapter
silently degrades into symbol-shuffling, and the reader cannot tell whether they are
confused about the chapter or about the prerequisite.

This skill finds those stops and removes them, one self-contained article at a time.

## The shape of the output

```
<chapter>/essentials/
  README.md                     index — a lookup table, not a reading list
  vectors-and-dot-products/
    README.md                   the article
    demo.py                     runnable, prints the evidence the article quotes
  averages-and-normalization/
    README.md
    demo.py
```

One folder per concept, article always `README.md`, script always `demo.py`. Two
reasons: links can point at a bare folder (`essentials/rotation-and-rope/`), and most
git hosts render the article automatically when a reader navigates in.

## Process

### 1. Inventory what the chapter uses but does not teach

Read the chapter end to end — prose, drill list, code, terminology table — and write
down every term, symbol and operation that appears without being explained. Notation
counts as much as vocabulary: `[T, d_model]`, `Q · Kᵀ`, `√d_head` and `-inf` are all
jargon.

Be suspicious of your own fluency. The giveaway is a sentence that asserts a
mechanism instead of explaining it: *"the scaling keeps softmax from saturating"*
tells a reader who already knows exactly what they already knew.

### 2. Filter to genuine blockers

Keep a concept if a capable high-school graduate would stall on it. Drop it if the
reader's existing expertise already covers it — for a programmer, that means loops,
complexity, caching, parsing and data structures need no article.

Typical keeps: vectors, dot products, matrix multiplication, softmax, probability
distributions, mean and variance, normalization, high-dimensional geometry, rotation
and trigonometry, linear versus non-linear, gradients, expectation, entropy,
logarithms.

Aim for the handful that actually block the chapter. A dozen articles nobody reads is
worse than five that unblock everything, and each one you keep has to be genuinely
good.

### 3. Check who owns it

These articles are shared across a curriculum, not chapter-local. If an earlier
chapter already owns a concept, link to it instead of writing a second version — two
explanations of softmax will drift apart and the reader will not know which to trust.
Whichever chapter first needs a concept owns its article.

### 4. Write the script before the article

This ordering is the single most important thing in the skill, and it is worth being
stubborn about.

Write `demo.py` first: a small, dependency-free program that *measures* the claim the
article will make. Then write the article around whatever it actually printed.

Do it the other way round and you will write a plausible explanation and then look for
numbers that agree with it. Writing the measurement first repeatedly turns an
assertion into a derivation, and sometimes shows the assertion was wrong. Three real
examples from one chapter:

- *"Scores are divided by `√d_head` so softmax doesn't saturate"* — measuring the
  spread of a dot product at six different widths showed `std/√d` flat at 1.00 across
  three orders of magnitude. The divisor is not a heuristic, it is an exact
  cancellation, and the article could say so.
- *"Depth needs non-linearity"* — computing `x @ W1 @ W2 @ W3` and `x @ (W1@W2@W3)`
  to six decimal places showed them identical. Far more convincing than asserting it.
- *"A vector can hold more features than it has dimensions"* — an early draft said
  "far more than d", which is a hand-wave. Packing 5,000 random directions into 4,096
  dimensions and measuring the worst pairwise overlap (0.071) replaced it with a fact.

Script rules: standard library only, no network, no install step, deterministic (seed
anything random), and runnable from inside its own folder. It should print labelled
sections that can be pasted straight into the article.

### 5. Write the article

Structure that works:

```markdown
# Essential · <plain-language name>

**Needed for:** <the exact sentence in the parent chapter that stops making sense
without this, plus a link>

## <plain explanation, example before terminology>

...prose, with real output from demo.py in fenced blocks...

## Where chapter NN uses this
<the specific place, named>

## Run it
```bash
python3 demo.py
```

## Terms
| Term | Meaning |
```

Guidelines that matter more than the structure:

- **Assume only high-school maths**, and define every symbol you use. If an
  explanation needs another undefined term, that term needs its own row in the table
  or its own article.
- **Anchor on what the reader already knows.** For a programmer: a vector is an
  array, a matrix is a function, softmax is normalising a list of weights, attention
  priority is a queue. Reach for their expertise before reaching for a physical
  metaphor.
- **Show the thing, then name it.** Print the table, then say what it is called.
- **Quote real output**, never invented numbers. The whole point is that the reader
  can re-run it.
- **Say where the analogy breaks** if you use one. An unmarked analogy teaches a
  wrong model silently.
- **Keep it skippable.** Readers arrive mid-chapter, read one article, and leave.

### 6. Write the index as a lookup table

`essentials/README.md` is not a syllabus. Its job is to get a stuck reader to the
right article in one glance, so lead with the symptom, not the topic:

| Article | Read it when you hit… |
| --- | --- |
| Vectors and dot products | "the dot product measures alignment", cosine similarity |
| Averages and normalization | RMSNorm, and the `/ √d_head` in every score |

Say explicitly that nobody needs to read them all. A suggested order for anyone who
does want to read straight through is a useful footnote, not the main content.

### 7. Wire it back into the chapter

The reader has to find these at the moment they get stuck, which means a pointer in
the parent chapter *before* the hard material starts — the same symptom-first table,
plus a row in the chapter's file list.

### 8. Verify

Run `scripts/verify_essentials.py <chapter-dir>`. It checks that every concept folder
has both files, that every `demo.py` runs cleanly from its own directory, that every
relative link resolves, and that any mermaid blocks are syntactically valid. Broken
links are the most common failure after a reorganisation, and a reader who clicks one
loses trust in the whole set.

## What good looks like

The test is not whether the article is correct — it is whether a reader who was stuck
becomes unstuck. Concretely:

- Could someone who has never seen the notation follow it without stopping?
- Does every claim have output behind it that the reader can reproduce?
- Does it say which sentence in the parent chapter it unblocks?
- Can it be read in isolation, out of order, by someone who arrived from a link?

## Anti-patterns

- **Article first, numbers second.** You will assert rather than measure, and you will
  miss the cases where the measurement contradicts you.
- **Hand-waving a quantity.** "Far more than d", "much faster", "very small" — measure
  it or cut the claim.
- **Re-explaining what another chapter owns.** Link instead.
- **Turning the index into a reading list.** It is a lookup table for someone who is
  already stuck and slightly annoyed.
- **Writing an article for something the reader already knows.** Padding the set
  dilutes it and costs you credibility on the ones that matter.
- **A dependency.** `pip install` in a prerequisite explainer defeats the purpose.
