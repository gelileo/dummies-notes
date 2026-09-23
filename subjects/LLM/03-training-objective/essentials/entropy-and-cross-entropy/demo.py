#!/usr/bin/env python3
"""Entropy, cross-entropy, KL divergence -- and why the training loss is a
cross-entropy. Run: python3 demo.py"""
import math

def H(p):        return -sum(x*math.log2(x) for x in p if x > 0)           # entropy, bits
def CE(p, q):    return -sum(x*math.log2(y) for x, y in zip(p, q) if x > 0) # cross-entropy
def KL(p, q):    return CE(p, q) - H(p)

print("=== entropy: the AVERAGE surprise of a distribution, in bits ===")
for name, p in (("fair coin", [0.5, 0.5]), ("biased coin 90/10", [0.9, 0.1]),
                ("certain", [1.0, 0.0]), ("fair 6-sided die", [1/6]*6),
                ("loaded die", [0.5, 0.1, 0.1, 0.1, 0.1, 0.1])):
    print(f"   {name:<20} H = {H(p):.3f} bits")
print("   Fair coin = 1 bit exactly. Certainty = 0. More spread = more bits.")
print("   Entropy is the FLOOR: no predictor of this source can average below it.")

print("\n=== cross-entropy: average surprise when you believe q but truth is p ===")
truth = [0.7, 0.2, 0.1]
print(f"   truth p = {truth}   entropy H(p) = {H(truth):.3f} bits")
print(f"   {'your model q':<26}{'cross-entropy':>15}{'gap (KL)':>12}")
for q in ([0.7, 0.2, 0.1], [0.6, 0.3, 0.1], [0.4, 0.4, 0.2], [1/3, 1/3, 1/3], [0.1, 0.2, 0.7]):
    print(f"   {str([round(x,3) for x in q]):<26}{CE(truth, q):>15.3f}{KL(truth, q):>12.3f}")
print("   Minimum is exactly at q = p, where cross-entropy equals entropy and")
print("   the gap is 0. Every other q pays extra. The gap is the KL divergence.")

print("\n=== the training loss is a cross-entropy against a one-hot truth ===")
q = [0.71, 0.09, 0.06, 0.04, 0.10]              # model's prediction (chapter 03's example)
truth_onehot = [1, 0, 0, 0, 0]                  # 'Paris' actually came next
print(f"   model q = {q}")
print(f"   truth   = {truth_onehot}   (we KNOW what came next -- all mass on one token)")
print(f"   cross-entropy = -1*log(q[0]) - 0 - 0 - 0 - 0 = -log({q[0]}) = {-math.log(q[0]):.3f} nats")
print("   With a one-hot truth, cross-entropy collapses to -log(p of the true token).")
print("   That IS the per-token loss. 'Cross-entropy loss' and '-log p' are one thing.")

print("\n=== so what does 'lowering the loss' mean? ===")
print("   average loss over a corpus = cross-entropy(true text distribution, model)")
print("                              = entropy(language) + KL(language || model)")
print("   The first term is fixed -- language is genuinely unpredictable to some")
print("   degree. Training can only shrink the second. That fixed part is the")
print("   'irreducible loss' that scaling-law curves flatten towards (chapter 06).")
