# Reasoning training, traced

Every number here is produced by `rlvr.py`. Run `python3 reasoning.py` to regenerate.

The task is a stand-in for a multi-step derivation: a problem is a start token, and the correct
answer is a chain of `K` steps where each step applies a hidden rule to the previous one. A
response is a chain of `K` choices, `4` options each. **Reward is 1 if every step is right, 0
otherwise** — a checker, not a reward model. Two policies are trained with the same GRPO recipe:

- **one-shot** — a separate distribution over all `4^K` possible chains, per problem;
- **step-by-step** — one shared table `previous → next`, used at every step of every problem.

---

## 1. Chain of thought, as measured

```
  K=4: 256 one-shot answers per problem (random guess 0.00391)
   GRPO steps   one-shot  step-by-step
            0      0.003         0.003
           25      0.008         0.988
           50      0.620         0.991
          100      0.830         0.994
          200      0.998         0.999
          400      0.999         1.000

  K=6: 4,096 one-shot answers per problem (random guess 0.00024)
   GRPO steps   one-shot  step-by-step
            0      0.000         0.000
           25      0.001         0.938
           50      0.000         0.997
          100      0.001         0.999
          200      0.000         0.999
          400      0.002         1.000

```

At `K=4` the step-by-step policy is essentially solved after 25 steps; one-shot needs 200. At
`K=6` one-shot has found a third of the answers after 400 steps; step-by-step has all of them.

**Why.** One-shot must discover each problem's 4,096-way answer separately, and until it stumbles
on one there is no gradient at all — every group of samples scores zero. Step-by-step has
sixteen numbers to learn: the rule. A success on *any* problem teaches all of them, because the
same table is used everywhere. That is the honest mechanism behind chain of thought: intermediate
steps are **reusable sub-computations**, and factoring a problem into them lets the model bring
what it learned everywhere to bear on each step.

## 1b. The control: when nothing recurs

```
  K=6, six independent random chains, 400 steps:   one-shot 0.000   step-by-step 0.012
```

Same recipe, but each problem's correct chain is now unrelated to the others. Decomposition buys
**nothing** — both face the same one-in-4,096 haystack with an all-or-nothing reward, and the
shared table is now a liability, since one rule cannot fit six chains. This experiment was run
first, expecting the opposite, and it is kept because it says something true: **chain of thought is
not magic search.** It is transfer. It helps exactly when the steps recur — which in real
language, mathematics and code they overwhelmingly do.

---

## 2. GRPO: the group is the baseline

```
  one prompt, a group of 8 samples, rewards   [0 0 1 0 1 0 0 0]
  mean 0.250   std 0.433
  advantages (r − mean) / std                [-0.58 -0.58  1.73 -0.58  1.73 -0.58 -0.58 -0.58]
```

Two correct responses get pushed up, six wrong ones pushed down, and the baseline is simply the
group's mean — no value network estimating expected reward, the siblings *are* the estimate.
Dividing by the standard deviation puts easy and hard prompts on the same scale. When a group is
all-right or all-wrong there is no signal at all, which is why the prompts that teach most are the
ones on the model's frontier: sometimes solved.
→ [essentials: z-scores](essentials/z-scores-and-group-normalisation/) ·
[chapter 08's policy gradient](../08-preference-optimization/essentials/the-policy-gradient/)

---

## 3. The reward is a checker

`verify(problem, response) → 1.0 or 0.0`. An exact-match answer, a unit test, a proof checker. There
is no reward model to have a blind spot, so there is nothing to hack except the checker itself. This
is the whole difference from [chapter 08](../08-preference-optimization/), and it is why maths and
code got reasoning models first: they are the domains where a checker exists.

---

## 4. Test-time compute

Given a single-sample accuracy `p`, exact results for two ways of spending more samples:

```
      p    n  majority vote  best-of-n
    0.3    1          0.300      0.300
    0.3    5          0.163      0.832
    0.3   15          0.050      0.995
    0.6    1          0.600      0.600
    0.6    5          0.683      0.990
    0.6   15          0.787      1.000
    0.9    1          0.900      0.900
    0.9    5          0.991      1.000
    0.9   15          1.000      1.000
```

*(Majority is the worst case, where every wrong answer is the same wrong answer; best-of-n
assumes a verifier can recognise a correct sample.)*

**Below `p = 0.5`, majority voting makes things worse.** Above it, it sharpens fast. **Best-of-n
with a verifier always helps** — one right sample is enough — which is again why verifiable domains
led. Both trade inference compute for accuracy, and that trade is the second scaling axis this
chapter is about: not a bigger model, but more thinking from the same one.
→ [essentials: compounding probabilities](essentials/compounding-probabilities/)

---

## 5. Long chains compound

```
   K steps  one-shot answers   p(all right) at 90%/step  at 99%/step
         1                 4                      0.900        0.990
         2                16                      0.810        0.980
         4               256                      0.656        0.961
         8            65,536                      0.430        0.923
        16     4,294,967,296                      0.185        0.851
```

A sixteen-step derivation at 90% per step succeeds one time in five; at 99% it succeeds five times
in six. Reasoning training is largely about that per-step number — and about learning to notice
and undo a wrong step, which is the backtracking behaviour that appears, untaught, in RL-trained
reasoning models.

---

## 6. Distillation

```
  179 correct traces sampled from the RL-trained policy
  plain SFT of a fresh policy on those traces

  student accuracy 1.000     teacher 0.999
```

No RL, no verifier, no sampling loop at training time — just imitate correct reasoning traces.
The expensive exploration was paid once by the teacher. This is how most small "reasoning" models
are actually made, and it is why a strong open reasoning model's traces are so valuable.

---

## 7. What is not shown here

**Faithfulness.** The written chain of thought is not guaranteed to be the computation that
produced the answer. In this toy the steps *are* the computation, by construction; in a language
model they are tokens the model chose to emit, and they can rationalise rather than reveal. Treat
a model's explanation as evidence, not proof.

**Where verifiers run out.** Writing, judgement, taste — no checker exists, and you are back to
[chapter 08](../08-preference-optimization/)'s learned rewards with all their blind spots. The
frontier of this method is exactly the frontier of what can be checked.

---

## 8. Invariants

1. **Chain of thought is transfer of reusable steps**, not search. It helps when steps recur — measured both ways.
2. **GRPO: the group is the baseline.** Normalise rewards within the group; no critic.
3. **The reward is a checker.** Nothing to hack but the checker. Hence maths and code first.
4. **Frontier prompts teach.** All-right and all-wrong groups carry no gradient.
5. **Best-of-n with a verifier always helps; majority vote only above 50%.** Exact binomial.
6. **Per-step reliability compounds.** `0.9¹⁶ ≈ 0.19`. Raise the per-step number.
7. **Distil.** Pay for exploration once; imitate the traces.
