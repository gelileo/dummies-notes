# Essential · Averages, spread, and why `√d_head`

**Needed for:** RMSNorm, and the `/ √d_head` in every attention score — two places
[chapter 02](../../README.md) divides by something without fully explaining why.

## Mean, variance, standard deviation

```
   data      [2, 4, 4, 4, 5, 5, 7, 9]
   mean      5.0                 <- the balance point
   variance  4.0                 <- average squared distance from the mean
   std dev   2.0                 <- typical distance from the mean
```

- **Mean** — the average. Add them up, divide by how many.
- **Variance** — average *squared* distance from the mean. Squaring makes everything positive, so
  distances below and above the mean do not cancel out.
- **Standard deviation** — the square root of variance, which puts it back into the original
  units. Read it as *"a typical value sits about this far from the mean"*.

That is all the statistics chapter 02 needs.

## Root mean square

```
   rms([3, 4]        ) = 3.536   (mean =   3.5)
   rms([-3, -4]      ) = 3.536   (mean =  -3.5)
   rms([1, 1, 1, 1]  ) = 1.000   (mean =   1.0)
   rms([0, 0, 0, 8]  ) = 4.000   (mean =   2.0)
   RMSNorm divides a vector by this, so its typical entry becomes about 1.
```

Square every entry, average them, square-root. It measures **size regardless of sign** — `[3,4]`
and `[-3,-4]` give the same answer, while their *means* differ wildly.

**RMSNorm** divides a vector by its RMS, so its typical entry becomes about 1. Chapter 02 applies
it before every sublayer because the residual stream keeps *accumulating*: without rescaling,
values drift upward through 32 layers and the later layers see inputs on a completely different
scale from the ones they were trained on.

## The one that actually needs explaining: `√d_head`

Attention divides every score by `√d_head`. Here is why.

A dot product sums `d` separate products. Each is a small positive or negative number and they
partly cancel — but not completely, and the more terms you add the further the total tends to
wander from zero. The question is *how fast*:

```
   two random vectors of length d, 2000 trials each:
        d   mean |a.b|   std of a.b  std / sqrt(d)
        4         1.48         1.96          0.980
       16         3.08         3.91          0.978
       64         6.44         8.06          1.007
      256        13.04        16.25          1.015
     1024        24.90        31.41          0.982
     4096        51.32        64.11          1.002
   The last column is flat at ~1.0. So the spread is exactly proportional
   to sqrt(d) -- which is why dividing by sqrt(d_head) cancels it.
```

Look at the last column. Dividing the spread by `√d` gives about 1.0 at **every** size, from 4 to
4096. So the spread of a dot product is **exactly proportional to `√d`** — which means dividing by
`√d` cancels it, and scores stay the same size no matter how wide the model is.

### Why it matters so much

Softmax amplifies gaps. Feed it scores that are several times too spread out and it collapses:

```
   toy d_head=4
      without /sqrt(d): scores ['  -0.3', '   1.2', '  -0.6', '   4.0', '   2.2']
                        weights ['0.011', '0.048', '0.008', '0.799', '0.134']
      with    /sqrt(d): scores ['  -0.2', '   0.6', '  -0.3', '   2.0', '   1.1']
                        weights ['0.061', '0.131', '0.054', '0.535', '0.219']
   Llama-3 d_head=128
      without /sqrt(d): scores ['  -5.2', '   0.4', '  10.1', '  -3.2', '   3.5']
                        weights ['0.000', '0.000', '0.998', '0.000', '0.001']
      with    /sqrt(d): scores ['  -0.5', '   0.0', '   0.9', '  -0.3', '   0.3']
                        weights ['0.101', '0.167', '0.391', '0.121', '0.220']
```

At `d_head = 128` unscaled, one token receives **0.998** of the attention and the rest get
essentially nothing. The softmax has **saturated** — it has become a hard pick instead of a soft
blend. Two things break:

- The head can no longer combine information from several tokens. It only ever copies one.
- Training nearly stops, because a saturated softmax has almost no gradient: nudging a score
  barely moves the output, so there is nothing to learn from.
  ([Chapter 04](../../../04-optimization-loop/) covers gradients.)

Scaled, the same scores give a usable spread. One number, `√d_head`, keeps attention working at
any model width.

## Run it

```bash
python3 demo.py
```

## Terms

| Term | Meaning |
| --- | --- |
| **mean** | The average. |
| **variance** | Average squared distance from the mean. |
| **standard deviation** | Square root of the variance; typical distance from the mean. |
| **root mean square (RMS)** | Square, average, square-root. Size ignoring sign. |
| **RMSNorm** | Divide a vector by its RMS, then apply a learned per-dimension gain. |
| **normalize** | Rescale something so a measure of its size becomes a fixed value. |
| **saturated softmax** | Nearly all weight on one entry; behaves like a hard pick and barely trains. |
