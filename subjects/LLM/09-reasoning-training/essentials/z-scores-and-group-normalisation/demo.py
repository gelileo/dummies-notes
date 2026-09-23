#!/usr/bin/env python3
"""Standardising a group of numbers: (x - mean) / std. The GRPO advantage. Run: python3 demo.py"""
import numpy as np

print("=== the z-score: how many standard deviations from the group mean ===")
for name, r in (("rewards", np.array([0, 0, 1, 0, 1, 0, 0, 0], float)),
                ("scores ", np.array([2.0, 7.5, 3.1, 9.0, 4.4, 1.2, 6.0, 8.8]))):
    m, s = r.mean(), r.std()
    print(f"   {name} {r}")
    print(f"           mean {m:.3f}  std {s:.3f}")
    print(f"           z = (x - mean)/std = {np.round((r - m)/s, 2)}")
    print(f"           z has mean {((r-m)/s).mean():+.1f} and std {((r-m)/s).std():.1f}, always.\n")

print("=== why GRPO does this to a group of rewards ===")
r = np.array([0, 0, 1, 0, 1, 0, 0, 0], float)
z = (r - r.mean()) / r.std()
print(f"   8 samples for one prompt, rewards {r.astype(int)}")
print(f"   advantages {np.round(z, 2)}")
print("   1. the mean is the baseline: 'was this sample better than its siblings?' -- no critic")
print("      network needed to estimate expected reward, the group estimates it.")
print("   2. dividing by std puts every prompt on the same scale: a prompt where 1/8 succeed and")
print("      one where 7/8 succeed both yield advantages of unit size, so neither dominates.")

print("\n=== the degenerate cases ===")
for r in (np.zeros(8), np.ones(8)):
    print(f"   rewards {r.astype(int)}  std = {r.std():.1f}  -> no signal: nothing to normalise, skip the update")
print("   all-wrong: the model has nothing to learn from. all-right: nothing to improve.")
print("   the informative prompts are the ones the model sometimes gets right -- its frontier.")

print("\n=== the same operation is everywhere in this curriculum ===")
print("   RMSNorm (chapter 02) rescales a vector by its size. batch statistics, z-scores,")
print("   standardised test scores: all 'subtract the centre, divide by the spread'.")
