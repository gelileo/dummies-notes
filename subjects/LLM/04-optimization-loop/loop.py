#!/usr/bin/env python3
"""Generates training-loop.md from live runs of train_loop.py. Run: python3 loop.py"""
import io, numpy as np
from train_loop import (V, D, N, FLOOR, prev, nxt, init, loss_and_grads, full_loss,
                        train, warmup_cosine)
o = io.StringIO(); W = o.write
np.set_printoptions(precision=3, suppress=True)

W(f"""# The loop, traced

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
  tokens            {N:,}
  vocabulary        {V}
  embedding dim     {D}
  irreducible loss  {FLOOR:.4f} nats   <- loss of the TRUE model on this data; nothing can beat it
  uniform baseline  {np.log(V):.4f} nats   <- ln({V})
```

---

## 2. One training step

""")
P = init(); idx = np.array([5, 17, 3, 11]); xb, yb = prev[idx], nxt[idx]
loss, g, p, dl = loss_and_grads(P, xb, yb)
W(f"""```
  batch:    prev tokens {xb.tolist()}  ->  true next {yb.tolist()}

  forward:  h      = E[x]          shape {P['E'][xb].shape}
            logits = h @ W + b     shape {(len(xb), V)}
            p      = softmax(logits)
            loss   = mean(-log p[true])  =  {loss:.4f}      (uniform would be {np.log(V):.4f})

  backward: dlogits = (p - onehot) / B
            row 0, first six entries      {dl[0,:6]}
            row 0 at the true token {yb[0]:>2}      {dl[0, yb[0]]:+.4f}   <- negative: push this logit UP
            dW = h.T @ dlogits            |dW| = {np.linalg.norm(g['W']):.4f}
            db = sum(dlogits)             |db| = {np.linalg.norm(g['b']):.4f}
            dE[x] += dlogits @ W.T        |dE| = {np.linalg.norm(g['E']):.4f}

  update:   W -= 0.5 * dW               largest single change {0.5*np.abs(g['W']).max():.4f}
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
""")
def numgrad(P, name, i, j, eps=1e-5):
    Q = {k: v.copy() for k, v in P.items()}
    Q[name][i, j] += eps; lp, *_ = loss_and_grads(Q, xb, yb)
    Q[name][i, j] -= 2*eps; lm, *_ = loss_and_grads(Q, xb, yb)
    return (lp - lm) / (2*eps)
for name, i, j in (("W", 2, 7), ("W", 10, 0), ("E", xb[1], 3)):
    W(f"  d loss / d {name}[{i},{j}]     analytic {g[name][i,j]:+.6f}     numeric {numgrad(P, name, i, j):+.6f}\n")
W(f"""```

They agree to six decimals. This check — the **gradient check** — is how you know a backward pass
is calculus and not a plausible-looking bug. Every autograd framework is tested this way.

---

## 4. Three optimizers

Same model, same data, same batches. Loss on the full dataset at each checkpoint:

```
""")
log = (1, 10, 50, 100, 200, 400, 600)
runs = {k: train(k, lr, log_at=log)[1] for k, lr in (("sgd", 0.5), ("momentum", 0.05), ("adam", 0.01))}
W(f"  {'step':>6}" + "".join(f"{k:>17}" for k in ("sgd lr=0.5", "momentum lr=.05", "adam lr=0.01")) + f"{'floor':>10}\n")
for t in log:
    W(f"  {t:>6}" + "".join(f"{runs[k][t]:>17.4f}" for k in runs) + f"{FLOOR:>10.4f}\n")
W(f"""```

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
""")
W(f"  {'sgd lr':>8}{'loss after 600 steps':>22}\n")
for lr in (0.01, 0.1, 0.5, 2.0, 10.0, 50.0):
    _, _, fl = train("sgd", lr)
    W(f"  {lr:>8}{fl if isinstance(fl, str) else f'{fl:.4f}':>22}\n")
W(f"""```

Too small and after 600 steps you have barely left the starting line. Too large and the loss is
`NaN` — the weights overshot so far the numbers stopped being numbers. The window between is not
wide. Learning rate is the one hyperparameter that cannot be approximately right.

---

## 6. Schedules

```
""")
for lr in (0.01, 0.05):
    c = train("adam", lr)[2]; sc = train("adam", lr, schedule=warmup_cosine)[2]
    W(f"  adam lr={lr}:   constant {c:.4f}     warmup + cosine {sc:.4f}\n")
W(f"""```

**Warmup** ramps the learning rate up from zero over the first steps, while the weights are
random and a full-size step would do damage. **Cosine decay** then eases it down so the model can
settle into a minimum instead of bouncing around it. At a gentle base rate the schedule barely
matters. At an aggressive one it rescues the run — which is the regime real training operates
in, because a higher rate that works is faster.

---

## 7. Batch size and noise

A batch gradient is an *estimate* of the full-data gradient. How good an estimate?

```
""")
P = init(); _, gfull, _, _ = loss_and_grads(P, prev, nxt)
W(f"  {'B':>6}{'|g_batch - g_full|':>20}{'x sqrt(B)':>12}\n")
r = np.random.default_rng(3)
for B in (1, 4, 16, 64, 256, 1024):
    errs = []
    for _ in range(40):
        idx = r.integers(0, len(prev), B); _, gb, _, _ = loss_and_grads(P, prev[idx], nxt[idx])
        errs.append(np.linalg.norm(gb["W"] - gfull["W"]))
    e = np.mean(errs); W(f"  {B:>6}{e:>20.4f}{e*np.sqrt(B):>12.4f}\n")
W(f"""```

The last column is flat: the error falls as **`1/√B`**. Quadrupling the batch halves the noise,
and no more. That diminishing return is why batch sizes are chosen by throughput (how many tokens
the hardware can process at once), not by accuracy — the noise is tolerable long before the
hardware is saturated.

---

## 8. Gradient clipping

Real training data occasionally produces a pathological batch whose gradient is enormous. Here
one is injected every 100 steps at 200× normal size:

```
""")
log7 = (99, 100, 101, 110, 200, 300, 600)
for clip in (None, 1.0):
    _, hist, fl = train("adam", 0.01, clip=clip, spike_every=100, log_at=log7)
    W(f"  clip={str(clip):<5} " + "  ".join(f"{t}:{hist[t]:.3f}" for t in log7) + f"   final {fl:.4f}\n")
W(f"""```

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
""")
for wd in (0.0, 0.1):
    Pw, _, fl = train("adamw", 0.01, steps=1500, wd=wd)
    W(f"  adamw wd={wd}:   loss {fl:.4f}   |W| {np.linalg.norm(Pw['W']):.3f}   |E| {np.linalg.norm(Pw['E']):.3f}\n")
W(f"""```

Each step, shrink every weight by a tiny fraction (`w -= lr · wd · w`) before applying the
gradient update. Nearly the same loss, noticeably smaller weights. Over 1,500 steps this is a
mild effect; over a million steps it is what stops parameters drifting without bound and is a
form of regularisation. **AdamW** applies it directly to the weights; older "L2 regularisation"
folded it into the gradient, which interacts badly with Adam's normalisation — hence the W.

---

## 10. Numerics

```
""")
def bf16(a):
    b = np.asarray(a, dtype=np.float32).view(np.uint32) & np.uint32(0xFFFF0000)
    return b.view(np.float32)
W(f"  {'value':<12}{'fp16':>12}{'bf16':>14}{'fp32':>14}\n")
for val in (1.0 + 1e-3, 1.0 + 1e-2, 65504.0, 70000.0, 3.0e38):
    with np.errstate(over="ignore"):
        W(f"  {val:<12g}{float(np.float16(val)):>12g}{float(bf16(val)):>14g}{float(np.float32(val)):>14g}\n")
W(f"""```

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
  FLOPs             ≈ 6 · N · D  =  6 · 8.03e9 · 15e12  ≈  {6*8.03e9*15e12:.1e}      (chapter 06 derives this)
  steps             at a 16M-token batch:  15e12 / 16e6  ≈  {15e12/16e6:,.0f}
  GPU-hours         at 40% of an H100's ~990 TFLOP/s bf16 peak:  {6*8.03e9*15e12/(0.4*990e12)/3600:,.0f}
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
""")
open('training-loop.md', 'w').write(o.getvalue())
print("wrote training-loop.md", len(o.getvalue()), "chars")
