#!/usr/bin/env python3
"""Mapping floats to a few integer levels: scale, round, clip, and where the error comes from.
Run: python3 demo.py"""
import numpy as np
rng = np.random.default_rng(0)

print("=== the recipe: scale so the biggest value fits, round to an integer, store the scale ===")
w = np.array([0.31, -0.12, 0.05, -0.44, 0.20, 0.02, -0.27, 0.09])
bits = 4; levels = 2**(bits-1) - 1
scale = np.abs(w).max() / levels
q = np.round(w / scale).clip(-levels, levels).astype(int)
back = q * scale
print(f"   weights      {w}")
print(f"   int{bits}: levels -{levels}..{levels}, scale = max|w|/{levels} = {scale:.4f}")
print(f"   integers     {q}")
print(f"   dequantised  {np.round(back, 3)}")
print(f"   error        {np.round(back - w, 3)}   (max possible: scale/2 = {scale/2:.4f})")
print("   storage: 8 x 4 bits + one 16-bit scale = 48 bits, vs 8 x 16 = 128 bits. 2.7x smaller.")

print("\n=== the error is at most half a step, and the step is set by the LARGEST value ===")
for b in (8, 4, 3, 2):
    lv = 2**(b-1) - 1; sc = np.abs(w).max()/lv
    print(f"   int{b}: {2*lv+1:>4} levels, step {sc:.4f}, max error {sc/2:.4f}  ({sc/2/np.abs(w).mean():.0%} of a typical weight)")

print("\n=== one outlier ruins everyone's precision ===")
w2 = w.copy(); w2[3] = -3.5
for name, ww in (("no outlier", w), ("one weight = -3.5", w2)):
    lv = 7; sc = np.abs(ww).max()/lv; qq = np.round(ww/sc).clip(-lv, lv)
    print(f"   {name:<20} step {sc:.4f}   small weights become {np.round(qq[[1,2,5]]*sc, 3)}  (were {ww[[1,2,5]]})")
print("   the outlier forces a coarse step and the small weights round to zero. real weight")
print("   matrices have such outliers, which is the whole problem quantization methods solve.")

print("\n=== the fix: a scale per small group, not per matrix ===")
W = rng.normal(0, 0.02, (256, 256)); W[rng.integers(0, 256, 10), rng.integers(0, 256, 10)] *= 8
def qerr(group):
    lv = 7; Wq = np.empty_like(W)
    for g in range(0, 256, group):
        blk = W[:, g:g+group]; sc = np.abs(blk).max(1, keepdims=True)/lv
        Wq[:, g:g+group] = np.round(blk/sc).clip(-lv, lv)*sc
    return np.linalg.norm(Wq - W)/np.linalg.norm(W)
print(f"   {'group size':>11}{'rel. weight error':>19}{'extra bits per weight':>23}")
for g in (256, 128, 64, 32, 16):
    print(f"   {g:>11}{qerr(g):>19.4f}{16/g:>23.2f}")
print("   smaller groups: an outlier only hurts its own block, at the cost of storing more scales.")
print("   group 32 is the common compromise (0.5 extra bits/weight). GPTQ and AWQ go further by")
print("   choosing the rounding to minimise output error, not weight error.")
