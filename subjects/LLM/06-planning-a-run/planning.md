# Planning a run, traced

Every number here is computed by `scaling.py`. Run `python3 planning.py` to regenerate.

One function carries this chapter — Chinchilla's **published** fit of loss against model size
and data (Hoffmann et al., 2022):

```
  L(N, D) = E + A / N^α + B / D^β
  E = 1.69   A = 406.4   B = 410.7   α = 0.34   β = 0.28
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
  Llama-3-8B:   6 × 8.03e+09 × 1.5e+13  =  7.23e+23 FLOPs
  at 40% of an H100's 990 TFLOP/s:      506,944 GPU-hours
  on 1,000 GPUs:                        21 days
```

Meta reported about 1.3M GPU-hours for the 8B model *(reported)*. The gap is attention FLOPs —
`6ND` counts only the weight matrices, and attention's `QKᵀ` grows with sequence length — plus
real utilisation below 40%. `6ND` is the right first estimate and a known underestimate.
→ [essentials: FLOPs and units](essentials/flops-and-units/)

---

## 2. The law, tabulated

```
  N (params)     D = 1e11    D = 1e12    D = 1e13
       1e+08       2.806       2.644       2.558
       1e+09       2.386       2.223       2.138
       1e+10       2.193       2.031       1.946
       1e+11       2.106       1.943       1.858
```

Read down a column: more parameters, lower loss, with diminishing returns. Read across a row:
more data, lower loss, likewise. Every entry tends to **`E = 1.69`** — the irreducible loss, the
entropy of the text itself ([chapter 03](../03-training-objective/)). No amount of either buys
its way below that.

---

## 3. Straight lines on log-log axes — if you subtract the whole floor

A power law `y = a·xᵇ` is a straight line of slope `b` when both axes are logarithmic. That is
the test scaling-law papers pass, and it is easy to run wrongly:

```
    log10 N  log10(L − E)  log10(L − E − B/D^β)
       8.00        -0.061                -0.111
       8.50        -0.209                -0.281
       9.00        -0.349                -0.451
       9.50        -0.477                -0.621
      10.00        -0.592                -0.791
      10.50        -0.691                -0.961
      11.00        -0.775                -1.131
  fitted slope:  -0.239         -0.340        (true exponent −α = -0.34)
```

Subtract only `E` and the fit says `−0.24`. The data term `B/D^β` is a constant at fixed `D` —
a second floor you did not remove — and it **bends the line**. Subtract it too and the slope is
`−0.34`, the law's exponent, exactly. A curve that looks "roughly straight" on log-log axes is a
hypothesis; the residuals decide.
→ [essentials: power laws and log-log](essentials/power-laws-and-log-log/)

---

## 4. Compute-optimal: given a budget, how big a model and how much data?

Fix `C = 6ND`, so `D = C / 6N`, and minimise `L(N, C/6N)` over `N`:

```
  budget C     best N      best D     D/N     loss      175B model at the same budget
     1e+21    1.82e+09   9.16e+10      50    2.329      D = 9.5e+08, loss 3.008
     1e+22    5.17e+09   3.22e+11      62    2.139      D = 9.5e+09, loss 2.411
     1e+23    1.46e+10   1.14e+12      78    2.005      D = 9.5e+10, loss 2.097
     1e+24    4.14e+10   4.03e+12      97    1.911      D = 9.5e+11, loss 1.933
```

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
                1.6e+11       20     2.164         7.7e+21
                4.0e+11       50     2.096         1.9e+22
                1.0e+12      125     2.044         4.8e+22
                4.0e+12      500     1.986         1.9e+23
                1.5e+13     1875     1.949         7.2e+23
```

Llama-3-8B's 15T tokens is roughly **1,900 tokens per parameter** — some 90× past
compute-optimal — and the loss is still falling at the end of that table. That is deliberate:
pay more once in training to get a small model that is cheap to serve. *Training-optimal and
deployment-optimal are different points*, and the industry moved to the second.

---

## 6. The actual use: predict before you spend

Train a ladder of small models, fit the line, read off where the big one lands:

```
  N = 1e+08   C = 1.2e+18   loss 3.487
  N = 3e+08   C = 1.1e+19   loss 2.973
  N = 1e+09   C = 1.2e+20   loss 2.586
  N = 3e+09   C = 1.1e+21   loss 2.329

  predicted for a 70B model at C = 5.9e+23:  1.936
  the law evaluated there:                    1.937
```

This demonstrates the **procedure** on a known law, not the law's truth — the ladder is generated
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
   0.80    0.800    0.328    0.107    0.012
   0.85    0.850    0.444    0.197    0.039
   0.90    0.900    0.590    0.349    0.122
   0.95    0.950    0.774    0.599    0.358
   0.98    0.980    0.904    0.817    0.668
   0.99    0.990    0.951    0.904    0.818
```

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
