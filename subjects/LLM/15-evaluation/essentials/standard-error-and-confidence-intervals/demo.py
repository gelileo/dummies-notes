#!/usr/bin/env python3
"""How noisy is a benchmark score, and how many questions do you need? Run: python3 demo.py"""
import numpy as np
rng = np.random.default_rng(0)

print("=== an accuracy is a proportion, and a proportion from N trials has a known spread ===")
print("   standard error = sqrt( p (1-p) / N )")
p = 0.7
print(f"   {'N':>7}{'SE (formula)':>14}{'SE (simulated)':>16}{'95% interval':>18}")
for N in (50, 100, 200, 500, 1000, 5000, 10000):
    se = np.sqrt(p*(1-p)/N); sim = (rng.binomial(N, p, 5000)/N).std()
    print(f"   {N:>7}{se:>14.4f}{sim:>16.4f}{f'{p-2*se:.3f} .. {p+2*se:.3f}':>18}")
print("   the interval is roughly +/- 2 SE. quadrupling N halves the SE -- diminishing returns.")

print("\n=== how many questions to trust a difference? ===")
print("   to distinguish a 2-point gap you need the SE of the DIFFERENCE well below 0.02:")
for N in (200, 1000, 5000, 20000):
    se_diff = np.sqrt(2 * p*(1-p)/N)              # two independent scores
    print(f"   N={N:>6}: SE of (acc_a - acc_b) = {se_diff:.4f}   {'gap is ~' + f'{0.02/se_diff:.1f}' + ' SE'}")
print("   a 2-point gap on 200 questions is under one standard error. on 5,000 it is about 3.")

print("\n=== p near 0.5 is the noisiest; p near 0 or 1 is quieter ===")
N = 500
for p_ in (0.5, 0.7, 0.9, 0.98):
    print(f"   p={p_:<5} N={N}: SE {np.sqrt(p_*(1-p_)/N):.4f}")
print("   a saturated benchmark (everyone at 97%) has tiny SE but also tiny gaps -- it stops discriminating.")

print("\n=== what a 95% interval means, checked ===")
hits = 0
for _ in range(5000):
    obs = rng.binomial(200, p)/200; se = np.sqrt(obs*(1-obs)/200)
    hits += (obs - 2*se <= p <= obs + 2*se)
print(f"   of 5000 experiments at N=200, the interval [obs +/- 2 SE] contained the true p in {hits/5000:.1%}")
print("   'the true value is in here 95% of the time' -- not 'there is a 95% chance it is here'.")
