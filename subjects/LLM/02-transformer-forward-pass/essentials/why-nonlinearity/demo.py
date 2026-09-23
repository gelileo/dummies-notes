#!/usr/bin/env python3
"""Why a network needs a non-linear step. Run: python3 nonlinear_demo.py"""
import math, random
def mm(A, B):
    return [[sum(A[i][k]*B[k][j] for k in range(len(B))) for j in range(len(B[0]))]
            for i in range(len(A))]

print("=== three matrices in a row do the work of one ===")
random.seed(3)
W1, W2, W3 = ([[random.gauss(0,1) for _ in range(3)] for _ in range(3)] for _ in range(3))
x = [[1.0, 2.0, 3.0]]
stepwise = mm(mm(mm(x, W1), W2), W3)
collapsed = mm(x, mm(mm(W1, W2), W3))
print(f"   x @ W1 @ W2 @ W3   = {[round(v,6) for v in stepwise[0]]}")
print(f"   x @ (W1 @ W2 @ W3) = {[round(v,6) for v in collapsed[0]]}")
print(f"   identical: {all(abs(a-b) < 1e-9 for a,b in zip(stepwise[0], collapsed[0]))}")
print("   So without something non-linear between them, depth buys NOTHING:")
print("   a 100-layer linear network is exactly one matrix wearing a costume.")

relu = lambda x: max(0.0, x)
silu = lambda x: x/(1+math.exp(-x))
print("\n=== the fix: bend the line between layers ===")
print(f"   {'x':>6}{'relu(x)':>10}{'silu(x)':>10}")
for v in (-3, -2, -1, -0.5, 0, 0.5, 1, 2, 3):
    print(f"   {v:>6}{relu(v):>10.3f}{silu(v):>10.3f}")
print("   Both flatten negatives and pass positives. SiLU does it smoothly, with")
print("   no corner at zero - which makes it easier to train.")

print("\n=== with a bend, the layers stop collapsing ===")
def run(activate):
    v = x[0][:]
    for W in (W1, W2, W3):
        v = mm([v], W)[0]
        if activate: v = [silu(t) for t in v]
    return v
print(f"   linear only      {[round(t,4) for t in run(False)]}")
print(f"   with SiLU        {[round(t,4) for t in run(True)]}")
print("   The second cannot be written as a single matrix. That is what depth is for.")
