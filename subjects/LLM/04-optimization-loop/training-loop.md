# The loop, traced

Every number here is produced by `train_loop.py`. Run `python3 loop.py` to regenerate.

The model is the smallest thing that can be trained by gradient descent on the chapter-03
objective: an embedding table, one linear layer, softmax. Three parameter matrices, hand-written
backward pass, numpy. The data is synthetic **so that the irreducible loss is known exactly** —
a 20-token Markov source whose true next-token distribution we hold — which means we can watch
training approach a floor we can name.

---

## 0. The whole chapter is four lines

```python
loss, grads = loss_and_grads(params, batch)      # forward + backward
grads = clip(grads)                              # optional safety net
lr    = schedule(step)                           # optional, usually not optional
params = optimizer.step(params, grads, lr)       # the update
```

Repeated for weeks on thousands of GPUs. Everything below is one of those lines, measured.

---

## 1. Data with a known floor

```
  tokens            20,000
  vocabulary        20
  embedding dim     16
  irreducible loss  2.1166 nats   <- loss of the TRUE model on this data; nothing can beat it
  uniform baseline  2.9957 nats   <- ln(20)
```

---

## 2. One training step

```
  batch:    prev tokens [12, 4, 18, 10]  ->  true next [10, 0, 19, 7]

  forward:  h      = E[x]          shape (4, 16)
            logits = h @ W + b     shape (4, 20)
            p      = softmax(logits)
            loss   = mean(-log p[true])  =  3.0199      (uniform would be 2.9957)

  backward: dlogits = (p - onehot) / B
            row 0, first six entries      [0.012 0.012 0.012 0.012 0.012 0.012]
            row 0 at the true token 10      -0.2387   <- negative: push this logit UP
            dW = h.T @ dlogits            |dW| = 0.1846
            db = sum(dlogits)             |db| = 0.4470
            dE[x] += dlogits @ W.T        |dE| = 0.2176

  update:   W -= 0.5 * dW               largest single change 0.0318
```

Two things to notice. At initialisation the model is near-uniform, so every `dlogits` entry is
about `p/B = 0.05/4 = 0.0125` — except the true token's, which is `(p − 1)/B`, large and
negative. The gradient says *"raise this one, lower all the others slightly"*. That is the
entire content of one step.

And the famous derivative: **the gradient of softmax-plus-cross-entropy with respect to the
logits is simply `p − onehot`.** No exponentials, no logs in the backward pass — they cancel.
It is the cleanest gradient in deep learning and it is why the loss is shaped the way it is.

---

## 3. Is the hand-written backward pass right?

A derivative is a slope, and a slope can be measured by nudging: `(loss(w+h) − loss(w−h)) / 2h`.

```
  d loss / d W[2,7]     analytic +0.014167     numeric +0.014167
  d loss / d W[10,0]     analytic -0.005202     numeric -0.005202
  d loss / d E[4,3]     analytic -0.000404     numeric -0.000404
```

They agree to six decimals. This check — the **gradient check** — is how you know a backward pass
is calculus and not a plausible-looking bug. Every autograd framework is tested this way.

---

## 4. Three optimizers

Same model, same data, same batches. Loss on the full dataset at each checkpoint:

```
    step       sgd lr=0.5  momentum lr=.05     adam lr=0.01     floor
       1           2.9944           2.9975           2.9916    2.1166
      10           2.9743           2.9864           2.9353    2.1166
      50           2.9072           2.9253           2.4720    2.1166
     100           2.7547           2.8164           2.2771    2.1166
     200           2.4303           2.4773           2.2053    2.1166
     400           2.2239           2.2326           2.1668    2.1166
     600           2.1845           2.1851           2.1548    2.1166
```

- **SGD**: `w -= lr · g`. The gradient, scaled, subtracted.
- **Momentum**: keep a running average of the gradient and step along that. Smooths out noise
  and keeps moving through flat stretches.
- **Adam**: two running averages — the gradient (direction) and its square (magnitude) — and a
  step of `lr · m / √v`. Every parameter gets a step size normalised by its own recent gradient
  scale, so one learning rate serves all of them. It reaches loss 2.47 in 50 steps; SGD needs
  200. → [essentials: moving averages](essentials/moving-averages/)

This is also what **a loss curve** looks like: a fast early drop, a slowing approach, and a floor
it never crosses. Learn to read those three phases — every training run you ever look at has them.

---

## 5. The learning rate

```
    sgd lr  loss after 600 steps
      0.01                2.9716
       0.1                2.6705
       0.5                2.1845
       2.0                2.2054
      10.0                2.6044
      50.0              DIVERGED
```

Too small and after 600 steps you have barely left the starting line. Too large and the loss is
`NaN` — the weights overshot so far the numbers stopped being numbers. The window between is not
wide. Learning rate is the one hyperparameter that cannot be approximately right.

---

## 6. Schedules

```
  adam lr=0.01:   constant 2.1548     warmup + cosine 2.1556
  adam lr=0.05:   constant 2.2513     warmup + cosine 2.1335
```

**Warmup** ramps the learning rate up from zero over the first steps, while the weights are
random and a full-size step would do damage. **Cosine decay** then eases it down so the model can
settle into a minimum instead of bouncing around it. At a gentle base rate the schedule barely
matters. At an aggressive one it rescues the run — which is the regime real training operates
in, because a higher rate that works is faster.

---

## 7. Batch size and noise

A batch gradient is an *estimate* of the full-data gradient. How good an estimate?

```
       B  |g_batch - g_full|   x sqrt(B)
       1              0.3584      0.3584
       4              0.1775      0.3550
      16              0.0849      0.3397
      64              0.0422      0.3373
     256              0.0221      0.3528
    1024              0.0112      0.3578
```

The last column is flat: the error falls as **`1/√B`**. Quadrupling the batch halves the noise,
and no more. That diminishing return is why batch sizes are chosen by throughput (how many tokens
the hardware can process at once), not by accuracy — the noise is tolerable long before the
hardware is saturated.

---

## 8. Gradient clipping

Real training data occasionally produces a pathological batch whose gradient is enormous. Here
one is injected every 100 steps at 200× normal size:

```
  clip=None  99:2.278  100:2.278  101:2.279  110:2.321  200:2.282  300:2.287  600:2.305   final 2.3049
  clip=1.0   99:2.278  100:2.277  101:2.275  110:2.264  200:2.204  300:2.179  600:2.154   final 2.1539
```

Unclipped, the run stalls at 2.30 and never recovers. The mechanism is specific to Adam and
worth knowing: the spike inflates `v`, the running average of *squared* gradients, and with
`β₂ = 0.999` that inflation takes roughly a thousand steps to decay. Every subsequent step is
divided by a hugely overestimated `√v` and shrinks to almost nothing. **One bad batch poisons
the optimizer's memory for a thousand steps.**

Clipped — scale the whole gradient down whenever its norm exceeds 1.0 — the spike is just a
slightly large step, `v` never sees it, and the run reaches the floor. This is why every real
training config has a clip value, and why loss spikes in a training curve are taken seriously.

---

## 9. Weight decay

```
  adamw wd=0.0:   loss 2.1428   |W| 10.395   |E| 10.693
  adamw wd=0.1:   loss 2.1598   |W| 8.694   |E| 9.439
```

Each step, shrink every weight by a tiny fraction (`w -= lr · wd · w`) before applying the
gradient update. Nearly the same loss, noticeably smaller weights. Over 1,500 steps this is a
mild effect; over a million steps it is what stops parameters drifting without bound and is a
form of regularisation. **AdamW** applies it directly to the weights; older "L2 regularisation"
folded it into the gradient, which interacts badly with Adam's normalisation — hence the W.

---

## 10. Numerics

```
  value               fp16          bf16          fp32
  1.001            1.00098             1         1.001
  1.01             1.00977       1.00781          1.01
  65504              65504         65280         65504
  70000                inf         69632         70000
  3e+38                inf   2.99076e+38         3e+38
```

Sixteen-bit numbers halve memory traffic and double matrix-multiply throughput, so training uses
them for the heavy lifting. Two 16-bit formats exist and they trade the same bits differently:
`fp16` spends them on precision and overflows at 65,504; `bf16` spends them on range and cannot
tell `1.001` from `1.0`. Gradients span many orders of magnitude within one model, so **range wins
and bf16 is the standard**. The weights themselves are kept in fp32 — the "master copy" — because
tiny rounding errors accumulate over a million updates.
→ [essentials: floating point](essentials/floating-point/)

---

## 11. At real scale

The loop is identical; only the numbers change. For Llama-3-8B, trained on 15 trillion tokens:

```
  FLOPs             ≈ 6 · N · D  =  6 · 8.03e9 · 15e12  ≈  7.2e+23      (chapter 06 derives this)
  steps             at a 16M-token batch:  15e12 / 16e6  ≈  937,500
  GPU-hours         at 40% of an H100's ~990 TFLOP/s bf16 peak:  506,944
```

*(The 16M batch and 40% utilisation are illustrative assumptions in the right range, not
Llama-3's published configuration. Meta reported about 1.3M GPU-hours for the 8B model — a
reported figure, not measured here — and the gap to the estimate above is attention FLOPs, which
`6ND` omits, plus real-world utilisation.)*

Roughly a million steps of the four lines in section 0, each one a bf16 forward-and-backward
over sixteen million tokens, followed by an AdamW update to eight billion fp32 master weights.

---

## 12. Invariants

1. **One step = forward, loss, backward, update.** Every trick is a modifier on one of those.
2. **`d loss / d logits = p − onehot`.** The cleanest gradient in the field; check it numerically.
3. **The learning rate is the hyperparameter.** Too low crawls; too high is `NaN`; warm it up, decay it.
4. **Batch noise falls as `1/√B`** — diminishing returns, so batch size is set by hardware.
5. **Adam normalises step size per parameter**, which is why it dominates — and why one spike
   can poison it for a thousand steps. Clip.
6. **Decay the weights, not the gradient.** That is the W in AdamW.
7. **bf16 for the multiplies, fp32 for the weights.** Range over precision.
