# Essential · Low-rank matrices, and why LoRA is small

**Needed for:** *"LoRA learns a low-rank update `A·B`"* and *"why it fits on one GPU"* in
[chapter 07](../../README.md).

## Rank: how many independent directions a matrix really has

```
   one outer product    shape (3, 4)  rank 1
   sum of two           shape (3, 4)  rank 2
   random 3x4           shape (3, 4)  rank 3
   a rank-1 matrix is a column times a row. rank-r is the sum of r of those.
```

A matrix is a grid of numbers, but some grids carry far less information than their size
suggests. If every row is a multiple of one row, the whole matrix is one **column times one
row** — rank 1. Add a second independent column-times-row and you have rank 2. A random matrix
has full rank: every row says something new.

## A low-rank matrix is a small matrix in disguise

```
   [4096x4096] as A[4096x1] @ B[1x4096]:         8,192 numbers instead of   16,777,216  ( 0.05%)
   [4096x4096] as A[4096x8] @ B[8x4096]:        65,536 numbers instead of   16,777,216  ( 0.39%)
   [4096x4096] as A[4096x64] @ B[64x4096]:       524,288 numbers instead of   16,777,216  ( 3.12%)
   [4096x4096] as A[4096x512] @ B[512x4096]:     4,194,304 numbers instead of   16,777,216  (25.00%)
   store the two factors, not the product. rank 8 is 0.4% of the full matrix.
```

A rank-*r* matrix of shape `[n, m]` can be stored as two factors, `A [n, r]` and `B [r, m]`,
using `r·(n+m)` numbers instead of `n·m`. For a 4096×4096 matrix at rank 8 that is **0.4%** of
the storage. The product `A @ B` reconstructs it exactly.

## What real weight matrices look like

```
   random full-rank       top 6 singular values [15.7 15.  14.  13.9 13.8 13.5]  ... 60th 0.63
   rank-4 + small noise   top 6 singular values [90.3 61.  57.1 47.7  0.8  0.7]  ... 60th 0.04
   the second matrix is 'really' 4 directions plus dust: a low-rank approximation
   captures it. fine-tuning updates turn out to look like the second kind.
```

The **singular values** of a matrix measure how much it stretches along each independent
direction, in order. A random matrix has them all of similar size — it genuinely uses every
direction. A "rank-4 plus noise" matrix has four large ones and then dust. The empirical finding
behind LoRA is that the *change* a fine-tune makes to a weight matrix looks like the second kind:
a few strong directions and little else.

## LoRA

```
   W  (36, 32) = 1152 frozen params
   A  (36, 2), B (2, 32) = 136 trainable params  (12% of W)
   effective weight = W + A@B, shape (36, 32); at init A@B = 0 so nothing changes
   B starts at zero on purpose: the model begins exactly as the base model.
   after training, A@B can be merged into W -- inference cost is unchanged.
```

Freeze `W`. Add a trainable `A @ B` of rank *r* beside it, so the layer computes `x @ (W + A@B)`.
Start `B` at zero, so at the first step the model is exactly the base model. Train only `A` and
`B`. Afterwards, add `A @ B` into `W` once and serve it — inference is unchanged.

## The saving is optimizer memory, not compute

```
   full fine-tune                       trainable 8.03e+09  ->  Adam state (2x) + grads (1x) in fp32:     96.4 GB
   LoRA r=16 on attention (typical)     trainable 4.20e+07  ->  Adam state (2x) + grads (1x) in fp32:      0.5 GB
   full fine-tuning of an 8B model needs ~100 GB just for optimizer state; LoRA needs
   under a gigabyte. that is why it fits on one GPU. compute per step is NOT lower --
   the forward and backward through W still happen.
```

The forward and backward passes still go through the full `W`, so a LoRA step costs about the
same compute as a full fine-tuning step. What shrinks is everything the optimizer has to *hold*
per trainable parameter — Adam's two moment estimates plus the gradient, all in fp32. For an 8B
model that is ~100 GB for full fine-tuning and under 1 GB for LoRA. That is the difference
between eight GPUs and one.

## Run it

```bash
python3 demo.py
```

## Terms

| Term | Meaning |
| --- | --- |
| **rank** | The number of independent directions a matrix has; how many rows say something new. |
| **outer product** | A column times a row. The simplest matrix: rank 1. |
| **low-rank** | Rank much smaller than the matrix's dimensions. Storable as two thin factors. |
| **factorization** | Writing a matrix as a product `A @ B` of smaller ones. |
| **singular values** | How much a matrix stretches along each of its independent directions, largest first. |
| **LoRA** | Low-Rank Adaptation: freeze `W`, train `A @ B`, merge afterwards. |
| **adapter** | The trained `A, B` pair. Small, swappable, shares one base model. |
| **QLoRA** | LoRA with the frozen base weights stored in 4-bit. Fits larger models on one GPU. |
