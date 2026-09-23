#!/usr/bin/env python3
"""p^k, 1-(1-p)^n, and the binomial: the arithmetic of multi-step tasks and repeated tries.
Run: python3 demo.py"""
from math import comb

print("=== a task with k steps that must ALL succeed: p^k ===")
print(f"   {'per-step p':>11}" + "".join(f"{f'k={k}':>9}" for k in (1, 2, 5, 10, 20, 50)))
for p in (0.90, 0.95, 0.99, 0.999):
    print(f"   {p:>11.3f}" + "".join(f"{p**k:>9.3f}" for k in (1, 2, 5, 10, 20, 50)))
print("   independent steps multiply. at 90% per step, a 20-step task succeeds 12% of the time.")
print("   at 99.9% it is 98%. long chains demand very high per-step reliability.")

print("\n=== n independent tries, and you need just ONE success: 1 - (1-p)^n ===")
print(f"   {'p':>6}" + "".join(f"{f'n={n}':>9}" for n in (1, 2, 5, 10, 20, 100)))
for p in (0.01, 0.1, 0.3, 0.6):
    print(f"   {p:>6.2f}" + "".join(f"{1-(1-p)**n:>9.3f}" for n in (1, 2, 5, 10, 20, 100)))
print("   the mirror image: failures multiply, so even p=0.01 reaches 63% with 100 tries.")
print("   this is best-of-n with a verifier: sample many, keep any that checks out.")

print("\n=== n tries, and you need a MAJORITY to agree: the binomial ===")
def majority(p, n): return sum(comb(n, k) * p**k * (1-p)**(n-k) for k in range(n//2 + 1, n + 1))
print(f"   {'p':>6}" + "".join(f"{f'n={n}':>9}" for n in (1, 3, 5, 11, 21, 101)))
for p in (0.3, 0.45, 0.55, 0.7, 0.9):
    print(f"   {p:>6.2f}" + "".join(f"{majority(p, n):>9.3f}" for n in (1, 3, 5, 11, 21, 101)))
print("   above 0.5, more votes sharpen toward certainty; below 0.5, more votes sharpen toward")
print("   certain FAILURE. majority voting amplifies whatever side of 50% you are on.")
print("   (worst case for voting: every wrong answer is the same wrong answer.)")

print("\n=== why the binomial: counting the ways ===")
n, k, p = 5, 3, 0.6
print(f"   P(exactly {k} of {n} succeed) = C({n},{k}) * p^{k} * (1-p)^{n-k}")
print(f"                              = {comb(n,k)} * {p**k:.4f} * {(1-p)**(n-k):.4f} = {comb(n,k)*p**k*(1-p)**(n-k):.4f}")
print(f"   C({n},{k}) = {comb(n,k)} is the number of ways to choose which {k} of the {n} succeed.")
print("   'majority' just sums this over every k above n/2.")
