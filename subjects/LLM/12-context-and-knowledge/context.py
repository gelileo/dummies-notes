#!/usr/bin/env python3
"""Generates context.md from retrieval.py. Run: python3 context.py"""
import io, numpy as np
import retrieval as R
o = io.StringIO(); W = o.write
chunks = R.chunk(R.DOC); bm, tf = R.BM25(chunks), R.TFIDFCosine(chunks)
def rank_of(scores, marker):
    order = np.argsort(-scores); return next((r+1 for r, i in enumerate(order) if marker in chunks[i]), None)

W(f"""# Context and knowledge, traced

Every number here is produced by `retrieval.py`. Run `python3 context.py` to regenerate.

The corpus is real: this curriculum's own field guide, `twelve-ideas-behind-modern-ai.md` —
{len(R.DOC.split()):,} words, cut into **{len(chunks)} chunks** of about 120 words with 30 words of overlap.
Two retrievers index it: **BM25** (keywords) and a **TF-IDF cosine** index, a bag-of-words
stand-in for a learned embedding model with the same geometry and no training.

---

## 1. Ask real questions: where does the answering chunk rank?

```
  {'question':<62}{'BM25':>6}{'TF-IDF':>8}
""")
QS = [("why divide attention scores by the square root of the dimension", "√d"),
      ("how many tokens per parameter did Chinchilla recommend", "20 tokens"),
      ("what does the KV cache store and why is GQA used", "KV cache")]
for q, m in QS: W(f"  {q:<62}{rank_of(bm.score(q), m):>6}{rank_of(tf.score(q), m):>8}\n")
i = R.top(bm.score(QS[0][0]), 1)[0]
W(f"""```

Rank 1 means the chunk that actually answers the question is the top hit. Two of three are; the
`√d` question's answer sits at rank 2 behind a chunk that merely shares vocabulary:

```
  BM25's top hit for the first question (chunk {i}):
  {chunks[i][:120]}...
```

The retrieved chunks are pasted into the prompt and the model answers from them. That is
**retrieval-augmented generation**, in full. And note what a rank of 4 would mean: a top-3
retriever silently misses, and the model answers from nothing. **Retrieval failures are
invisible unless you measure them.**

---

## 2. Keyword versus meaning

```
""")
q = "making the model cheaper to run on a graphics card"
W(f"  Q: {q}\n  the answering section uses 'efficiency', 'quantization', 'GPU' — none of the query's words.\n\n")
for name, idx in (("BM25  ", bm), ("TF-IDF", tf)):
    i = R.top(idx.score(q), 1)[0]; W(f"  {name} top hit (chunk {i:>3}): {chunks[i][:95]}...\n")
W(f"  rank of the hardware section:  BM25 {rank_of(bm.score(q), 'co-design')}   TF-IDF {rank_of(tf.score(q), 'co-design')}\n```\n\n")
W(f"""Both bag-of-words retrievers put the wrong chunk first; the right section survives at rank 2 on
incidental overlap. A **learned embedding model** — trained so that texts about the same thing
point the same way — closes this gap: "cheaper to run" lands near "efficiency" because the
training data put them there. Production systems run both (**hybrid** retrieval) and **rerank**
the union with a cross-encoder that reads query and chunk together.
→ [essentials: TF-IDF and BM25](essentials/tf-idf-and-bm25/)

---

## 3. Chunk size is a knob

```
  {'chunk words':>12}{'chunks':>8}{'answering chunk rank':>22}{'words retrieved (top-3)':>26}
""")
q = QS[0][0]
for size in (40, 120, 400):
    ch = R.chunk(R.DOC, size, size//4); idx = R.BM25(ch); order = np.argsort(-idx.score(q))
    rk = next((r+1 for r, i in enumerate(order) if "√d" in ch[i]), None)
    W(f"  {size:>12}{len(ch):>8}{str(rk):>22}{sum(len(ch[i].split()) for i in order[:3]):>26}\n")
W(f"""```

Small chunks hit precisely and bring little context; large chunks contain the answer somewhere in
a lot of padding the model must read past — and cost ten times the tokens. 100–300 words with
overlap is the usual compromise; splitting on document structure (headings, paragraphs) beats
fixed windows.

---

## 4. Long context or retrieval? Arithmetic

```
""")
dt = int(len(R.DOC.split()) * 1.3)
for calls in (1, 100, 10_000):
    W(f"  {calls:>6} question(s):  whole guide in the prompt ({dt:,} tok) = {dt*calls:>12,}     retrieve 3 chunks (~{int(3*120*1.3)} tok) = {int(3*120*1.3)*calls:>10,}\n")
W(f"""```

For one question, stuffing the document in is simpler and cannot miss. For ten thousand,
retrieval is about 30× cheaper. Prefix caching ([chapter 10](../10-inference-and-decoding/))
narrows the gap when the stuffed document is shared across calls. And a corpus of a million
documents fits in no window: there, retrieval is not a trade-off but the only option. The
honest current answer is *both*: retrieve generously into a large window.

---

## 5. Why long context was hard

```
""")
for T in (8_192, 128_000, 1_000_000):
    W(f"  T = {T:>9,}:  attention scores per layer {T*T:>18,}     KV cache (Llama-3-8B) {2*32*8*128*2*T/1e9:>7.1f} GB per sequence\n")
W(f"""```

Two costs. Attention is quadratic in `T` — tiled away by FlashAttention
([chapter 11](../11-efficiency/)), so it is compute, not memory. The KV cache is linear in `T` and
cannot be tiled away: at a million tokens it is 131 GB for one sequence. And a third, subtler
cost: positional encodings that were never trained past the training length.

---

## 6. Position is an angle, so it can be stretched

RoPE rotates each query and key by an angle proportional to position
([chapter 02](../02-transformer-forward-pass/essentials/rotation-and-rope/)). A crude proxy for
how much two identical tokens still "match" at a given distance:

```
  {'distance':>9}{'trained (scale 1)':>19}{'positions ÷ 4':>15}
""")
d = 128; theta = 1.0 / (10000 ** (np.arange(0, d, 2) / d))
def m(dist, s=1.0): return np.mean(np.cos(theta * dist / s))
for dist in (1, 100, 1000, 8000, 32000): W(f"  {dist:>9,}{m(dist):>19.3f}{m(dist, 4.0):>15.3f}\n")
W(f"""```

A model trained to 8k has seen angles up to `θ·8000`. At 32k the fast-rotating dimension pairs
have spun into territory it never saw. **Divide every position by 4** and 32k looks exactly like 8k
did (compare the two `−0.006` entries) — that is *position interpolation*, and a short fine-tune on
long documents settles the rest. NTK-aware scaling and YaRN stretch the slow and fast frequencies
by different amounts. This is why "trained on 8k, serves 128k" is possible at all.

---

## 7. Finding neighbours among a billion vectors

```
""")
for n in (1_000, 1_000_000, 1_000_000_000): W(f"  {n:>14,} vectors × 1024 dims:  {n*1024:>16,} multiply-adds per query, brute force\n")
W(f"""```

A billion-vector index cannot be scanned per query. Approximate indexes — LSH, IVF, HNSW —
touch a fraction of a percent and return nearly the right neighbours, *because embeddings cluster*.
→ [essentials: nearest-neighbour search](essentials/nearest-neighbour-search/)

---

## 8. Memory across sessions

Nothing above changes the weights. "Memory" in a shipped product is retrieval over past
conversations, notes the model wrote to itself, and summaries — chapters 10 and 12 plus prompt
engineering. It works, and it is not the same as the model *learning*: it forgets what is not
written down, and it cannot notice a pattern across a thousand sessions the way a weight update
would. The gap between the two is one of the open problems.

---

## 9. Invariants

1. **Weights know the training data, frozen at a date. Everything else arrives through the context.**
2. **Retrieval failures are silent.** Measure rank, not vibes.
3. **Keywords and embeddings fail differently.** Run both; rerank.
4. **Chunk size trades precision for context and tokens.** Split on structure where you can.
5. **Stuff for one call, retrieve for ten thousand — and both for real systems.**
6. **Long context costs a linear cache and an extrapolating position code.** RoPE stretches because position is an angle.
7. **ANN works because embeddings cluster.** Recall for speed, tunably.
8. **Memory is retrieval plus prompting**, not learning.
""")
open('context.md', 'w').write(o.getvalue())
print("wrote context.md", len(o.getvalue()), "chars")
