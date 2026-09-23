#!/usr/bin/env python3
"""Generates preference.md from live runs of preference.py. Run: python3 rlhf.py"""
import io, numpy as np
import preference as P
o = io.StringIO(); W = o.write
np.set_printoptions(precision=3, suppress=True)
R, NAMES, LENGTH, QUALITY = P.R, P.NAMES, P.LENGTH, P.QUALITY
ref_logits = np.zeros(R); ref = P.softmax(ref_logits)

W(f"""# Preference optimization, traced

Every number here is produced by `preference.py`. Run `python3 rlhf.py` to regenerate.

The setup is deliberately small enough to see through. The "policy" is a distribution over
**eight candidate responses** to one prompt. Each response has a length the reward model can
see, and a hidden **true quality** that only the humans doing comparisons can sense. In this
dataset longer responses happen to be better — up to a point — so a reward model trained on the
comparisons will learn something plausible and wrong, and we can measure exactly what the
policy does with that.

```
  response        length   true quality   (hidden from everything below)
""")
for i in range(R): W(f"  {NAMES[i]:<14}{LENGTH[i]:>8.0f}{QUALITY[i]:>14.1f}\n")
W(f"""
  reference policy (the SFT model): uniform.   expected true quality {P.expected(ref, QUALITY):.2f}
```

The true best response is `r5` (quality 5.5). `r7` is forty tokens of junk.

---

## 1. Humans compare pairs; a reward model learns from the comparisons

Raters never score a response in isolation — they say which of two is better. That is a
**pairwise preference**, and the standard model of it is **Bradley–Terry**: the probability that
A beats B is `σ(score_A − score_B)`. A reward model is a network trained so that its scores
reproduce the human choices. → [essentials: sigmoid and pairwise preference](essentials/sigmoid-and-pairwise-preference/)

Here the reward model can see only a response's *length*:

```
""")
P.rng = np.random.default_rng(0)
pairs = P.collect_pairs(300)
feats = np.stack([LENGTH / 10, np.ones(R)], 1)
w = P.train_reward_model(pairs, feats); reward = feats @ w
W(f"  {len(pairs)} comparisons.  features [length/10, 1].  learned weights {w}\n\n")
W(f"  {'response':<14}{'true quality':>13}{'RM reward':>11}\n")
for i in range(R): W(f"  {NAMES[i]:<14}{QUALITY[i]:>13.1f}{reward[i]:>11.2f}\n")
agree = np.mean([reward[c] > reward[r_] for c, r_ in pairs])
W(f"""
  agrees with the human on {agree:.0%} of training pairs
```

Two things are true at once. **The reward model looks good** — 77% agreement is respectable for
noisy human data. And **it has learned the wrong thing**: in the data longer *was* better, so it
concluded longer is better, and it extrapolates that to `r7`, which the raters were almost never
shown. Forty tokens of junk gets the highest reward of all.

---

## 2. Policy gradient: push up what the reward model likes

The policy is trained to maximise expected reward, minus `β` times its KL divergence from the
reference — a penalty for wandering away from where the reward model was trained.
→ [essentials: the policy gradient](essentials/the-policy-gradient/)

```
  {'β (KL)':>8}{'true quality':>14}{'RM reward':>11}{'KL to ref':>11}{'mass on r7':>12}   top response
""")
for beta in (0.0, 0.3, 1.0, 3.0, 10.0):
    P.rng = np.random.default_rng(1)
    pol, _ = P.reinforce(reward, 300, 0.3, ref_logits, beta=beta); p = P.softmax(pol)
    W(f"  {beta:>8}{P.expected(p, QUALITY):>14.2f}{P.expected(p, reward):>11.2f}{P.kl(p, ref):>11.2f}{p[7]:>12.2f}   {NAMES[p.argmax()]}\n")
W(f"""
  (untrained reference: true quality {P.expected(ref, QUALITY):.2f})
```

**`β = 0` is reward hacking in one line.** The policy collapses onto `r7`: maximal reward-model
score, and a true quality *below the untrained model*. It did exactly what it was told — and what
it was told was wrong. The optimiser is very good at finding the reward model's blind spot,
because that is precisely where the reward is highest.

**The KL penalty is the leash**, and look at how strong it has to be. The reward gap is so large
that `β = 0.3` and `β = 1.0` barely restrain the policy. At `β = 10` it stays near the reference —
and stops improving. The leash costs exactly what it protects; you cannot tune it without a
better reward model.

---

## 3. Why a baseline

A policy-gradient step is an estimate from a handful of samples. Subtracting the batch's mean
reward before using it changes nothing in expectation and reduces the noise:

```
""")
P.rng = np.random.default_rng(2)
p0 = P.softmax(ref_logits)
for bl in (False, True):
    ests = []
    for _ in range(2000):
        idx = P.rng.choice(R, 16, p=p0); rw = reward[idx]
        adv = rw - (rw.mean() if bl else 0.0); g = np.zeros(R)
        for k, a in zip(idx, adv):
            onehot = np.zeros(R); onehot[k] = 1; g += a * (onehot - p0)
        ests.append(g / 16)
    ests = np.array(ests); mean = ests.mean(0); spread = np.sqrt(((ests - mean)**2).sum(1)).mean()
    W(f"  baseline={str(bl):<5}  |mean gradient| {np.linalg.norm(mean):.3f}   typical scatter of one 16-sample estimate {spread:.3f}\n")
W(f"""```

`reward − baseline` is the **advantage**. PPO estimates the baseline with a learned value network;
GRPO ([chapter 09](../09-reasoning-training/)) uses the mean of a group of samples.
→ [essentials: expectation and sampling](essentials/expectation-and-sampling/)

---

## 4. A better reward model

The hack came from two gaps: raters rarely saw `r7` (coverage), and the model could only express
"longer is better" (capacity). Fix both — show raters everything, add a squared-length feature:

```
""")
P.rng = np.random.default_rng(3)
feats2 = np.stack([LENGTH / 10, (LENGTH / 10)**2, np.ones(R)], 1)
pairs2 = P.collect_pairs(300, exclude_long=False)
w2 = P.train_reward_model(pairs2, feats2); reward2 = feats2 @ w2
pol, _ = P.reinforce(reward2, 300, 0.3, ref_logits, beta=0.3); p_rlhf = P.softmax(pol)
W(f"  reward for r7 (junk):  before {reward[7]:.2f}   now {reward2[7]:.2f}\n")
W(f"  policy after RL:       true quality {P.expected(p_rlhf, QUALITY):.2f}   top {NAMES[p_rlhf.argmax()]}   mass on r7 {p_rlhf[7]:.2f}\n")
W(f"""```

The hack is gone. **The reward model matters more than the RL algorithm** — every RL trick in
section 2 and 5 is downstream of what this thing can and cannot see. It is still imperfect: two
features of length cannot place `r5` above `r6`, so the policy settles on second-best.

---

## 5. PPO-style clipping

Cap how far the policy may move in one update:

```
""")
for lr_ in (3.0, 30.0):
    for clip in (None, 0.2):
        P.rng = np.random.default_rng(4)
        pol = ref_logits.copy(); moves = []; qs = []
        for _ in range(60):
            before = P.softmax(pol); pol, _ = P.reinforce(reward2, 1, lr_, pol, beta=0.3, clip=clip)
            after = P.softmax(pol); moves.append(np.abs(after - before).sum()); qs.append(P.expected(after, QUALITY))
        W(f"  lr={lr_:<5} clip={str(clip):<5}  largest single-step move {np.max(moves):.3f}   final quality {qs[-1]:.2f}\n")
W(f"""```

At a sane step size clipping changes nothing. At ten times the step, the unclipped policy moves by
whole probability masses in a single update; the clipped one is held to a bounded move. Both land
in the same place *here* — eight responses and a smooth reward are hard to break — but on a real
model that unbounded lurch is where training collapses. PPO's clipped objective exists to turn a
too-large update into a bounded one.

---

## 6. DPO: skip the reward model

Direct Preference Optimization takes the preference pairs and a closed-form loss —
`−log σ(β · [log π/π_ref (chosen) − log π/π_ref (rejected)])` — and optimises the policy directly. No
reward model, no sampling loop:

```
""")
P.rng = np.random.default_rng(5)
pol = P.dpo(pairs2, ref_logits); p_dpo = P.softmax(pol)
W(f"  from the same {len(pairs2)} pairs:   true quality {P.expected(p_dpo, QUALITY):.2f}   KL to ref {P.kl(p_dpo, ref):.2f}   top {NAMES[p_dpo.argmax()]}   mass on r7 {p_dpo[7]:.2f}\n\n")
W(f"  {'response':<14}{'reference':>10}{'RLHF':>7}{'DPO':>7}\n")
for i in range(R): W(f"  {NAMES[i]:<14}{ref[i]:>10.3f}{p_rlhf[i]:>7.3f}{p_dpo[i]:>7.3f}\n")
W(f"""```

DPO reaches a similar place — here {'a slightly better one' if P.expected(p_dpo, QUALITY) > P.expected(p_rlhf, QUALITY) else 'a comparable one'}, landing on `{NAMES[p_dpo.argmax()].split('(')[0]}` — with none of the
machinery. It is simpler and more stable, which is why it spread fast. The trade: it is
**offline**. It learns only from the pairs it was given, while RLHF keeps sampling *new*
responses and scoring them, and so can improve beyond the dataset — or, as section 2 showed,
hack it.

---

## 7. Where the values come from

Nothing in this chapter decides *what "better" means*. The raters do, following instructions
someone wrote; or a model does, following a written constitution (RLAIF / Constitutional AI).
The reward model compresses those judgements; the policy optimises the compression. This is the
one place in the pipeline where a model's values and refusals are actually set — and it is set
by the rater guidelines and the prompt distribution more than by any algorithm above.

---

## 8. Invariants

1. **Preferences, not scores.** Humans compare; Bradley–Terry turns comparisons into a reward model.
2. **The policy will find the reward model's blind spot.** That is not a bug in RL; it is RL working.
3. **KL to the reference is the leash**, and its strength is a trade-off with improvement.
4. **Advantage = reward − baseline.** Same expectation, less noise. Everyone does it.
5. **The reward model matters more than the algorithm.** Coverage and capacity fixed the hack; nothing else did.
6. **Clipping bounds the per-step move.** Invisible when the step is sane; decisive when it is not.
7. **DPO trades the sampling loop for an offline loss.** Simpler, stabler, bounded by its data.
""")
open('preference.md', 'w').write(o.getvalue())
print("wrote preference.md", len(o.getvalue()), "chars")
