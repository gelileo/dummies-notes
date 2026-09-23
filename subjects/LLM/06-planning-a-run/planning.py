#!/usr/bin/env python3
"""Generates planning.md from scaling.py. Run: python3 planning.py"""
import io, numpy as np
from scaling import E, A, B, ALPHA, BETA, L, flops_train, gpu_hours
o = io.StringIO(); W = o.write

W(f"""# Planning a run, traced

Every number here is computed by `scaling.py`. Run `python3 planning.py` to regenerate.

One function carries this chapter — Chinchilla's **published** fit of loss against model size
and data (Hoffmann et al., 2022):

```
  L(N, D) = E + A / N^α + B / D^β
  E = {E}   A = {A}   B = {B}   α = {ALPHA}   β = {BETA}
```

Those five constants are *reported, not measured here*. Everything below is arithmetic on
them — which is exactly the situation a lab is in when it plans a run: a fitted law from a
ladder of small models, and a budget to allocate.

---

## 1. Where `6ND` comes from

A matrix multiply `[n,k] @ [k,m]` costs `2·n·k·m` FLOPs — one multiply and one add per term. For
one token passing through a weight matrix holding `P` parameters that is `2P`. The backward pass
needs two such products (gradient with respect to the input, and to the weights): `4P`. So one
token through all `N` parameters, forward and backward, is `6N`, and `D` tokens is **`6ND`**.

```
""")
N8, D8 = 8.03e9, 15e12; C8 = flops_train(N8, D8)
W(f"  Llama-3-8B:   6 × {N8:.2e} × {D8:.1e}  =  {C8:.2e} FLOPs\n")
W(f"  at 40% of an H100's 990 TFLOP/s:      {gpu_hours(C8):,.0f} GPU-hours\n")
W(f"  on 1,000 GPUs:                        {gpu_hours(C8)/1000/24:.0f} days\n```\n\n")
W(f"""Meta reported about 1.3M GPU-hours for the 8B model *(reported)*. The gap is attention FLOPs —
`6ND` counts only the weight matrices, and attention's `QKᵀ` grows with sequence length — plus
real utilisation below 40%. `6ND` is the right first estimate and a known underestimate.
→ [essentials: FLOPs and units](essentials/flops-and-units/)

---

## 2. The law, tabulated

```
  N (params)     D = 1e11    D = 1e12    D = 1e13
""")
for N in (1e8, 1e9, 1e10, 1e11):
    W(f"  {N:>10.0e}" + "".join(f"{L(N, D):>12.3f}" for D in (1e11, 1e12, 1e13)) + "\n")
W(f"""```

Read down a column: more parameters, lower loss, with diminishing returns. Read across a row:
more data, lower loss, likewise. Every entry tends to **`E = {E}`** — the irreducible loss, the
entropy of the text itself ([chapter 03](../03-training-objective/)). No amount of either buys
its way below that.

---

## 3. Straight lines on log-log axes — if you subtract the whole floor

A power law `y = a·xᵇ` is a straight line of slope `b` when both axes are logarithmic. That is
the test scaling-law papers pass, and it is easy to run wrongly:

```
""")
Ns = np.logspace(8, 11, 7); D = 1e13
ex1 = L(Ns, D) - E; ex2 = L(Ns, D) - E - B / D**BETA
s1, _ = np.polyfit(np.log10(Ns), np.log10(ex1), 1); s2, _ = np.polyfit(np.log10(Ns), np.log10(ex2), 1)
W(f"  {'log10 N':>9}{'log10(L − E)':>14}{'log10(L − E − B/D^β)':>22}\n")
for n, a_, b_ in zip(Ns, ex1, ex2): W(f"  {np.log10(n):>9.2f}{np.log10(a_):>14.3f}{np.log10(b_):>22.3f}\n")
W(f"  fitted slope:  {s1:.3f}         {s2:.3f}        (true exponent −α = {-ALPHA})\n```\n\n")
W(f"""Subtract only `E` and the fit says `−0.24`. The data term `B/D^β` is a constant at fixed `D` —
a second floor you did not remove — and it **bends the line**. Subtract it too and the slope is
`−0.34`, the law's exponent, exactly. A curve that looks "roughly straight" on log-log axes is a
hypothesis; the residuals decide.
→ [essentials: power laws and log-log](essentials/power-laws-and-log-log/)

---

## 4. Compute-optimal: given a budget, how big a model and how much data?

Fix `C = 6ND`, so `D = C / 6N`, and minimise `L(N, C/6N)` over `N`:

```
  budget C     best N      best D     D/N     loss      175B model at the same budget
""")
for C in (1e21, 1e22, 1e23, 1e24):
    Ns_ = np.logspace(7, 13, 2000); Ds_ = C / (6*Ns_); ls = L(Ns_, Ds_); i = ls.argmin()
    Dg = C / (6*175e9)
    W(f"  {C:>8.0e}   {Ns_[i]:>9.2e}  {Ds_[i]:>9.2e}  {Ds_[i]/Ns_[i]:>6.0f}  {ls[i]:>7.3f}      D = {Dg:.1e}, loss {L(175e9, Dg):.3f}\n")
W(f"""```

This parametric fit says **50–100 tokens per parameter**, rising with budget. Chinchilla's two
other estimation methods gave the famous **~20:1** at around `10²³` FLOPs. The methods disagree on
the number — a real limitation of scaling laws — and agree on the direction: **GPT-3 was far too
large for its data.** 175B parameters on 300B tokens is 1.7 tokens per parameter, and the
right-hand column shows what that costs at every budget. Chinchilla (70B on 1.4T) matched it at
a quarter the size.

---

## 5. Why production models over-train anyway

Compute-optimal minimises *training* cost. But a model is trained once and served forever, and
serving cost scales with `N`, not `D`. Hold `N` fixed and keep going:

```
  8B model:   D (tokens)     D/N      loss     training FLOPs
""")
for D_ in (1.6e11, 4e11, 1e12, 4e12, 15e12):
    W(f"              {D_:>9.1e}  {D_/8e9:>7.0f}  {L(8e9, D_):>8.3f}  {flops_train(8e9, D_):>14.1e}\n")
W(f"""```

Llama-3-8B's 15T tokens is roughly **1,900 tokens per parameter** — some 90× past
compute-optimal — and the loss is still falling at the end of that table. That is deliberate:
pay more once in training to get a small model that is cheap to serve. *Training-optimal and
deployment-optimal are different points*, and the industry moved to the second.

---

## 6. The actual use: predict before you spend

Train a ladder of small models, fit the line, read off where the big one lands:

```
""")
lad_N = np.array([1e8, 3e8, 1e9, 3e9]); lad_D = 20*lad_N
lad_L = L(lad_N, lad_D) + np.random.default_rng(0).normal(0, 0.01, 4); lad_C = flops_train(lad_N, lad_D)
m, c = np.polyfit(np.log10(lad_C), np.log10(lad_L - E), 1)
tN = 70e9; tC = flops_train(tN, 20*tN); pred = E + 10**(m*np.log10(tC) + c)
for n_, c_, l_ in zip(lad_N, lad_C, lad_L): W(f"  N = {n_:.0e}   C = {c_:.1e}   loss {l_:.3f}\n")
W(f"\n  predicted for a 70B model at C = {tC:.1e}:  {pred:.3f}\n  the law evaluated there:                    {L(tN, 20*tN):.3f}\n```\n\n")
W(f"""This demonstrates the **procedure** on a known law, not the law's truth — the ladder is generated
by the same equation it then predicts. In a lab the four small runs are real training runs, the
line is fit to their measured losses, and the extrapolation is the bet. GPT-4's technical report
describes predicting its final loss from models trained with 1,000–10,000× less compute, and
landing *(reported)*.

The same ladder settles design questions cheaply: try two architectures at 100M parameters, and
if one has a better *slope* — not just a better intercept — it will win at 100B. A change that
only helps small models is discarded.

---

## 7. What the law does not predict

```
  per-token accuracy p, smooth in scale  ->  a task needing k tokens all correct = p^k
     p      k=1      k=5     k=10     k=20
""")
for p in (0.80, 0.85, 0.90, 0.95, 0.98, 0.99):
    W(f"  {p:>5.2f}" + "".join(f"{p**k:>9.3f}" for k in (1, 5, 10, 20)) + "\n")
W(f"""```

Loss is smooth and predictable. **Capabilities are not**, or not the way they are measured. Move
`p` smoothly from 0.80 to 0.99 and a 20-token task jumps from 1% to 82% — a "sudden emergence"
that is entirely the metric's threshold, not a discontinuity in the model. Some abilities really
do appear abruptly; many reported ones are this arithmetic. Either way, the loss curve tells you
almost nothing about *when a specific skill will arrive*, which is the honest limit of scaling
laws. → [chapter 15](../15-evaluation/)

---

## 8. Invariants

1. **`C ≈ 6ND`.** Two FLOPs forward, four backward, per parameter per token. Attention is extra.
2. **Loss is a power law in N, D and C** — straight on log-log **after every floor is subtracted**.
3. **The floor is `E`**, the entropy of text. Nothing buys below it.
4. **Compute-optimal is roughly tens of tokens per parameter**; the exact figure depends on the
   estimation method, and GPT-3 was an order of magnitude off.
5. **Deployment-optimal ≠ training-optimal.** Over-train small models, because inference cost is `N`.
6. **Fit a ladder, then extrapolate.** That is the tool's actual job.
7. **Loss is predictable; capabilities are not.** A smooth `p` makes a sharp `pᵏ`.
""")
open('planning.md', 'w').write(o.getvalue())
print("wrote planning.md", len(o.getvalue()), "chars")
