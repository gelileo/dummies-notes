# The pipeline, traced

Every number here is produced by `data_pipeline.py`. Run `python3 pipeline.py` to regenerate.

The "crawl" is 27 documents — small enough to read every one — seeded with the things a
real crawl is full of: boilerplate repeated across pages, spam, exact duplicates, a
near-duplicate, one non-English page, some code. The pipeline is the real sequence of stages at
toy scale, and section 8 measures what it buys.

---

## 1. The crawl

```
  [web  ] the baker rises before dawn and the bread is warm when the shop opens
  [web  ] buy now buy now best price best price free free free click click click
  [web  ] click here to subscribe accept cookies privacy policy terms of service...
  [web  ] the river runs through the valley and the farmers water their fields f...
  [web  ] the old clock in the hall has kept time for a hundred years without fa...
  [web  ] the river runs through the valley and the farmers water their fields f...
  [web  ] he fixed the fence and then sat on the porch until the light was gone
  [web  ] she opened the letter and read it three times before she understood wh...
  [web  ] the river runs through the valley and the farmers water their fields f...
  [web  ] the river runs through the valley and the farmers water their fields f...
  [code ] def f(x): return x*x  #  TODO fix  {{ }} ;; == != <> [] [] []
  [books] in the beginning the house was quiet and the garden was full of birds
  [web  ] we walked along the shore and watched the boats come back with the tid...
  [web  ] a good map shows the roads and the rivers but not every stone along th...
  [web  ] el río corre por el valle y los granjeros riegan sus campos con su agu...
  [web  ] every autumn the leaves turn and the hills look like they are on fire
  [web  ] click here to subscribe accept cookies privacy policy terms of service...
  [web  ] the river runs through the valley and the farmers water their fields f...
  [web  ] click here to subscribe accept cookies privacy policy terms of service...
  [books] the road bent twice and then ran straight toward the distant hills
  [web  ] buy now buy now best price best price free free free click click click
  [web  ] buy now buy now best price best price free free free click click click
  [web  ] click here to subscribe accept cookies privacy policy terms of service...
  [web  ] she opened the letter and read it twice before she understood what it ...
  [web  ] click here to subscribe accept cookies privacy policy terms of service...
  [code ] def f(x): return x*x  #  TODO fix  {{ }} ;; == != <> [] [] []
  [web  ] click here to subscribe accept cookies privacy policy terms of service...
```

27 documents, 374 tokens. The objective says "predict this", so whatever survives to the
end *is the specification of the model*.

---

## 2. Stage by stage

```
  stage                         docs  tokens   removed
  raw crawl                     27    374   -
  language filter               26    359   1 non-English
  quality classifier            17    245   9 scored as junk
  exact dedup (hash)            12    173   5 identical copies
  near-dedup (MinHash)          11    159   1 near-duplicate
```

From 27 documents to 11; from 374 tokens to 159. Each stage below.

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
  good prose   +0.188   a good map shows the roads and the rivers but not every ...
  good prose   +0.133   the old clock in the hall has kept time for a hundred ye...
  boilerplate  -1.167   click here to subscribe accept cookies privacy policy te...
  spam         -2.571   buy now buy now best price best price free free free cli...
```

Sign separates them. This is a miniature of exactly what production pipelines do: train a
classifier on "text we trust" versus "random crawl" and keep what scores well.

**Every such filter is a bias you have chosen.** Trust Wikipedia-like text and you down-weight
dialogue, dialects, and every register that does not resemble an encyclopedia. There is no
neutral filter; there is only the filter whose bias you understand.

---

## 5. Exact deduplication

Hash every document; keep the first with each hash. One pass, linear time, and it removed
5 copies here — the repeated boilerplate and the duplicated good sentence.

Why duplicates hurt: the loss is an average over tokens, so a document seen five times gets
five times the vote. Boilerplate repeated across every page of a site becomes, to the model,
the most important text on the internet. Some repetition of genuinely good data is fine
(section 7); accidental repetition of junk is not.

---

## 6. Near-duplicates

Documents that differ by a date, a footer, or one word have unrelated hashes. Cut each into
overlapping 3-word **shingles**, treat it as a set, and measure overlap:

```
  near-dup pair    Jaccard 0.562    MinHash estimate (64 hashes) 0.562
  unrelated pair   Jaccard 0.000    MinHash estimate (64 hashes) 0.000
```

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
  source    docs  tokens  natural share  chosen weight  tokens sampled   epochs
  web          8     117           0.74           0.60             120      1.0
  books        2      26           0.16           0.30              60      2.3
  code         1      16           0.10           0.10              20      1.2
```

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
  benchmark item:   the baker rises before dawn and the bread is warm when the s...
  8-gram overlap with 1 training document(s)  ->  contaminated: removed
  training set after decontamination: 10 docs
```

Exact n-gram matching is the standard and it is porous — paraphrases, translations and
reformatted versions pass straight through. It is one of the main reasons benchmark numbers are
hard to trust, and it is [chapter 15](../15-evaluation/)'s problem to live with.

---

## 9. What the pipeline buys

Same bigram model, trained on the raw crawl versus the cleaned set, scored on clean held-out text
neither has seen:

```
  trained on raw crawl    374 tokens   held-out loss 3.808 nats
  trained on clean set    145 tokens   held-out loss 3.576 nats
  -> 2.6x fewer tokens, 6% lower loss
```

**Less data, better model.** The duplicates and boilerplate were not merely useless — they
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
