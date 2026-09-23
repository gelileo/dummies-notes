# Essential · Compounding probabilities

**Needed for:** *"a 20-step derivation at 90% per step"*, *"best-of-n with a verifier"*, and
*"majority vote"* in [chapter 09](../../README.md).

## All *k* steps must succeed: `pᵏ`

```
    per-step p      k=1      k=2      k=5     k=10     k=20     k=50
         0.900    0.900    0.810    0.590    0.349    0.122    0.005
         0.950    0.950    0.902    0.774    0.599    0.358    0.077
         0.990    0.990    0.980    0.951    0.904    0.818    0.605
         0.999    0.999    0.998    0.995    0.990    0.980    0.951
   independent steps multiply. at 90% per step, a 20-step task succeeds 12% of the time.
   at 99.9% it is 98%. long chains demand very high per-step reliability.
```

Independent successes multiply. Ninety percent per step sounds fine until you need twenty of them
in a row and get 12%. This single table explains why reasoning training is largely about raising
*per-step* reliability, and why long derivations are hard for everyone.

## Any one of *n* tries succeeds: `1 − (1−p)ⁿ`

```
        p      n=1      n=2      n=5     n=10     n=20    n=100
     0.01    0.010    0.020    0.049    0.096    0.182    0.634
     0.10    0.100    0.190    0.410    0.651    0.878    1.000
     0.30    0.300    0.510    0.832    0.972    0.999    1.000
     0.60    0.600    0.840    0.990    1.000    1.000    1.000
   the mirror image: failures multiply, so even p=0.01 reaches 63% with 100 tries.
   this is best-of-n with a verifier: sample many, keep any that checks out.
```

The mirror image: *failures* multiply, so the chance that all `n` attempts fail shrinks fast.
Even a 1% per-try success reaches 63% with a hundred tries. This is **best-of-n with a
verifier** — sample many answers, keep any one that checks out — and it always helps.

## A majority must agree: the binomial

```
        p      n=1      n=3      n=5     n=11     n=21    n=101
     0.30    0.300    0.216    0.163    0.078    0.026    0.000
     0.45    0.450    0.425    0.407    0.367    0.321    0.156
     0.55    0.550    0.575    0.593    0.633    0.679    0.844
     0.70    0.700    0.784    0.837    0.922    0.974    1.000
     0.90    0.900    0.972    0.991    1.000    1.000    1.000
   above 0.5, more votes sharpen toward certainty; below 0.5, more votes sharpen toward
   certain FAILURE. majority voting amplifies whatever side of 50% you are on.
   (worst case for voting: every wrong answer is the same wrong answer.)
```

**Voting amplifies whichever side of 50% you are on.** Above it, more votes push toward
certainty; below it, toward certain failure. This is why majority voting (self-consistency) is
only a win for tasks the model already gets right more often than not — and why a verifier,
which needs just one success, is the stronger tool when one exists.

## Where the formula comes from

```
   P(exactly 3 of 5 succeed) = C(5,3) * p^3 * (1-p)^2
                              = 10 * 0.2160 * 0.1600 = 0.3456
   C(5,3) = 10 is the number of ways to choose which 3 of the 5 succeed.
   'majority' just sums this over every k above n/2.
```

`C(n, k)` counts the ways to choose *which* `k` of the `n` succeed; `pᵏ(1−p)ⁿ⁻ᵏ` is the probability
of any one such pattern. "Majority" sums over every `k` above `n/2`.

## Run it

```bash
python3 demo.py
```

## Terms

| Term | Meaning |
| --- | --- |
| **independent** | One outcome does not affect another. The assumption behind every formula here. |
| **`pᵏ`** | Probability that `k` independent things all succeed. |
| **`1 − (1−p)ⁿ`** | Probability that at least one of `n` independent tries succeeds. |
| **binomial distribution** | The probability of exactly `k` successes in `n` tries: `C(n,k)·pᵏ·(1−p)ⁿ⁻ᵏ`. |
| **`C(n, k)`** | "n choose k": the number of ways to pick `k` items out of `n`. |
| **majority vote / self-consistency** | Sample several answers, return the most common. Helps only when `p > 0.5`. |
| **best-of-n** | Sample several, keep one a verifier accepts. Always helps, needs a verifier. |
