# Inference, traced

Every number here is produced by `decoding.py`. Run `python3 inference.py` to regenerate.

The model is a one-layer causal-attention block with random weights — the mechanics of
generation do not depend on training, and random weights make a small, honest testbed for the
cache and cost experiments. The sampling and cost sections are arithmetic on Llama-3-8B's
published shape and an H100's spec sheet.

---

## 1. The loop

```
  prompt ids   [54, 40, 32, 17, 19, 2, 4, 1]
  greedy       [59, 12, 41, 14, 44]      5 tokens = 5 forward passes
```

Forward pass → distribution over the next token → pick one → append → repeat, until an end token
or a length cap. One forward pass per generated token. That is the entire runtime behaviour of a
language model, and why output tokens are slow and priced above input tokens.

---

## 2. The KV cache

Because of the causal mask, a past token's keys and values can never change. Compute them once
and keep them:

```
  identical output with and without the cache: True

  attention multiply-adds for 40 tokens:   recompute-all 1,138,560    cached  36,736    (31x)

   context T  recompute, per token  cached, per token
          16                 8,192                512
          64               131,072              2,048
         256             2,097,152              8,192
        1024            33,554,432             32,768

  wall clock, 120 tokens:   recompute 0.024s    cached 0.005s
```

Recomputing attention is `O(T²)` per token; the cache makes it `O(T)`. Same output, a
different algorithm. Every serving system does this.

---

## 3. Prefill versus decode

The prompt goes through in **one** batched pass — big matrix multiplies, compute-bound. Each
generated token is a pass with a batch of **one** — tiny multiplies, and every step must read all
the weights to produce a single token:

```
  Llama-3-8B in bf16:  16.1 GB of weights
  one full read at 3.35 TB/s:  4.8 ms
  -> one sequence cannot decode faster than ~209 tokens/s, however fast the arithmetic
  -> batch 32 sequences: the same read serves 32 tokens; throughput ×32, per-user latency ~unchanged
```

Decode is **memory-bound**: the limit is how fast weights can be streamed from memory, not how
fast they can be multiplied. That single fact drives batching, quantization and most of
[chapter 11](../11-efficiency/). Time-to-first-token is prefill; tokens-per-second is decode.

---

## 4. The cache is not free

```
  Llama-3-8B:  32 layers × 2 (K,V) × 8 kv-heads × 128 dims × 2 bytes = 128 KB per token
  at 8,192 tokens of context:   1.07 GB per sequence;  32 concurrent users: 34 GB
  with 32 kv-heads (no GQA):   137 GB
```

That is why grouped-query attention exists ([chapter 02](../02-transformer-forward-pass/)): sharing
keys and values across query heads cuts this fourfold. Paged attention (vLLM) manages the cache in
blocks like virtual memory; prefix caching shares it across requests with a common prompt.

---

## 5. Sampling

The model's last row is a distribution. Turning it into one token is a **decoding choice**:

```
  top-6 tokens: ids [59 36 54 44 17 16]   probs [0.053 0.049 0.042 0.036 0.033 0.032]

  setting               p(top-1)  tokens possible  entropy (bits)
  greedy (T→0)             1.000               12            0.00
  T = 0.5                  0.119               64            4.93
  T = 1.0                  0.053               64            5.65
  T = 2.0                  0.031               64            5.90
  T=1, top-k=5             0.250                5            2.30
  T=1, top-p=0.9           0.059               45            5.31
```

Temperature divides the logits before softmax: below 1 sharpens, above 1 flattens, ranking
unchanged. Top-k and top-p cut the tail and renormalise. **The randomness in a model's output is a
decoding setting, not a property of the model.** → [essentials: sampling](essentials/sampling-from-a-distribution/)

---

## 6. Greedy repeats itself

```
  greedy, 30 tokens:      most common 3-gram appears 7×;  10 distinct tokens of 30
  sampled T=1, 30 tokens: 26 distinct tokens of 30
```

Argmax at every step walks into loops — the most likely continuation of a repeated phrase is
often the phrase again. Sampling breaks the cycle; repetition penalties are the patch when you
need determinism anyway.

---

## 7. Speculative decoding

A small draft model proposes `k` tokens; the big model checks them all in a single pass, accepting
each with probability `q` until the first rejection:

```
      q     k=1     k=3     k=5     k=8
    0.5    1.50    1.88    1.97    2.00
    0.7    1.70    2.53    2.94    3.20
    0.9    1.90    3.44    4.69    6.13
```

Expected tokens per expensive pass. At `q = 0.9` and `k = 5`, 4.7 tokens per pass instead of 1 —
with **the same output distribution**, because rejected drafts are resampled from the big model's
corrected distribution. Free speed, paid for by running a second, small model.
→ [essentials: geometric series](essentials/geometric-series-and-expected-tries/)

---

## 8. Constrained decoding

Set the logits of every token the grammar forbids to `−∞` before softmax:

```
  random logits + grammar mask  ->  {key:val,key:val}
```

The model's preferences choose among the *legal* tokens; illegal output is impossible. This is how
"JSON mode" and function-call formats are guaranteed to parse ([chapter 14](../14-tools-and-agents/)).
It is `exp(−∞) = 0` doing structural work.

---

## 9. Invariants

1. **One forward pass per token.** Output is slow because it is sequential.
2. **The KV cache turns `O(T²)` into `O(T)`**, legal because past keys cannot change. Same output.
3. **Prefill is compute-bound; decode is memory-bound.** Batching is how decode gets cheap.
4. **The cache costs memory** — hence GQA, paging, prefix sharing.
5. **Randomness is a decoding setting.** Temperature reshapes; top-k/top-p truncate.
6. **Greedy loops.** Sample, or penalise repetition.
7. **Speculative decoding gives the same distribution faster.** Draft, verify, geometric payoff.
8. **`−∞` before softmax makes invalid output impossible.** Grammar, not hope.
