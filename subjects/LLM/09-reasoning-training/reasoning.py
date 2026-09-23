#!/usr/bin/env python3
"""Generates reasoning.md from live runs of rlvr.py. Run: python3 reasoning.py"""
import io, numpy as np
from math import comb
import rlvr as R
o = io.StringIO(); W = o.write

W(f"""# Reasoning training, traced

Every number here is produced by `rlvr.py`. Run `python3 reasoning.py` to regenerate.

The task is a stand-in for a multi-step derivation: a problem is a start token, and the correct
answer is a chain of `K` steps where each step applies a hidden rule to the previous one. A
response is a chain of `K` choices, `{R.A}` options each. **Reward is 1 if every step is right, 0
otherwise** — a checker, not a reward model. Two policies are trained with the same GRPO recipe:

- **one-shot** — a separate distribution over all `{R.A}^K` possible chains, per problem;
- **step-by-step** — one shared table `previous → next`, used at every step of every problem.

---

## 1. Chain of thought, as measured

```
""")
log = (0, 25, 50, 100, 200, 400); saved = {}
for k_ in (4, 6):
    R.set_problems(k_, shared_rule=True); R.rng = np.random.default_rng(0)
    W(f"  K={k_}: {R.A**k_:,} one-shot answers per problem (random guess {1/R.A**k_:.5f})\n")
    W(f"  {'GRPO steps':>11}{'one-shot':>11}{'step-by-step':>14}\n")
    one, cot = R.OneShot(), R.StepByStep(); accs = {}
    for step in range(401):
        if step in log: accs[step] = (R.accuracy(one), R.accuracy(cot))
        for prob in range(R.N_PROBLEMS): R.grpo_step(one, prob, lr=2.0); R.grpo_step(cot, prob, lr=1.0)
    for s_ in log: W(f"  {s_:>11}{accs[s_][0]:>11.3f}{accs[s_][1]:>14.3f}\n")
    saved[k_] = cot; W("\n")
W(f"""```

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
""")
R.set_problems(6, shared_rule=False); R.rng = np.random.default_rng(0)
one, cot = R.OneShot(), R.StepByStep()
for step in range(400):
    for prob in range(R.N_PROBLEMS): R.grpo_step(one, prob, lr=2.0); R.grpo_step(cot, prob, lr=1.0)
W(f"  K=6, six independent random chains, 400 steps:   one-shot {R.accuracy(one):.3f}   step-by-step {R.accuracy(cot):.3f}\n```\n\n")
W(f"""Same recipe, but each problem's correct chain is now unrelated to the others. Decomposition buys
**nothing** — both face the same one-in-4,096 haystack with an all-or-nothing reward, and the
shared table is now a liability, since one rule cannot fit six chains. This experiment was run
first, expecting the opposite, and it is kept because it says something true: **chain of thought is
not magic search.** It is transfer. It helps exactly when the steps recur — which in real
language, mathematics and code they overwhelmingly do.

---

## 2. GRPO: the group is the baseline

```
""")
R.set_problems(4, shared_rule=True); cot = saved[4]
r = np.array([0, 0, 1, 0, 1, 0, 0, 0], float)
W(f"  one prompt, a group of 8 samples, rewards   {r.astype(int)}\n")
W(f"  mean {r.mean():.3f}   std {r.std():.3f}\n")
W(f"  advantages (r − mean) / std                {np.round((r - r.mean())/r.std(), 2)}\n```\n\n")
W(f"""Two correct responses get pushed up, six wrong ones pushed down, and the baseline is simply the
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
  {'p':>5}{'n':>5}{'majority vote':>15}{'best-of-n':>11}
""")
for p_ in (0.3, 0.6, 0.9):
    for n in (1, 5, 15):
        maj = sum(comb(n, k_) * p_**k_ * (1-p_)**(n-k_) for k_ in range(n//2 + 1, n + 1))
        W(f"  {p_:>5.1f}{n:>5}{maj:>15.3f}{1-(1-p_)**n:>11.3f}\n")
W(f"""```

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
  {'K steps':>8}{'one-shot answers':>18}{'p(all right) at 90%/step':>27}{'at 99%/step':>13}
""")
for k_ in (1, 2, 4, 8, 16):
    W(f"  {k_:>8}{R.A**k_:>18,}{0.9**k_:>27.3f}{0.99**k_:>13.3f}\n")
W(f"""```

A sixteen-step derivation at 90% per step succeeds one time in five; at 99% it succeeds five times
in six. Reasoning training is largely about that per-step number — and about learning to notice
and undo a wrong step, which is the backtracking behaviour that appears, untaught, in RL-trained
reasoning models.

---

## 6. Distillation

```
""")
R.rng = np.random.default_rng(0)
p_single = R.accuracy(cot, 400); student = R.StepByStep()
traces = [(p, s) for p in range(R.N_PROBLEMS) for s in cot.sample(p, 30)[0] if R.verify(p, s)]
for _ in range(30):
    for p, s in traces: student.logprob_grad(p, [s], [1.0], 0.5)
W(f"  {len(traces)} correct traces sampled from the RL-trained policy\n  plain SFT of a fresh policy on those traces\n\n  student accuracy {R.accuracy(student):.3f}     teacher {p_single:.3f}\n```\n\n")
W(f"""No RL, no verifier, no sampling loop at training time — just imitate correct reasoning traces.
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
""")
open('reasoning.md', 'w').write(o.getvalue())
print("wrote reasoning.md", len(o.getvalue()), "chars")
