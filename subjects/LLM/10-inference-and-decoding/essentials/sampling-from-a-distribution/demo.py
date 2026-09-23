#!/usr/bin/env python3
"""How one token is actually drawn from a probability distribution, and what temperature,
top-k and top-p do to that distribution. Run: python3 demo.py"""
import numpy as np
rng = np.random.default_rng(0)
def softmax(z): e = np.exp(z - z.max()); return e / e.sum()

print("=== drawing from a distribution: the cumulative-sum trick ===")
p = np.array([0.5, 0.3, 0.15, 0.05]); cum = np.cumsum(p)
print(f"   probabilities {p}")
print(f"   cumulative    {cum}")
print("   draw u uniformly in [0,1); the token is the first index whose cumulative sum exceeds u:")
for u in (0.12, 0.61, 0.83, 0.97):
    print(f"      u = {u:.2f} -> token {int(np.searchsorted(cum, u, side='right'))}")
draws = [int(np.searchsorted(cum, rng.random(), side='right')) for _ in range(100000)]
print(f"   100,000 draws: frequencies {np.round(np.bincount(draws)/1e5, 3)}   (match p)")
print("   that is all 'sampling' is: one uniform random number and a lookup.")

print("\n=== temperature: divide the logits BEFORE softmax ===")
logits = np.array([3.0, 2.0, 1.0, 0.0, -1.0])
print(f"   logits {logits}")
print(f"   {'T':>6}{'probabilities':>44}{'p(top)':>9}")
for T in (0.2, 0.5, 1.0, 2.0, 5.0):
    q = softmax(logits / T); print(f"   {T:>6}{str(np.round(q, 3)):>44}{q.max():>9.3f}")
print("   T -> 0 approaches argmax (greedy). T -> inf approaches uniform. it rescales the gaps")
print("   between logits, so it changes confidence, not ranking.")

print("\n=== top-k: keep the k most likely, renormalise ===")
q = softmax(logits); k = 2
cut = np.sort(q)[-k]; qk = np.where(q >= cut, q, 0); qk /= qk.sum()
print(f"   full      {np.round(q, 3)}")
print(f"   top-2     {np.round(qk, 3)}   (three tokens can never be chosen)")

print("\n=== top-p (nucleus): keep the smallest set whose probability adds to p, renormalise ===")
order = np.argsort(-q); cum = np.cumsum(q[order])
for top_p in (0.5, 0.9, 0.99):
    keep = order[cum - q[order] < top_p]
    qp = np.zeros_like(q); qp[keep] = q[keep]; qp /= qp.sum()
    print(f"   top-p={top_p:<5} keeps {len(keep)} tokens -> {np.round(qp, 3)}")
print("   top-k fixes the COUNT; top-p fixes the MASS. when the model is confident top-p keeps")
print("   few tokens; when it is unsure it keeps many. that adaptivity is why top-p is the default.")

print("\n=== the order of operations matters ===")
print("   1. logits / T   2. softmax   3. truncate (top-k / top-p)   4. renormalise   5. draw")
print("   temperature changes which tokens survive truncation; do it first.")
