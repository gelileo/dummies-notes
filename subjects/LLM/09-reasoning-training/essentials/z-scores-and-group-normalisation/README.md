# Essential · Z-scores and group normalisation

**Needed for:** GRPO's *"advantage = (reward − group mean) / group std"* in
[chapter 09](../../README.md).

## The z-score

Subtract the group's mean, divide by its standard deviation
([mean and std](../../../02-transformer-forward-pass/essentials/averages-and-normalization/)):

```
   rewards [0. 0. 1. 0. 1. 0. 0. 0.]
           mean 0.250  std 0.433
           z = (x - mean)/std = [-0.58 -0.58  1.73 -0.58  1.73 -0.58 -0.58 -0.58]
           z has mean -0.0 and std 1.0, always.

   scores  [2.  7.5 3.1 9.  4.4 1.2 6.  8.8]
           mean 5.250  std 2.842
           z = (x - mean)/std = [-1.14  0.79 -0.76  1.32 -0.3  -1.43  0.26  1.25]
           z has mean +0.0 and std 1.0, always.
```

Whatever the original units or scale, the result always has mean 0 and standard deviation 1. A
z-score answers *"how many standard deviations above or below the group is this one?"*

## Why GRPO does this to rewards

```
   8 samples for one prompt, rewards [0 0 1 0 1 0 0 0]
   advantages [-0.58 -0.58  1.73 -0.58  1.73 -0.58 -0.58 -0.58]
   1. the mean is the baseline: 'was this sample better than its siblings?' -- no critic
      network needed to estimate expected reward, the group estimates it.
   2. dividing by std puts every prompt on the same scale: a prompt where 1/8 succeed and
      one where 7/8 succeed both yield advantages of unit size, so neither dominates.
```

Two jobs at once. Subtracting the mean makes the group its own **baseline** — no separate value
network guessing the expected reward, the siblings *are* the estimate
([why baselines help](../../../08-preference-optimization/essentials/expectation-and-sampling/)).
Dividing by the standard deviation puts every prompt on the same footing: an easy prompt where
seven of eight succeed and a hard one where one of eight does both produce unit-sized advantages,
so neither dominates the update.

## The degenerate groups

```
   rewards [0 0 0 0 0 0 0 0]  std = 0.0  -> no signal: nothing to normalise, skip the update
   rewards [1 1 1 1 1 1 1 1]  std = 0.0  -> no signal: nothing to normalise, skip the update
   all-wrong: the model has nothing to learn from. all-right: nothing to improve.
   the informative prompts are the ones the model sometimes gets right -- its frontier.
```

All-right or all-wrong means zero standard deviation and no signal. The prompts that teach are
the ones on the model's frontier — solved sometimes. Real GRPO pipelines filter for exactly
those.

## Run it

```bash
python3 demo.py
```

## Terms

| Term | Meaning |
| --- | --- |
| **z-score / standard score** | `(x − mean) / std`. Distance from the group mean in units of standard deviation. |
| **standardise / normalise** | Transform a set of numbers to mean 0, std 1. |
| **group** | GRPO's set of `G` sampled responses to one prompt. |
| **group baseline** | The group's mean reward, used in place of a learned critic. |
| **advantage (GRPO)** | The z-scored reward within the group. |
| **frontier prompt** | One the model solves sometimes — the only kind that produces a non-zero advantage. |
