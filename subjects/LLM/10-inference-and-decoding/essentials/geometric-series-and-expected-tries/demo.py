#!/usr/bin/env python3
"""Geometric series and expected counts -- the arithmetic behind speculative decoding.
Run: python3 demo.py"""
import numpy as np
rng = np.random.default_rng(0)

print("=== a geometric series: 1 + q + q^2 + ... ===")
for q in (0.5, 0.9):
    partial = [sum(q**i for i in range(n+1)) for n in (0, 1, 2, 5, 10, 50)]
    print(f"   q={q}: partial sums {np.round(partial, 3)}   limit 1/(1-q) = {1/(1-q):.3f}")
print("   each term is the last times q. the sum of the first n+1 terms is (1 - q^(n+1)) / (1 - q),")
print("   and it converges to 1/(1-q) when q < 1.")

print("\n=== expected number of accepted draft tokens ===")
print("   a draft model proposes k tokens; the big model checks them in order and accepts each")
print("   with probability q, stopping at the first rejection (and supplying its own token there).")
print("   accepted count = 1 + q + q^2 + ... + q^k in expectation  -- a geometric series.")
print(f"   {'q':>6}" + "".join(f"{f'k={k}':>8}" for k in (1, 2, 4, 8, 16)))
for q in (0.5, 0.7, 0.9, 0.95):
    print(f"   {q:>6.2f}" + "".join(f"{(1-q**(k+1))/(1-q):>8.2f}" for k in (1, 2, 4, 8, 16)))
print("   tokens per expensive pass. at q=0.9 drafting 8 gives 6.5 -- but drafting 16 gives only")
print("   8.1, and the draft itself costs something: diminishing returns set the best k.")

print("\n=== check by simulation ===")
q, k = 0.9, 5
sims = []
for _ in range(20000):
    n = 0
    while n < k and rng.random() < q: n += 1
    sims.append(n + 1)                          # +1: the big model always emits one token itself
print(f"   q={q}, k={k}: simulated mean {np.mean(sims):.3f}   formula {(1-q**(k+1))/(1-q):.3f}")

print("\n=== the same series is the expected number of tries until a success ===")
for p in (0.5, 0.1, 0.01):
    tries = [next(i for i in range(1, 10**6) if rng.random() < p) for _ in range(5000)]
    print(f"   success probability {p:<5}: expected tries 1/p = {1/p:>6.1f}   simulated {np.mean(tries):>6.1f}")
print("   'how many samples until one passes the verifier' is this number (chapter 09).")
