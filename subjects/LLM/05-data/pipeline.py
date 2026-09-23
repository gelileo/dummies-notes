#!/usr/bin/env python3
"""Generates data-pipeline.md from a live run of data_pipeline.py. Run: python3 pipeline.py"""
import io, collections
from data_pipeline import (raw, GOOD, BOILER, SPAM, BENCH, HELDOUT, STOP, REF_BAD, toks, n_tokens,
                           quality, shingles, jaccard, minhash, minhash_sim, run_pipeline,
                           decontaminate, bigram_loss)
o = io.StringIO(); W = o.write
stages = run_pipeline(raw); clean = stages[-1][1]

W(f"""# The pipeline, traced

Every number here is produced by `data_pipeline.py`. Run `python3 pipeline.py` to regenerate.

The "crawl" is {len(raw)} documents — small enough to read every one — seeded with the things a
real crawl is full of: boilerplate repeated across pages, spam, exact duplicates, a
near-duplicate, one non-English page, some code. The pipeline is the real sequence of stages at
toy scale, and section 8 measures what it buys.

---

## 1. The crawl

```
""")
for s, d in raw: W(f"  [{s:<5}] {d[:70]}{'...' if len(d) > 70 else ''}\n")
W(f"""```

{len(raw)} documents, {n_tokens(raw)} tokens. The objective says "predict this", so whatever survives to the
end *is the specification of the model*.

---

## 2. Stage by stage

```
  stage                         docs  tokens   removed
""")
for name, docs, removed in stages: W(f"  {name:<28} {len(docs):>3}  {n_tokens(docs):>5}   {removed}\n")
W(f"""```

From {len(raw)} documents to {len(clean)}; from {n_tokens(raw)} tokens to {n_tokens(clean)}. Each stage below.

---

## 3. Language identification

Here: does the text contain any non-ASCII letters? That catches the Spanish page and nothing
else. Real pipelines run a classifier over character n-grams (fastText's `lid.176` is the
standard) and keep documents above a confidence threshold per target language. Either way, the
decision *which languages to keep, and at what threshold* fixes what the model will be able to do
in each one — and rare languages tend to sit near the threshold, where the classifier is least
reliable.

---

## 4. The quality classifier

Prose has dense function words and little repetition. Junk has a distinctive vocabulary and
repeats itself. The scorer learns the junk vocabulary from a handful of reference examples that
are **not** in the crawl, then scores every document:

```
""")
for label, d in (("good prose", GOOD[2]), ("good prose", GOOD[5]), ("boilerplate", BOILER), ("spam", SPAM)):
    W(f"  {label:<12} {quality(d):+.3f}   {d[:56]}...\n")
W(f"""```

Sign separates them. This is a miniature of exactly what production pipelines do: train a
classifier on "text we trust" versus "random crawl" and keep what scores well.

**Every such filter is a bias you have chosen.** Trust Wikipedia-like text and you down-weight
dialogue, dialects, and every register that does not resemble an encyclopedia. There is no
neutral filter; there is only the filter whose bias you understand.

---

## 5. Exact deduplication

Hash every document; keep the first with each hash. One pass, linear time, and it removed
{stages[3][2].split()[0]} copies here — the repeated boilerplate and the duplicated good sentence.

Why duplicates hurt: the loss is an average over tokens, so a document seen five times gets
five times the vote. Boilerplate repeated across every page of a site becomes, to the model,
the most important text on the internet. Some repetition of genuinely good data is fine
(section 7); accidental repetition of junk is not.

---

## 6. Near-duplicates

Documents that differ by a date, a footer, or one word have unrelated hashes. Cut each into
overlapping 3-word **shingles**, treat it as a set, and measure overlap:

```
""")
a, b = shingles(GOOD[1]), shingles(GOOD[1].replace("twice", "three times")); c = shingles(GOOD[3])
ha, hb, hc = minhash(a), minhash(b), minhash(c)
W(f"  near-dup pair    Jaccard {jaccard(a,b):.3f}    MinHash estimate (64 hashes) {minhash_sim(ha,hb):.3f}\n")
W(f"  unrelated pair   Jaccard {jaccard(a,c):.3f}    MinHash estimate (64 hashes) {minhash_sim(ha,hc):.3f}\n")
W(f"""```

Jaccard is the right measure and impossibly expensive at scale — a billion documents is
5×10¹⁷ pairs. **MinHash** replaces each shingle set with 64 numbers whose match rate estimates the
Jaccard, and locality-sensitive bucketing finds candidate pairs without comparing everything.
→ [essentials: hashing and set similarity](essentials/hashing-and-set-similarity/)

The threshold (here 0.5) is a knob. Set it high and you keep near-copies; set it low and you
start removing legitimately similar documents — two news reports of the same event, say.

---

## 7. Mixture weights and epochs

After cleaning, the crawl has a *natural* mix of sources. Nobody uses it as-is:

```
""")
by_src = collections.Counter(s for s, _ in clean); tok_src = collections.Counter()
for s, d in clean: tok_src[s] += len(toks(d))
total = sum(tok_src.values()); weights = {"web": 0.6, "books": 0.3, "code": 0.1}; budget = 200
W(f"  {'source':<8}{'docs':>6}{'tokens':>8}{'natural share':>15}{'chosen weight':>15}{'tokens sampled':>16}{'epochs':>9}\n")
for s in ("web", "books", "code"):
    nat = tok_src[s] / total if total else 0
    samp = weights[s] * budget
    ep = samp / tok_src[s] if tok_src[s] else float('nan')
    W(f"  {s:<8}{by_src[s]:>6}{tok_src[s]:>8}{nat:>15.2f}{weights[s]:>15.2f}{samp:>16.0f}{ep:>9.1f}\n")
W(f"""```

The **weight** is a decision about what the model should be good at, overriding what the crawl
happened to contain. Books and code are up-sampled — seen more than once per pass ("epochs"
above 1) — because there is less of them than you want. Up to about four repetitions of good
data helps; beyond that the model starts to memorise. Frontier runs choose these weights by
training small models on candidate mixtures and comparing (chapter 06's ladder, again).

Two more levers, not shown at this scale: **curriculum** — put the highest-quality data at the
*end* of training, where it disproportionately shapes the final model — and **synthetic data**,
model-written text that works well for maths, code and instructions and carries a real risk
when a model trains on its own unfiltered output.

---

## 8. Contamination

If a benchmark question is in the training set, the score on it means nothing. Check by
n-gram overlap:

```
""")
clean2, hits = decontaminate(clean, BENCH)
W(f"  benchmark item:   {BENCH[:60]}...\n  8-gram overlap with {len(hits)} training document(s)  ->  {'contaminated: removed' if hits else 'clean'}\n  training set after decontamination: {len(clean2)} docs\n```\n\n")
W(f"""Exact n-gram matching is the standard and it is porous — paraphrases, translations and
reformatted versions pass straight through. It is one of the main reasons benchmark numbers are
hard to trust, and it is [chapter 15](../15-evaluation/)'s problem to live with.

---

## 9. What the pipeline buys

Same bigram model, trained on the raw crawl versus the cleaned set, scored on clean held-out text
neither has seen:

```
""")
lr, lc = bigram_loss(raw, HELDOUT), bigram_loss(clean2, HELDOUT)
W(f"  trained on raw crawl   {n_tokens(raw):>4} tokens   held-out loss {lr:.3f} nats\n")
W(f"  trained on clean set   {n_tokens(clean2):>4} tokens   held-out loss {lc:.3f} nats\n")
W(f"  -> {n_tokens(raw)/n_tokens(clean2):.1f}x fewer tokens, {(1-lc/lr)*100:.0f}% lower loss\n```\n\n")
W(f"""**Less data, better model.** The duplicates and boilerplate were not merely useless — they
skewed every count toward junk. At this scale the effect is a few percent; at trillion-token
scale the difference between a careless and a careful pipeline is the difference between model
generations.

---

## 10. At real scale

*(Reported figures, not measured here.)* A Common Crawl snapshot is on the order of hundreds of
terabytes of raw HTML; there are around a hundred of them. FineWeb, a public pipeline over
those snapshots — URL filtering, text extraction, language ID, quality heuristics, exact and
MinHash deduplication — yields about 15 trillion tokens, and its authors report that
deduplication and filtering together remove the large majority of the raw text. Every stage
above exists at that scale, running for days on thousands of cores, and the choices at each one
are the least visible and most consequential decisions in a training run.

---

## 11. Invariants

1. **The corpus is the specification.** The objective says "predict this"; what "this" is, you chose.
2. **Every filter is a bias.** There is no neutral cleaning, only understood cleaning.
3. **Duplicates are votes.** Dedup is not tidiness; it is fixing the loss's weighting.
4. **Near-dedup needs a similarity, not equality** — Jaccard via MinHash, with a threshold you set.
5. **Mixture weights override the crawl.** Up-sampling is deliberate; a few epochs of good data is fine.
6. **Contamination checks are porous.** Treat benchmark numbers accordingly.
7. **Less, cleaner data can beat more, dirtier data.** Measured, even at 374 tokens.
""")
open('data-pipeline.md', 'w').write(o.getvalue())
print("wrote data-pipeline.md", len(o.getvalue()), "chars")
