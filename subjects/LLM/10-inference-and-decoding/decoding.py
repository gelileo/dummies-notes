#!/usr/bin/env python3
"""Inference and decoding, measured. A one-layer causal-attention model (random weights --
the mechanics do not depend on training) for the KV-cache and prefill/decode experiments,
plus exact arithmetic for sampling, speculative decoding, cache size and constrained output.
numpy. Run: python3 decoding.py
"""
import numpy as np, time
rng = np.random.default_rng(0)

# ------------------------------------------------------------------ a one-layer attention model
V, D, H = 64, 32, 4; DH = D // H
Wq, Wk, Wv, Wo = (rng.normal(0, .1, (D, D)) for _ in range(4)); E = rng.normal(0, .3, (V, D)); Wlm = rng.normal(0, .5, (D, V))   # scaled so the distribution is peaked enough to see sampling effects
def softmax(z): e = np.exp(z - z.max(-1, keepdims=True)); return e / e.sum(-1, keepdims=True)

def forward_full(ids):
    """Recompute attention for ALL positions from scratch. Returns logits for the last position
    and the number of multiply-adds spent in the attention score computation."""
    x = E[ids]; T = len(ids)
    q, k, v = x @ Wq, x @ Wk, x @ Wv
    ops = 0; outs = []
    for h in range(H):
        qh, kh, vh = q[:, h*DH:(h+1)*DH], k[:, h*DH:(h+1)*DH], v[:, h*DH:(h+1)*DH]
        s = qh @ kh.T / np.sqrt(DH); ops += T * T * DH
        s += np.triu(np.full((T, T), -np.inf), 1)
        outs.append(softmax(s) @ vh)
    y = np.concatenate(outs, 1) @ Wo + x
    return y[-1] @ Wlm, ops

class Cached:
    """Keep K and V of every past position; each new token attends over the cache."""
    def __init__(self): self.K = np.zeros((0, D)); self.Vv = np.zeros((0, D))
    def step(self, tok):
        x = E[tok][None]; q = x @ Wq
        self.K = np.vstack([self.K, x @ Wk]); self.Vv = np.vstack([self.Vv, x @ Wv])
        T = len(self.K); ops = 0; outs = []
        for h in range(H):
            s = q[:, h*DH:(h+1)*DH] @ self.K[:, h*DH:(h+1)*DH].T / np.sqrt(DH); ops += T * DH
            outs.append(softmax(s) @ self.Vv[:, h*DH:(h+1)*DH])
        y = np.concatenate(outs, 1) @ Wo + x
        return (y @ Wlm)[0], ops

def generate(ids, n, cached=True, pick=lambda lg: int(lg.argmax())):
    ids = list(ids); ops = 0
    if cached:
        c = Cached()
        for t in ids[:-1]: c.step(t)                       # prefill
        lg, o = c.step(ids[-1]); ops += o
        for _ in range(n):
            nxt = pick(lg); ids.append(nxt); lg, o = c.step(nxt); ops += o
    else:
        for _ in range(n):
            lg, o = forward_full(np.array(ids)); ops += o; ids.append(pick(lg))
    return ids, ops

if __name__ == "__main__":
    np.set_printoptions(precision=3, suppress=True)
    prompt = [int(t) for t in rng.integers(0, V, 8)]

    print("=== 1. the loop: one forward pass per generated token ===")
    out, _ = generate(prompt, 5, cached=False)
    print(f"   prompt ids {prompt}")
    print(f"   greedy: {[int(t) for t in out[len(prompt):]]}   (5 tokens = 5 forward passes; each sees everything before it)")

    print("\n=== 2. with and without a KV cache: same output, different cost ===")
    a, ops_full = generate(prompt, 40, cached=False); b, ops_cache = generate(prompt, 40, cached=True)
    print(f"   identical output: {a == b}")
    print(f"   attention-score multiply-adds, 40 tokens:  recompute-all {ops_full:>9,}   cached {ops_cache:>7,}   ratio {ops_full/ops_cache:.1f}x")
    print(f"   {'context T':>10}{'recompute per token':>22}{'cached per token':>18}")
    for T in (16, 64, 256, 1024):
        print(f"   {T:>10}{H*T*T*DH:>22,}{H*T*DH:>18,}")
    print("   recomputing is O(T^2) per token; the cache makes it O(T). legal because of the causal")
    print("   mask: a past token's K and V can never change, so they are computed once and kept.")
    t0 = time.perf_counter(); generate(prompt, 120, cached=False); t1 = time.perf_counter(); generate(prompt, 120, cached=True); t2 = time.perf_counter()
    print(f"   wall clock, 120 tokens: recompute {t1-t0:.3f}s   cached {t2-t1:.3f}s")

    print("\n=== 3. prefill vs decode ===")
    print("   prefill: the prompt's T tokens go through in ONE batched pass -- big matmuls, compute-bound.")
    print("   decode:  each new token is a pass with a batch of ONE -- tiny matmuls, memory-bound:")
    print("            every step must read all the weights to produce a single token.")
    N_params, bytes_per = 8.03e9, 2
    for hbm in (3.35e12,):   # H100 memory bandwidth, bytes/s
        t_read = N_params * bytes_per / hbm
        print(f"   Llama-3-8B in bf16 = {N_params*bytes_per/1e9:.1f} GB of weights; reading them once at {hbm/1e12:.2f} TB/s takes {t_read*1000:.1f} ms")
        print(f"   -> a single-user decode cannot exceed ~{1/t_read:.0f} tokens/s no matter how fast the arithmetic is.")
        print(f"   -> batch 32 users: the same weight read serves 32 tokens. throughput up 32x, latency barely changes.")

    print("\n=== 4. the KV cache is not free: its size ===")
    L, nkv, dh, T = 32, 8, 128, 8192
    per_tok = 2 * L * nkv * dh * bytes_per
    print(f"   Llama-3-8B: {L} layers x 2 (K,V) x {nkv} kv-heads x {dh} dims x {bytes_per} bytes = {per_tok/1024:.0f} KB per token")
    print(f"   at {T:,} tokens of context: {per_tok*T/1e9:.2f} GB per sequence.  32 concurrent users: {per_tok*T*32/1e9:.0f} GB")
    print(f"   with 32 kv-heads instead of 8 (no GQA) it would be {per_tok*T*32*4/1e9:.0f} GB. that is why GQA exists.")

    print("\n=== 5. sampling: turning the last row into one token ===")
    lg, _ = forward_full(np.array(prompt)); p = softmax(lg)
    top = np.argsort(-p)[:6]
    print(f"   top-6 of the distribution: ids {top}  probs {p[top]}")
    def sample(logits, T=1.0, top_k=None, top_p=None):
        z = logits / T; pr = softmax(z)
        if top_k: cut = np.sort(pr)[-top_k]; pr = np.where(pr >= cut, pr, 0)
        if top_p:
            order = np.argsort(-pr); cum = np.cumsum(pr[order]); keep = order[cum - pr[order] < top_p]
            mask = np.zeros_like(pr); mask[keep] = 1; pr = pr * mask
        pr /= pr.sum(); return pr
    print(f"   {'setting':<22}{'p(top-1)':>10}{'tokens with p>0':>17}{'entropy (bits)':>16}")
    for name, kw in (("greedy (T->0)", dict(T=1e-3)), ("T=0.5", dict(T=0.5)), ("T=1.0", dict(T=1.0)), ("T=2.0", dict(T=2.0)),
                     ("T=1, top-k=5", dict(top_k=5)), ("T=1, top-p=0.9", dict(top_p=0.9))):
        pr = sample(lg, **kw); nz = pr[pr > 0]
        print(f"   {name:<22}{pr.max():>10.3f}{int((pr>0).sum()):>17}{-(nz*np.log2(nz)).sum():>16.2f}")
    print("   temperature divides the logits before softmax: <1 sharpens, >1 flattens. top-k and top-p")
    print("   cut the tail, then renormalise. randomness in outputs is a DECODING choice, not a model one.")

    print("\n=== 6. greedy repeats itself ===")
    g, _ = generate(prompt, 30, cached=True)
    tail = g[len(prompt):]
    from collections import Counter
    c = Counter(tuple(tail[i:i+3]) for i in range(len(tail)-2))
    print(f"   greedy, 30 tokens: most common 3-gram appears {c.most_common(1)[0][1]}x; distinct tokens {len(set(tail))}/30")
    s_, _ = generate(prompt, 30, cached=True, pick=lambda lg: int(rng.choice(V, p=softmax(lg))))
    tail2 = s_[len(prompt):]
    print(f"   sampled T=1, 30 tokens: distinct tokens {len(set(tail2))}/30")
    print("   argmax at every step walks into loops; sampling breaks them. repetition penalties are the patch.")

    print("\n=== 7. speculative decoding: a small draft proposes, the big model verifies in one pass ===")
    print("   if the draft's tokens are accepted with probability q each, k drafted tokens yield")
    print("   on average (1 - q^(k+1)) / (1 - q) accepted tokens per big-model pass:")
    print(f"   {'q':>6}" + "".join(f"{f'k={k}':>8}" for k in (1, 3, 5, 8)))
    for q in (0.5, 0.7, 0.9):
        print(f"   {q:>6.1f}" + "".join(f"{(1-q**(k+1))/(1-q):>8.2f}" for k in (1, 3, 5, 8)))
    print("   at q=0.9, k=5 -> 4.7 tokens per expensive pass instead of 1. same output distribution,")
    print("   because rejected drafts are resampled from the big model's corrected distribution.")

    print("\n=== 8. constrained decoding: mask the logits so the output MUST parse ===")
    # a toy grammar: after '{' must come a key token; after a key, ':'; after ':', a value; after a value, ',' or '}'
    toks = {"{": 0, "}": 1, ":": 2, ",": 3, "key": 4, "val": 5}
    allowed = {None: ["{"], "{": ["key"], "key": [":"], ":": ["val"], "val": [",", "}"], ",": ["key"], "}": []}
    out, prev = [], None
    for _ in range(9):
        lg = rng.normal(size=len(toks))
        mask = np.full(len(toks), -np.inf)
        for t in allowed[prev]: mask[toks[t]] = 0
        if not allowed[prev]: break
        pr = softmax(lg + mask); tok = list(toks)[int(rng.choice(len(toks), p=pr))]
        out.append(tok); prev = tok
    print(f"   random logits + grammar mask -> {''.join(out)}")
    print("   every step, tokens the grammar forbids get -inf before softmax. the model's preferences")
    print("   choose among the legal tokens; illegal output is impossible. this is how 'JSON mode' works.")
