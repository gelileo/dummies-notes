# Essential · Expected value, sampling, and baselines

**Needed for:** *"maximise expected reward"*, *"estimate the gradient from 16 samples"*, and
*"the advantage is reward minus a baseline"* in [chapter 08](../../README.md).

## Expected value

```
   outcomes      [1.  2.  3.  4.5 5.  5.5 4.  2. ]
   probabilities [0.05 0.05 0.1  0.2  0.25 0.2  0.1  0.05]   (sum 1.00)
   E[value] = sum(p * value) = 4.200
   'if you drew from this distribution forever, this is the average you would see.'
```

The probability-weighted average: what you would see on average if you drew from the
distribution forever. "The policy's expected reward" is exactly this, with `value` = reward and
`p` = the policy's probabilities.

## You rarely know `p` — so sample and average

```
    samples n  estimate    error   typical error over 500 trials
            1     5.000    0.800                           1.290
            4     3.625    0.575                           0.651
           16     3.875    0.325                           0.319
           64     4.234    0.034                           0.167
          256     4.223    0.023                           0.079
         1024     4.192    0.008                           0.041
   the estimate is unbiased at any n, and its scatter shrinks like 1/sqrt(n).
   a batch of 16 responses in RLHF is a Monte Carlo estimate with n=16. noisy.
```

Draw `n` samples, average what you see. That is a **Monte Carlo estimate**: unbiased at any `n`,
with scatter shrinking like `1/√n`. In RLHF each step samples a handful of responses from the
policy and scores them — a Monte Carlo estimate with `n` in the tens. It is noisy, and everything
about the algorithm design is about living with that noise.

## Baselines: same expectation, less scatter

```
   estimating E[value * f] where f is something else we care about (a gradient, say).
   subtract a constant b from value first: E[(value - b) * f] = E[value*f] - b*E[f].
   if E[f] = 0, the baseline changes NOTHING in expectation -- but can cut the scatter.
   no baseline (b=0)    mean [-0.161 -0.11  -0.119  0.044  0.21   0.259 -0.015 -0.109]
                        scatter 0.897
   b = mean value       mean [-0.163 -0.109 -0.12   0.06   0.197  0.264 -0.02  -0.11 ]
                        scatter 0.285
   same mean, smaller scatter. that is exactly what the 'advantage' in policy
   gradients does: reward minus a baseline, with the baseline's gradient being zero.
```

If you are estimating `E[value · f]` and `E[f] = 0`, then subtracting *any* constant `b` from
`value` leaves the expectation unchanged — the extra term is `b · E[f] = 0` — but can shrink the
scatter dramatically. In policy gradients `f` is the gradient of log-probability, whose
expectation under the policy is exactly zero. So **reward minus a baseline** — the **advantage** —
gives the same direction with far less noise. Every RL method for LLMs does this; GRPO uses the
group mean as the baseline.

## Run it

```bash
python3 demo.py
```

## Terms

| Term | Meaning |
| --- | --- |
| **expected value** `E[X]` | Probability-weighted average of the outcomes. |
| **Monte Carlo estimate** | Approximate an expectation by sampling and averaging. Unbiased; noise ∝ `1/√n`. |
| **unbiased** | Right on average, even if wrong on any one draw. |
| **variance** | How much an estimate scatters around its mean. Owned by [chapter 02](../../../02-transformer-forward-pass/essentials/averages-and-normalization/). |
| **baseline** | A constant subtracted from the reward before use. Zero effect on the expected gradient, large effect on its variance. |
| **advantage** | Reward minus baseline. What policy-gradient methods actually multiply by. |
