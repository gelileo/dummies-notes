# Essential · The contrastive loss (InfoNCE)

**Needed for:** *"CLIP"*, *"InfoNCE"*, *"pull matched pairs together"* in [chapter 13](../../README.md),
and the training of every embedding model in [chapter 12](../../../12-context-and-knowledge/).

## Every image against every caption

```
   rows = images, columns = captions. the DIAGONAL is the matched pairs.
[[ 0.97  0.11 -0.02 -0.29]
 [-0.24  0.83  0.02  0.21]
 [ 0.09  0.28  0.79 -0.64]
 [-0.47 -0.06  0.26  0.82]]
```

A batch of `B` (image, caption) pairs gives a `B × B` matrix of similarities. The diagonal is the
matched pairs; everything else is a mismatch you get for free.

## Cross-entropy, with the batch as the vocabulary

```
   softmax(row / 0.1):
[[1.    0.    0.    0.   ]
 [0.    0.998 0.    0.002]
 [0.001 0.006 0.993 0.   ]
 [0.    0.    0.004 0.996]]
   -log p(correct caption) per image: [0.    0.002 0.007 0.004]   mean 0.003
   that IS chapter 03's cross-entropy, with 'which caption?' in place of 'which next token?'.
   the symmetric version does the same for columns (which image for this caption) and averages.
```

Softmax each row, take `−log` of the diagonal entry, average. **That is
[chapter 03](../../../03-training-objective/)'s cross-entropy** with "which caption?" in place of
"which next token?". The symmetric version does the same down the columns and averages both.

## Batch size sets the difficulty

```
   batch      4: chance = 1/4, loss at chance = ln(4) = 1.39
   batch     64: chance = 1/64, loss at chance = ln(64) = 4.16
   batch   1024: chance = 1/1024, loss at chance = ln(1024) = 6.93
   batch  32768: chance = 1/32768, loss at chance = ln(32768) = 10.40
   bigger batch = more wrong captions to reject = harder task = better embeddings. CLIP used 32k.
```

More items in the batch means more wrong captions to reject. CLIP used a batch of 32,768, and the
loss at chance is `ln 32768 ≈ 10.4`. Bigger batches make the task harder and the embeddings better —
which is why contrastive training is famously batch-hungry.

## Temperature

```
   temp 1.0   p(diagonal) = [0.482 0.43  0.426 0.443]
   temp 0.1   p(diagonal) = [1.    0.998 0.993 0.996]
   temp 0.01  p(diagonal) = [1. 1. 1. 1.]
   small temperature sharpens: small similarity gaps become decisive. it is usually learned.
```

## Negatives for free — and false ones

```
   every off-diagonal entry is a negative pair, for free -- no sampling step, no 'negative
   mining'. two captions of the same thing in one batch are a false negative; with few classes
   that caps the in-batch accuracy while the embedding space is still learned correctly.
```

## Run it

```bash
python3 demo.py
```

## Terms

| Term | Meaning |
| --- | --- |
| **contrastive learning** | Train embeddings so matched pairs are close and mismatched pairs far. |
| **positive / negative pair** | Matched (diagonal) / mismatched (off-diagonal). |
| **in-batch negatives** | Using the other items in the batch as negatives. No sampling step. |
| **InfoNCE** | Softmax over the batch, cross-entropy against the diagonal. The contrastive loss. |
| **temperature** | Divisor on similarities before softmax. Sharpens; usually learned. |
| **false negative** | A mismatched pair that is actually a match (two captions of the same thing). |
| **CLIP** | Contrastive Language–Image Pretraining: this loss on 400M image–text pairs. |
