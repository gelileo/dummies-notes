#!/usr/bin/env python3
"""Try many things, keep the best: why that manufactures improvement out of noise.
Run: python3 demo.py"""
import numpy as np
rng = np.random.default_rng(0)

N, p = 200, 0.70
print("=== one honest run vs the best of K identical variants ===")
print(f"   every variant has TRUE accuracy {p}. N = {N} questions. 5000 repetitions.")
print(f"   {'K variants tried':>17}{'mean of reported best':>23}{'inflation (points)':>20}")
for K in (1, 3, 10, 30, 100):
    best = rng.binomial(N, p, (5000, K)).max(1)/N
    print(f"   {K:>17}{best.mean():>23.3f}{(best.mean()-p)*100:>20.1f}")
print("   the more you try, the better the 'winner' looks -- and none of them is better.")

print("\n=== the winner's curse: re-test the winner on fresh data ===")
K = 10
wins_first = []; wins_retest = []
for _ in range(5000):
    scores = rng.binomial(N, p, K)/N; w = scores.argmax()
    wins_first.append(scores[w]); wins_retest.append(rng.binomial(N, p)/N)
print(f"   winner's score on the data used to pick it: {np.mean(wins_first):.3f}")
print(f"   the same winner on a FRESH test set:          {np.mean(wins_retest):.3f}   (back to the truth)")
print("   selection and evaluation on the same data is the bug. hold out a set you touch once.")

print("\n=== the chance of a false 'significant' result grows with the number of tests ===")
alpha = 0.05
print(f"   {'tests':>6}{'P(at least one false positive at 5%)':>40}{'Bonferroni threshold':>22}")
for K in (1, 5, 10, 20, 100):
    print(f"   {K:>6}{1-(1-alpha)**K:>40.3f}{alpha/K:>22.4f}")
print("   run twenty ablations and one will 'pass' at 5% by chance. either divide the threshold by")
print("   the number of tests (Bonferroni) or pre-register the one comparison you care about.")

print("\n=== this is the mechanism behind benchmark inflation in the field ===")
print("   many labs, many checkpoints, many prompts, one leaderboard: the max of a great many noisy")
print("   draws. it is why a fresh, private test set almost always lands below the public number.")
