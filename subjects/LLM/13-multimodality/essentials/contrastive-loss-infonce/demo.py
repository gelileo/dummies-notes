#!/usr/bin/env python3
"""InfoNCE: cross-entropy where the 'vocabulary' is the rest of the batch. Run: python3 demo.py"""
import numpy as np
rng = np.random.default_rng(0)
def softmax(z, axis=-1): e = np.exp(z - z.max(axis, keepdims=True)); return e / e.sum(axis, keepdims=True)

B, D = 4, 8
I = rng.normal(size=(B, D)); T = I + 0.5*rng.normal(size=(B, D))       # 4 images and their 4 captions, roughly aligned
I /= np.linalg.norm(I, axis=1, keepdims=True); T /= np.linalg.norm(T, axis=1, keepdims=True)
sim = I @ T.T
print("=== the similarity matrix: every image against every caption in the batch ===")
print("   rows = images, columns = captions. the DIAGONAL is the matched pairs.")
print(np.round(sim, 2))

print("\n=== turn each row into a distribution and ask for the diagonal ===")
temp = 0.1
P = softmax(sim / temp)
print(f"   softmax(row / {temp}):")
print(np.round(P, 3))
loss_i = -np.log(P[np.arange(B), np.arange(B)])
print(f"   -log p(correct caption) per image: {np.round(loss_i, 3)}   mean {loss_i.mean():.3f}")
print("   that IS chapter 03's cross-entropy, with 'which caption?' in place of 'which next token?'.")
print("   the symmetric version does the same for columns (which image for this caption) and averages.")

print("\n=== at initialisation the loss is ln(B): batch size sets the difficulty ===")
for b in (4, 64, 1024, 32768):
    print(f"   batch {b:>6}: chance = 1/{b}, loss at chance = ln({b}) = {np.log(b):.2f}")
print("   bigger batch = more wrong captions to reject = harder task = better embeddings. CLIP used 32k.")

print("\n=== temperature ===")
for t in (1.0, 0.1, 0.01):
    P = softmax(sim / t); print(f"   temp {t:<5} p(diagonal) = {np.round(P[np.arange(B), np.arange(B)], 3)}")
print("   small temperature sharpens: small similarity gaps become decisive. it is usually learned.")

print("\n=== negatives you did not choose ===")
print("   every off-diagonal entry is a negative pair, for free -- no sampling step, no 'negative")
print("   mining'. two captions of the same thing in one batch are a false negative; with few classes")
print("   that caps the in-batch accuracy while the embedding space is still learned correctly.")
