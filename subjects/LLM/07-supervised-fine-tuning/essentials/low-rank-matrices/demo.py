#!/usr/bin/env python3
"""Rank, low-rank factorization, and why LoRA is small. Run: python3 demo.py"""
import numpy as np
rng = np.random.default_rng(0)

print("=== rank: how many independent directions a matrix really has ===")
a = np.array([1.0, 2.0, 3.0]); b = np.array([2.0, -1.0, 0.5])
M1 = np.outer(a, np.array([1, 0, 2, 1]))                 # every row is a multiple of one row
M2 = np.outer(a, [1, 0, 2, 1]) + np.outer(b, [0, 1, 1, -1])
M3 = rng.normal(size=(3, 4))
for name, M in (("one outer product", M1), ("sum of two", M2), ("random 3x4", M3)):
    print(f"   {name:<20} shape {M.shape}  rank {np.linalg.matrix_rank(M)}")
print("   a rank-1 matrix is a column times a row. rank-r is the sum of r of those.")

print("\n=== a low-rank matrix is a small matrix in disguise ===")
n, m = 4096, 4096
for r in (1, 8, 64, 512):
    print(f"   [{n}x{m}] as A[{n}x{r}] @ B[{r}x{m}]:  {r*(n+m):>12,} numbers instead of {n*m:>12,}  ({100*r*(n+m)/(n*m):5.2f}%)")
print("   store the two factors, not the product. rank 8 is 0.4% of the full matrix.")

print("\n=== what does a matrix's spectrum look like? (singular values) ===")
W = rng.normal(size=(64, 64))
Wl = rng.normal(size=(64, 4)) @ rng.normal(size=(4, 64)) + 0.05*rng.normal(size=(64, 64))
for name, X in (("random full-rank", W), ("rank-4 + small noise", Wl)):
    sv = np.linalg.svd(X, compute_uv=False)
    print(f"   {name:<22} top 6 singular values {np.round(sv[:6], 1)}  ... 60th {sv[59]:.2f}")
print("   the second matrix is 'really' 4 directions plus dust: a low-rank approximation")
print("   captures it. fine-tuning updates turn out to look like the second kind.")

print("\n=== LoRA: W stays frozen; train a rank-r correction A@B ===")
W = rng.normal(0, 0.1, (36, 32))
A = rng.normal(0, 0.01, (36, 2)); B = np.zeros((2, 32))
print(f"   W  {W.shape} = {W.size} frozen params")
print(f"   A  {A.shape}, B {B.shape} = {A.size + B.size} trainable params  ({100*(A.size+B.size)/W.size:.0f}% of W)")
print(f"   effective weight = W + A@B, shape {(W + A@B).shape}; at init A@B = 0 so nothing changes")
print("   B starts at zero on purpose: the model begins exactly as the base model.")
print("   after training, A@B can be merged into W -- inference cost is unchanged.")

print("\n=== the real saving: optimizer state ===")
full = 8.03e9
for name, trainable in (("full fine-tune", full), ("LoRA r=16 on attention (typical)", 4.2e7)):
    print(f"   {name:<36} trainable {trainable:.2e}  ->  Adam state (2x) + grads (1x) in fp32: {3*trainable*4/1e9:8.1f} GB")
print("   full fine-tuning of an 8B model needs ~100 GB just for optimizer state; LoRA needs")
print("   under a gigabyte. that is why it fits on one GPU. compute per step is NOT lower --")
print("   the forward and backward through W still happen.")
