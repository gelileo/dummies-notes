#!/usr/bin/env python3
"""Expected value, Monte Carlo estimates, and why a baseline helps. Run: python3 demo.py"""
import numpy as np
rng = np.random.default_rng(0)

vals = np.array([1.0, 2.0, 3.0, 4.5, 5.0, 5.5, 4.0, 2.0])
p = np.array([0.05, 0.05, 0.1, 0.2, 0.25, 0.2, 0.1, 0.05])
print("=== expected value: the probability-weighted average ===")
print(f"   outcomes      {vals}")
print(f"   probabilities {p}   (sum {p.sum():.2f})")
print(f"   E[value] = sum(p * value) = {p @ vals:.3f}")
print("   'if you drew from this distribution forever, this is the average you would see.'")

print("\n=== you rarely know p exactly -- so you SAMPLE and average (Monte Carlo) ===")
truth = p @ vals
print(f"   {'samples n':>10}{'estimate':>10}{'error':>9}{'typical error over 500 trials':>32}")
for n in (1, 4, 16, 64, 256, 1024):
    ests = [vals[rng.choice(8, n, p=p)].mean() for _ in range(500)]
    print(f"   {n:>10}{ests[0]:>10.3f}{abs(ests[0]-truth):>9.3f}{np.std(ests):>32.3f}")
print("   the estimate is unbiased at any n, and its scatter shrinks like 1/sqrt(n).")
print("   a batch of 16 responses in RLHF is a Monte Carlo estimate with n=16. noisy.")

print("\n=== variance reduction: subtract a baseline ===")
print("   estimating E[value * f] where f is something else we care about (a gradient, say).")
print("   subtract a constant b from value first: E[(value - b) * f] = E[value*f] - b*E[f].")
print("   if E[f] = 0, the baseline changes NOTHING in expectation -- but can cut the scatter.")
f = lambda idx: (np.eye(8)[idx] - p)          # score-function-like: E over p is exactly 0
for b_name, b in (("no baseline (b=0)", 0.0), ("b = mean value", truth)):
    ests = []
    for _ in range(2000):
        idx = rng.choice(8, 16, p=p)
        ests.append(((vals[idx] - b)[:, None] * f(idx)).mean(0))
    ests = np.array(ests)
    print(f"   {b_name:<20} mean {np.round(ests.mean(0), 3)}")
    print(f"   {'':<20} scatter {np.sqrt(((ests - ests.mean(0))**2).sum(1)).mean():.3f}")
print("   same mean, smaller scatter. that is exactly what the 'advantage' in policy")
print("   gradients does: reward minus a baseline, with the baseline's gradient being zero.")
