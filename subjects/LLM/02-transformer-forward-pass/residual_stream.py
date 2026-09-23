#!/usr/bin/env python3
"""Four measurements of the residual stream. Run: python3 residual_stream.py"""
import math
from tiny_transformer import (EMBED, VOCAB, NORM1_GAIN, NORMF_GAIN, W_LM,
                              rmsnorm, matmul, softmax, encode, forward)
TOK = ["the", "trophy", "did", "not", "fit", "it"]; ids = encode(TOK); i_it = 5
tr = {}; forward(ids, tr, use_rope=False)
norm = lambda v: math.sqrt(sum(x*x for x in v))
STAGES = [("after embedding","embed"),("after attention","after_attn"),("after MLP","after_mlp")]

print("=== 1. the stream at each stage - row for 'it' ===")
print("   stage            " + "".join(f"{f'd{i}':>7}" for i in range(8)) + "    length")
for label, key in STAGES:
    r = tr[key][i_it]
    print(f"   {label:<17}" + "".join(f"{v:>7.2f}" for v in r) + f"{norm(r):>10.2f}")
print("   dim1 = 'trophy': starts at 0.00, attention writes it in.")
print("   dim6 = 'it':     still there at the end - nothing was overwritten.\n")

print("=== 2. add vs replace ===")
def run(residual, blocks=4):
    x = [EMBED[VOCAB[i]][:] for i in ids]
    W = [[0.3 if a == b else 0.0 for b in range(8)] for a in range(8)]
    for _ in range(blocks):
        corr = matmul([rmsnorm(r, NORM1_GAIN) for r in x], W)
        x = [[a+b for a, b in zip(ra, rb)] for ra, rb in zip(x, corr)] if residual else corr
    return x
for res in (True, False):
    r = run(res)[i_it]
    print(f"   residual={'ON ' if res else 'OFF'} 'it' after 4 blocks: "
          f"[{' '.join(f'{v:.2f}' for v in r)}]  length {norm(r):.3f}")
print("   OFF: each block replaced the stream, so the token's identity faded.\n")

print("=== 3. signal through N blocks (illustrative arithmetic, not a trained model) ===")
print(f"   {'blocks':>7}{'with residual':>16}{'without':>14}")
for n in (1, 2, 4, 8, 16, 32):
    w = wo = 1.0
    for _ in range(n):
        w, wo = w + 0.3*w, 0.3*wo
    print(f"   {n:>7}{w:>16.2f}{wo:>14.2e}")
print("   The real claim is about gradients: d(x+f(x))/dx = 1 + f'(x) always")
print("   leaves a path of derivative 1 back to every layer. See chapter 04.\n")

print("=== 4. logit lens - read the prediction out mid-stream ===")
for label, key in STAGES:
    lg = matmul([rmsnorm(r, NORMF_GAIN) for r in tr[key]], W_LM)
    pr = softmax(lg[-1])
    top = sorted(range(len(VOCAB)), key=lambda v: -pr[v])[:3]
    print(f"   {label:<17}" + "  ".join(f"{VOCAB[v]}={pr[v]:.3f}" for v in top))
print("   Straight after embedding the model just echoes its input.")
print("   After attention the prediction has moved - you are watching it form.")
