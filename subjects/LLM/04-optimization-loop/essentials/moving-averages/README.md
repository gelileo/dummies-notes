# Essential · Moving averages — the mechanism inside Adam

**Needed for:** *"Adam keeps running averages of the gradient and its square"* in
[chapter 04](../../README.md).

## A running average that gradually forgets

`m ← β·m + (1−β)·g`. Each new value is blended in at weight `(1−β)`; everything older is scaled
down by `β`. The result is a smoothed version of a noisy signal:

```
   beta=0.5:  1.09  1.45  2.20  2.18  1.69  2.12  3.04  3.23  2.09  1.09  1.08  1.57
   beta=0.9:  0.22  0.38  0.64  0.79  0.83  1.00  1.30  1.51  1.45  1.32  1.29  1.37
   raw     :  2.19  1.80  2.96  2.16  1.20  2.54  3.96  3.42  0.94  0.10  1.07  2.06
   truth = 2.0. beta=0.9 is smoother but slower to arrive. rule of thumb:
   beta=0.9 averages over ~1/(1-0.9) = 10 steps; beta=0.999 over ~1000.
```

Higher `β` means smoother but slower to react. A useful rule of thumb: the average effectively
spans about `1/(1−β)` recent values — 10 for `β = 0.9`, 1,000 for `β = 0.999`. That is why Adam's
defaults are `β₁ = 0.9` (a short memory for direction) and `β₂ = 0.999` (a long memory for
magnitude).

## The startup bias

```
    step t     ema   ema/(1-beta^t)   (true value 2.0)
         1   0.200            2.000
         2   0.380            2.000
         3   0.542            2.000
         4   0.688            2.000
         5   0.819            2.000
         6   0.937            2.000
         7   1.043            2.000
   the ema starts at 0 and is biased low early on. dividing by (1-beta^t)
   removes exactly that bias. those are Adam's 'mhat' and 'vhat'.
```

The average starts at zero, so for the first several steps it is biased low — it has not had time
to fill up. Dividing by `(1 − β^t)` removes exactly that bias. Those corrected values are the `m̂`
and `v̂` in Adam's update.

## Why Adam keeps two of them

```
   m = ema of the gradient      (which way, on average)
   v = ema of gradient squared  (how big, on average)
   step = lr * m / sqrt(v)
   two parameters with very different gradient scales:
   param A, gradients ~ 0.001     m=   0.0010  sqrt(v)=  0.0010  m/sqrt(v)= 1.000
   param B, gradients ~ 10        m=  10.4191  sqrt(v)= 10.2280  m/sqrt(v)= 1.019
   both get a step of about lr * 1.0. Adam normalises away the gradient's
   scale, so one learning rate serves every parameter -- that is its whole appeal.
```

`m` averages the gradient itself — *which way, on balance*. `v` averages the gradient *squared* —
*how big, on balance*. Dividing one by the square root of the other gives a step of roughly
`lr × (±1)` **regardless of the gradient's scale**. In the example, a parameter whose gradients
are around 0.001 and one whose gradients are around 10 both receive a step of about `lr`.

That is Adam's whole appeal: one learning rate serves every parameter, because each parameter's
step is normalised by its own recent gradient magnitude. Plain SGD would give the second
parameter a step 10,000× larger than the first.

## Run it

```bash
python3 demo.py
```

## Terms

| Term | Meaning |
| --- | --- |
| **exponential moving average (EMA)** | `m ← β·m + (1−β)·g`. A running average that weights recent values more. |
| **β (beta)** | The forgetting factor. `1/(1−β)` is roughly how many recent values the average spans. |
| **bias correction** | Dividing the EMA by `(1 − β^t)` to undo the low start. |
| **momentum** | SGD plus an EMA of the gradient: keeps moving in the recent average direction. |
| **first moment `m`** | EMA of the gradient. Direction. |
| **second moment `v`** | EMA of the squared gradient. Magnitude. |
| **Adam** | Step `= lr · m̂ / (√v̂ + ε)`. Per-parameter step size, normalised by recent gradient scale. |
| **AdamW** | Adam with weight decay applied to the weights directly rather than through the gradient. |
