#!/usr/bin/env python3
"""Turning scores into probabilities. Run: python3 softmax_demo.py"""
import math
def softmax(v):
    m = max(v)                                  # subtract the max: same answer, no overflow
    e = [math.exp(x - m) for x in v]
    s = sum(e)
    return [x/s for x in e]

print("=== softmax turns any list of numbers into a probability distribution ===")
for scores in ([2.0, 1.0, 0.1], [5.0, 1.0, 0.1], [1.0, 1.0, 1.0], [-3.0, -1.0, -8.0]):
    p = softmax(scores)
    print(f"   {str(scores):<24} -> {[f'{x:.3f}' for x in p]}   sums to {sum(p):.3f}")

print("\n=== why exp()? it makes everything positive and amplifies gaps ===")
print(f"   {'score':>8}{'exp(score)':>13}")
for s in (-2, -1, 0, 1, 2, 3):
    print(f"   {s:>8}{math.exp(s):>13.3f}")
print("   Negative scores survive as small positive numbers - nothing is thrown away.")

print("\n=== only the DIFFERENCES matter ===")
for scores in ([1.0, 2.0, 3.0], [101.0, 102.0, 103.0], [-9.0, -8.0, -7.0]):
    print(f"   {str(scores):<24} -> {[f'{x:.3f}' for x in softmax(scores)]}")
print("   Adding a constant to every score changes nothing. That is why subtracting")
print("   the max is safe, and it is what stops exp() overflowing.")

print("\n=== -inf becomes exactly zero: this is how the causal mask works ===")
print(f"   softmax([2.0, 1.0, -inf]) = {[f'{x:.3f}' for x in softmax([2.0, 1.0, float('-inf')])]}")

print("\n=== dividing every score by T before softmax ('temperature') ===")
base = [3.0, 2.0, 1.0]
for T in (0.5, 1.0, 2.0, 10.0):
    print(f"   T={T:<5} -> {[f'{x:.3f}' for x in softmax([s/T for s in base])]}")
print("   small T -> sharper (closer to picking the top one); large T -> flatter.")
