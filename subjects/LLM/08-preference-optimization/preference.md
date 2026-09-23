# Preference optimization, traced

Every number here is produced by `preference.py`. Run `python3 rlhf.py` to regenerate.

The setup is deliberately small enough to see through. The "policy" is a distribution over
**eight candidate responses** to one prompt. Each response has a length the reward model can
see, and a hidden **true quality** that only the humans doing comparisons can sense. In this
dataset longer responses happen to be better — up to a point — so a reward model trained on the
comparisons will learn something plausible and wrong, and we can measure exactly what the
policy does with that.

```
  response        length   true quality   (hidden from everything below)
  r0(len 3)            3           1.0
  r1(len 5)            5           2.0
  r2(len 8)            8           3.0
  r3(len 10)          10           4.5
  r4(len 12)          12           5.0
  r5(len 15)          15           5.5
  r6(len 20)          20           4.0
  r7(len 40)          40           2.0

  reference policy (the SFT model): uniform.   expected true quality 3.38
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
  300 comparisons.  features [length/10, 1].  learned weights [1.629 0.   ]

  response       true quality  RM reward
  r0(len 3)               1.0       0.49
  r1(len 5)               2.0       0.81
  r2(len 8)               3.0       1.30
  r3(len 10)              4.5       1.63
  r4(len 12)              5.0       1.95
  r5(len 15)              5.5       2.44
  r6(len 20)              4.0       3.26
  r7(len 40)              2.0       6.52

  agrees with the human on 77% of training pairs
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
    β (KL)  true quality  RM reward  KL to ref  mass on r7   top response
       0.0          2.00       6.50       2.06        1.00   r7(len 40)
       0.3          2.01       6.50       2.04        1.00   r7(len 40)
       1.0          2.16       6.18       1.67        0.92   r7(len 40)
       3.0          3.12       3.81       0.27        0.40   r7(len 40)
      10.0          3.36       2.67       0.02        0.19   r7(len 40)

  (untrained reference: true quality 3.38)
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
  baseline=False  |mean gradient| 0.641   typical scatter of one 16-sample estimate 0.623
  baseline=True   |mean gradient| 0.594   typical scatter of one 16-sample estimate 0.351
```

`reward − baseline` is the **advantage**. PPO estimates the baseline with a learned value network;
GRPO ([chapter 09](../09-reasoning-training/)) uses the mean of a group of samples.
→ [essentials: expectation and sampling](essentials/expectation-and-sampling/)

---

## 4. A better reward model

The hack came from two gaps: raters rarely saw `r7` (coverage), and the model could only express
"longer is better" (capacity). Fix both — show raters everything, add a squared-length feature:

```
  reward for r7 (junk):  before 6.52   now 1.31
  policy after RL:       true quality 4.28   top r6(len 20)   mass on r7 0.00
```

The hack is gone. **The reward model matters more than the RL algorithm** — every RL trick in
section 2 and 5 is downstream of what this thing can and cannot see. It is still imperfect: two
features of length cannot place `r5` above `r6`, so the policy settles on second-best.

---

## 5. PPO-style clipping

Cap how far the policy may move in one update:

```
  lr=3.0   clip=None   largest single-step move 0.375   final quality 4.00
  lr=3.0   clip=0.2    largest single-step move 0.153   final quality 4.00
  lr=30.0  clip=None   largest single-step move 1.727   final quality 4.00
  lr=30.0  clip=0.2    largest single-step move 0.424   final quality 4.00
```

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
  from the same 300 pairs:   true quality 4.62   KL to ref 0.40   top r4(len 12)   mass on r7 0.03

  response       reference   RLHF    DPO
  r0(len 3)          0.125  0.003  0.018
  r1(len 5)          0.125  0.004  0.029
  r2(len 8)          0.125  0.008  0.053
  r3(len 10)         0.125  0.014  0.155
  r4(len 12)         0.125  0.034  0.312
  r5(len 15)         0.125  0.184  0.311
  r6(len 20)         0.125  0.749  0.089
  r7(len 40)         0.125  0.004  0.034
```

DPO reaches a similar place — here a slightly better one, landing on `r4` — with none of the
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
