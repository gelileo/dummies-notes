#!/usr/bin/env python3
"""Generates inference.md from decoding.py. Run: python3 inference.py"""
import io, time, numpy as np
from collections import Counter
import decoding as D
o = io.StringIO(); W = o.write
np.set_printoptions(precision=3, suppress=True)
D.rng = np.random.default_rng(0); prompt = [int(t) for t in D.rng.integers(0, D.V, 8)]

W(f"""# Inference, traced

Every number here is produced by `decoding.py`. Run `python3 inference.py` to regenerate.

The model is a one-layer causal-attention block with random weights — the mechanics of
generation do not depend on training, and random weights make a small, honest testbed for the
cache and cost experiments. The sampling and cost sections are arithmetic on Llama-3-8B's
published shape and an H100's spec sheet.

---

## 1. The loop

```
""")
out, _ = D.generate(prompt, 5, cached=False)
W(f"  prompt ids   {prompt}\n  greedy       {[int(t) for t in out[len(prompt):]]}      5 tokens = 5 forward passes\n```\n\n")
W(f"""Forward pass → distribution over the next token → pick one → append → repeat, until an end token
or a length cap. One forward pass per generated token. That is the entire runtime behaviour of a
language model, and why output tokens are slow and priced above input tokens.

---

## 2. The KV cache

Because of the causal mask, a past token's keys and values can never change. Compute them once
and keep them:

```
""")
a, ops_full = D.generate(prompt, 40, cached=False); b, ops_cache = D.generate(prompt, 40, cached=True)
W(f"  identical output with and without the cache: {a == b}\n\n")
W(f"  attention multiply-adds for 40 tokens:   recompute-all {ops_full:>9,}    cached {ops_cache:>7,}    ({ops_full/ops_cache:.0f}x)\n\n")
W(f"  {'context T':>10}{'recompute, per token':>22}{'cached, per token':>19}\n")
for T in (16, 64, 256, 1024): W(f"  {T:>10}{D.H*T*T*D.DH:>22,}{D.H*T*D.DH:>19,}\n")
t0 = time.perf_counter(); D.generate(prompt, 120, cached=False); t1 = time.perf_counter(); D.generate(prompt, 120, cached=True); t2 = time.perf_counter()
W(f"\n  wall clock, 120 tokens:   recompute {t1-t0:.3f}s    cached {t2-t1:.3f}s\n```\n\n")
W(f"""Recomputing attention is `O(T²)` per token; the cache makes it `O(T)`. Same output, a
different algorithm. Every serving system does this.

---

## 3. Prefill versus decode

The prompt goes through in **one** batched pass — big matrix multiplies, compute-bound. Each
generated token is a pass with a batch of **one** — tiny multiplies, and every step must read all
the weights to produce a single token:

```
""")
N_params, bytes_per, hbm = 8.03e9, 2, 3.35e12; t_read = N_params*bytes_per/hbm
W(f"  Llama-3-8B in bf16:  {N_params*bytes_per/1e9:.1f} GB of weights\n  one full read at {hbm/1e12:.2f} TB/s:  {t_read*1e3:.1f} ms\n  -> one sequence cannot decode faster than ~{1/t_read:.0f} tokens/s, however fast the arithmetic\n  -> batch 32 sequences: the same read serves 32 tokens; throughput ×32, per-user latency ~unchanged\n```\n\n")
W(f"""Decode is **memory-bound**: the limit is how fast weights can be streamed from memory, not how
fast they can be multiplied. That single fact drives batching, quantization and most of
[chapter 11](../11-efficiency/). Time-to-first-token is prefill; tokens-per-second is decode.

---

## 4. The cache is not free

```
""")
L, nkv, dh, T = 32, 8, 128, 8192; per_tok = 2*L*nkv*dh*bytes_per
W(f"  Llama-3-8B:  {L} layers × 2 (K,V) × {nkv} kv-heads × {dh} dims × {bytes_per} bytes = {per_tok/1024:.0f} KB per token\n")
W(f"  at {T:,} tokens of context:   {per_tok*T/1e9:.2f} GB per sequence;  32 concurrent users: {per_tok*T*32/1e9:.0f} GB\n")
W(f"  with 32 kv-heads (no GQA):   {per_tok*T*32*4/1e9:.0f} GB\n```\n\n")
W(f"""That is why grouped-query attention exists ([chapter 02](../02-transformer-forward-pass/)): sharing
keys and values across query heads cuts this fourfold. Paged attention (vLLM) manages the cache in
blocks like virtual memory; prefix caching shares it across requests with a common prompt.

---

## 5. Sampling

The model's last row is a distribution. Turning it into one token is a **decoding choice**:

```
""")
lg, _ = D.forward_full(np.array(prompt)); p = D.softmax(lg); top = np.argsort(-p)[:6]
W(f"  top-6 tokens: ids {top}   probs {p[top]}\n\n")
def sample(logits, T=1.0, top_k=None, top_p=None):
    z = logits / T; pr = D.softmax(z)
    if top_k: cut = np.sort(pr)[-top_k]; pr = np.where(pr >= cut, pr, 0)
    if top_p:
        order = np.argsort(-pr); cum = np.cumsum(pr[order]); keep = order[cum - pr[order] < top_p]
        mask = np.zeros_like(pr); mask[keep] = 1; pr = pr * mask
    return pr / pr.sum()
W(f"  {'setting':<20}{'p(top-1)':>10}{'tokens possible':>17}{'entropy (bits)':>16}\n")
for name, kw in (("greedy (T→0)", dict(T=1e-3)), ("T = 0.5", dict(T=0.5)), ("T = 1.0", dict(T=1.0)), ("T = 2.0", dict(T=2.0)), ("T=1, top-k=5", dict(top_k=5)), ("T=1, top-p=0.9", dict(top_p=0.9))):
    pr = sample(lg, **kw); nz = pr[pr > 0]
    W(f"  {name:<20}{pr.max():>10.3f}{int((pr>0).sum()):>17}{-(nz*np.log2(nz)).sum():>16.2f}\n")
W(f"""```

Temperature divides the logits before softmax: below 1 sharpens, above 1 flattens, ranking
unchanged. Top-k and top-p cut the tail and renormalise. **The randomness in a model's output is a
decoding setting, not a property of the model.** → [essentials: sampling](essentials/sampling-from-a-distribution/)

---

## 6. Greedy repeats itself

```
""")
D.rng = np.random.default_rng(1)
g, _ = D.generate(prompt, 30, cached=True); tail = g[len(prompt):]
c = Counter(tuple(tail[i:i+3]) for i in range(len(tail)-2))
s_, _ = D.generate(prompt, 30, cached=True, pick=lambda lg: int(D.rng.choice(D.V, p=D.softmax(lg)))); tail2 = s_[len(prompt):]
W(f"  greedy, 30 tokens:      most common 3-gram appears {c.most_common(1)[0][1]}×;  {len(set(tail))} distinct tokens of 30\n")
W(f"  sampled T=1, 30 tokens: {len(set(tail2))} distinct tokens of 30\n```\n\n")
W(f"""Argmax at every step walks into loops — the most likely continuation of a repeated phrase is
often the phrase again. Sampling breaks the cycle; repetition penalties are the patch when you
need determinism anyway.

---

## 7. Speculative decoding

A small draft model proposes `k` tokens; the big model checks them all in a single pass, accepting
each with probability `q` until the first rejection:

```
  {'q':>5}""" + "".join(f"{f'k={k}':>8}" for k in (1, 3, 5, 8)) + "\n")
for q in (0.5, 0.7, 0.9): W(f"  {q:>5.1f}" + "".join(f"{(1-q**(k+1))/(1-q):>8.2f}" for k in (1, 3, 5, 8)) + "\n")
W(f"""```

Expected tokens per expensive pass. At `q = 0.9` and `k = 5`, 4.7 tokens per pass instead of 1 —
with **the same output distribution**, because rejected drafts are resampled from the big model's
corrected distribution. Free speed, paid for by running a second, small model.
→ [essentials: geometric series](essentials/geometric-series-and-expected-tries/)

---

## 8. Constrained decoding

Set the logits of every token the grammar forbids to `−∞` before softmax:

```
""")
D.rng = np.random.default_rng(2)
toks = {"{": 0, "}": 1, ":": 2, ",": 3, "key": 4, "val": 5}
allowed = {None: ["{"], "{": ["key"], "key": [":"], ":": ["val"], "val": [",", "}"], ",": ["key"], "}": []}
outl, prev = [], None
for _ in range(9):
    if not allowed[prev]: break
    lg2 = D.rng.normal(size=len(toks)); mask = np.full(len(toks), -np.inf)
    for t in allowed[prev]: mask[toks[t]] = 0
    pr = D.softmax(lg2 + mask); tok = list(toks)[int(D.rng.choice(len(toks), p=pr))]; outl.append(tok); prev = tok
W(f"  random logits + grammar mask  ->  {''.join(outl)}\n```\n\n")
W(f"""The model's preferences choose among the *legal* tokens; illegal output is impossible. This is how
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
""")
open('inference.md', 'w').write(o.getvalue())
print("wrote inference.md", len(o.getvalue()), "chars")
