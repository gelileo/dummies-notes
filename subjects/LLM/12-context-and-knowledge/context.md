# Context and knowledge, traced

Every number here is produced by `retrieval.py`. Run `python3 context.py` to regenerate.

The corpus is real: this curriculum's own field guide, `twelve-ideas-behind-modern-ai.md` —
10,877 words, cut into **121 chunks** of about 120 words with 30 words of overlap.
Two retrievers index it: **BM25** (keywords) and a **TF-IDF cosine** index, a bag-of-words
stand-in for a learned embedding model with the same geometry and no training.

---

## 1. Ask real questions: where does the answering chunk rank?

```
  question                                                        BM25  TF-IDF
  why divide attention scores by the square root of the dimension     2       2
  how many tokens per parameter did Chinchilla recommend             1       1
  what does the KV cache store and why is GQA used                   1       1
```

Rank 1 means the chunk that actually answers the question is the top hit. Two of three are; the
`√d` question's answer sits at rank 2 behind a chunk that merely shares vocabulary:

```
  BM25's top hit for the first question (chunk 99):
  synthesis of the whole book fail. In practice teams combine them: retrieve generously into a large context, and cache th...
```

The retrieved chunks are pasted into the prompt and the model answers from them. That is
**retrieval-augmented generation**, in full. And note what a rank of 4 would mean: a top-3
retriever silently misses, and the model answers from nothing. **Retrieval failures are
invisible unless you measure them.**

---

## 2. Keyword versus meaning

```
  Q: making the model cheaper to run on a graphics card
  the answering section uses 'efficiency', 'quantization', 'GPU' — none of the query's words.

  BM25   top hit (chunk   9): in that direction. Repeat. The “learning rate” is the step size: too big and training oscillate...
  TF-IDF top hit (chunk   9): in that direction. Repeat. The “learning rate” is the step size: too big and training oscillate...
  rank of the hardware section:  BM25 2   TF-IDF 2
```

Both bag-of-words retrievers put the wrong chunk first; the right section survives at rank 2 on
incidental overlap. A **learned embedding model** — trained so that texts about the same thing
point the same way — closes this gap: "cheaper to run" lands near "efficiency" because the
training data put them there. Production systems run both (**hybrid** retrieval) and **rerank**
the union with a cross-encoder that reads query and chunk together.
→ [essentials: TF-IDF and BM25](essentials/tf-idf-and-bm25/)

---

## 3. Chunk size is a knob

```
   chunk words  chunks  answering chunk rank   words retrieved (top-3)
            40     363                     2                       120
           120     121                     2                       360
           400      37                     1                      1200
```

Small chunks hit precisely and bring little context; large chunks contain the answer somewhere in
a lot of padding the model must read past — and cost ten times the tokens. 100–300 words with
overlap is the usual compromise; splitting on document structure (headings, paragraphs) beats
fixed windows.

---

## 4. Long context or retrieval? Arithmetic

```
       1 question(s):  whole guide in the prompt (14,140 tok) =       14,140     retrieve 3 chunks (~468 tok) =        468
     100 question(s):  whole guide in the prompt (14,140 tok) =    1,414,000     retrieve 3 chunks (~468 tok) =     46,800
   10000 question(s):  whole guide in the prompt (14,140 tok) =  141,400,000     retrieve 3 chunks (~468 tok) =  4,680,000
```

For one question, stuffing the document in is simpler and cannot miss. For ten thousand,
retrieval is about 30× cheaper. Prefix caching ([chapter 10](../10-inference-and-decoding/))
narrows the gap when the stuffed document is shared across calls. And a corpus of a million
documents fits in no window: there, retrieval is not a trade-off but the only option. The
honest current answer is *both*: retrieve generously into a large window.

---

## 5. Why long context was hard

```
  T =     8,192:  attention scores per layer         67,108,864     KV cache (Llama-3-8B)     1.1 GB per sequence
  T =   128,000:  attention scores per layer     16,384,000,000     KV cache (Llama-3-8B)    16.8 GB per sequence
  T = 1,000,000:  attention scores per layer  1,000,000,000,000     KV cache (Llama-3-8B)   131.1 GB per sequence
```

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
   distance  trained (scale 1)  positions ÷ 4
          1              0.970          0.998
        100              0.477          0.588
      1,000              0.159          0.307
      8,000             -0.006          0.029
     32,000              0.140         -0.006
```

A model trained to 8k has seen angles up to `θ·8000`. At 32k the fast-rotating dimension pairs
have spun into territory it never saw. **Divide every position by 4** and 32k looks exactly like 8k
did (compare the two `−0.006` entries) — that is *position interpolation*, and a short fine-tune on
long documents settles the rest. NTK-aware scaling and YaRN stretch the slow and fast frequencies
by different amounts. This is why "trained on 8k, serves 128k" is possible at all.

---

## 7. Finding neighbours among a billion vectors

```
           1,000 vectors × 1024 dims:         1,024,000 multiply-adds per query, brute force
       1,000,000 vectors × 1024 dims:     1,024,000,000 multiply-adds per query, brute force
   1,000,000,000 vectors × 1024 dims:  1,024,000,000,000 multiply-adds per query, brute force
```

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
