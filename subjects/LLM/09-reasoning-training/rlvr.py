#!/usr/bin/env python3
"""Reasoning training, measured. The task: a 'problem' is a hidden sequence of k correct
choices (think: k steps of a derivation). A response is a sequence of k choices; reward is
1 if ALL are right, else 0 -- a verifiable reward, no reward model. We compare answering in
one shot vs step by step (chain of thought), train with GRPO (group-normalised advantages,
no critic), and then measure what spending more compute at inference buys. numpy.

Run: python3 rlvr.py
"""
import numpy as np
from math import comb
rng = np.random.default_rng(0)

A = 4                              # options per step
N_PROBLEMS = 6
K = 4                              # steps per problem
RULE = (1, 3)                      # the hidden shared rule: next = (a*prev + b) mod A
START = np.random.default_rng(0).integers(0, A, N_PROBLEMS)   # each problem begins somewhere different
PROBLEMS = None

def set_problems(k, shared_rule):
    """shared_rule=True: every problem's correct chain follows next = f(prev) from its own start --
    the same sub-computation recurs. False: each chain is independent random -- nothing recurs."""
    global K, PROBLEMS
    K = k
    if shared_rule:
        a, b = RULE; chains = []
        for s0 in START:
            c, prev = [], int(s0)
            for _ in range(K): prev = (a*prev + b) % A; c.append(prev)
            chains.append(c)
        PROBLEMS = np.array(chains)
    else:
        PROBLEMS = np.random.default_rng(0).integers(0, A, (N_PROBLEMS, K))
set_problems(K, True)

def softmax(z): e = np.exp(z - z.max(-1, keepdims=True)); return e / e.sum(-1, keepdims=True)

# ------------------------------------------------------------------ two policies
class OneShot:
    """Emit the whole K-tuple at once: a softmax over all A^K answers, per problem."""
    def __init__(self): self.logits = np.zeros((N_PROBLEMS, A**K))
    def sample(self, prob, n):
        p = softmax(self.logits[prob]); idx = rng.choice(A**K, n, p=p)
        return [np.array(np.unravel_index(i, [A]*K)) for i in idx], idx
    def logprob_grad(self, prob, idx, adv, lr):
        p = softmax(self.logits[prob]); g = np.zeros(A**K)
        for i, a in zip(idx, adv):
            oh = np.zeros(A**K); oh[i] = 1; g += a * (oh - p)
        self.logits[prob] += lr * g / len(idx)

class StepByStep:
    """Emit one step at a time, each conditioned on the previous token. ONE table [prev -> next],
    shared across steps and problems: a step learned anywhere is a step learned everywhere."""
    def __init__(self): self.logits = np.zeros((A, A))                  # [prev choice, next choice]
    def sample(self, prob, n):
        outs = []
        for _ in range(n):
            seq, prev = [], int(START[prob])
            for t in range(K):
                p = softmax(self.logits[prev]); c = rng.choice(A, p=p); seq.append(c); prev = c
            outs.append(np.array(seq))
        return outs, None
    def logprob_grad(self, prob, seqs, adv, lr):
        g = np.zeros_like(self.logits)
        for seq, a in zip(seqs, adv):
            prev = int(START[prob])
            for c in seq:
                p = softmax(self.logits[prev]); oh = np.zeros(A); oh[c] = 1
                g[prev] += a * (oh - p); prev = c
        self.logits += lr * g / len(seqs)

def verify(prob, seq): return float(np.array_equal(seq, PROBLEMS[prob]))

def grpo_step(policy, prob, G=8, lr=1.0, beta=0.0):
    """Sample a GROUP of G responses, score each 0/1, advantage = (r - mean)/std. No critic."""
    seqs, idx = policy.sample(prob, G)
    r = np.array([verify(prob, s) for s in seqs])
    if r.std() == 0: return r.mean()           # all right or all wrong: no signal this step
    adv = (r - r.mean()) / (r.std() + 1e-8)
    policy.logprob_grad(prob, idx if idx is not None else seqs, adv, lr)
    return r.mean()

def accuracy(policy, n=200):
    return np.mean([verify(p, s) for p in range(N_PROBLEMS) for s in policy.sample(p, n)[0]])

if __name__ == "__main__":
    print(f"{N_PROBLEMS} problems, each a hidden chain of {K} steps with {A} options per step "
          f"({A**K} possible one-shot answers). reward = 1 iff all {K} steps right.\n")

    print("=== 1. one-shot vs step-by-step, same GRPO recipe ===")
    print("   problems: 6 start tokens; the correct chain applies a hidden rule next = f(prev) K times.")
    print("   one-shot: a separate softmax over all A^K answers PER PROBLEM.")
    print("   step-by-step: one shared table prev -> next, used at every step of every problem.\n")
    log = (0, 25, 50, 100, 200, 400)
    saved = {}
    for k_ in (4, 6):
        set_problems(k_, shared_rule=True)
        print(f"   K={K}: {A**K:,} one-shot answers per problem (random guess {1/A**K:.5f})")
        print(f"   {'GRPO steps':>11}{'one-shot acc':>14}{'step-by-step acc':>18}")
        one, cot = OneShot(), StepByStep(); accs = {}
        for step in range(401):
            if step in log: accs[step] = (accuracy(one), accuracy(cot))
            for prob in range(N_PROBLEMS):
                grpo_step(one, prob, lr=2.0); grpo_step(cot, prob, lr=1.0)
        for s_ in log: print(f"   {s_:>11}{accs[s_][0]:>14.3f}{accs[s_][1]:>18.3f}")
        saved[k_] = cot
        print()
    print("   one-shot must discover each problem's 4,096-way answer separately. step-by-step has")
    print("   16 numbers to learn -- the rule -- and a success on ANY problem teaches all of them.")
    print("   that is the honest mechanism of chain of thought: intermediate steps are REUSABLE")
    print("   sub-computations, so the model brings knowledge from everywhere to each step.\n")

    print("=== 1b. control: when nothing recurs, decomposition buys nothing ===")
    set_problems(6, shared_rule=False)
    one, cot = OneShot(), StepByStep()
    for step in range(400):
        for prob in range(N_PROBLEMS): grpo_step(one, prob, lr=2.0); grpo_step(cot, prob, lr=1.0)
    print(f"   K=6, independent random chains, 400 steps:  one-shot {accuracy(one):.3f}   step-by-step {accuracy(cot):.3f}")
    print("   with an all-or-nothing reward and no shared structure, both face the same 1-in-4096")
    print("   haystack, and the shared table is now a liability (one rule cannot fit six chains).")
    print("   chain of thought is not magic search. it is transfer of reusable steps.")
    set_problems(4, shared_rule=True); cot = saved[4]

    print("\n=== 2. why the group: GRPO's advantage is 'better than my siblings' ===")
    r = np.array([0, 0, 1, 0, 1, 0, 0, 0], float)
    print(f"   group of 8 rewards {r.astype(int)}   mean {r.mean():.3f}   std {r.std():.3f}")
    print(f"   advantages (r - mean)/std: {np.round((r - r.mean())/r.std(), 2)}")
    print("   the two correct responses get pushed up, the six wrong ones pushed down, and the")
    print("   baseline is the group mean -- no critic network to estimate expected reward. when")
    print("   a group is all-right or all-wrong there is no signal, which is why problems near")
    print("   the model's frontier (sometimes solved) teach the most.")

    print("\n=== 3. the reward needs no model: it is a checker ===")
    print("   verify(problem, response) -> 1.0 or 0.0. exact-match answer, unit tests, a proof")
    print("   checker. nothing to hack except the checker itself. (chapter 08's reward model")
    print("   was the weak point; here there isn't one.)")

    print("\n=== 4. test-time compute: spend more samples, get more right ===")
    print("   given single-sample accuracy p, exact binomial results (majority: worst case, all")
    print("   wrong answers agree; best-of-n: a verifier picks any correct sample):")
    print(f"   {'p':>6}{'n':>5}{'majority vote':>15}{'best-of-n':>11}")
    for p_ in (0.3, 0.6, 0.9):
        for n in (1, 5, 15):
            maj = sum(comb(n, k_) * p_**k_ * (1-p_)**(n-k_) for k_ in range(n//2 + 1, n + 1))
            print(f"   {p_:>6.1f}{n:>5}{maj:>15.3f}{1-(1-p_)**n:>11.3f}")
    print("   below p=0.5 majority vote makes things WORSE; above it, it sharpens fast. best-of-n")
    print("   with a verifier always helps -- one right sample is enough -- which is why verifiable")
    print("   domains (maths, code) got test-time scaling first. both trade compute for accuracy.")

    print("\n=== 5. longer chains are harder -- and worth more steps ===")
    print(f"   {'K steps':>8}{'one-shot answers':>18}{'p(all right) at 90%/step':>27}{'at 99%/step':>13}")
    for k_ in (1, 2, 4, 8, 16):
        print(f"   {k_:>8}{A**k_:>18,}{0.9**k_:>27.3f}{0.99**k_:>13.3f}")
    print("   per-step reliability compounds. a 16-step derivation at 90%/step succeeds 19% of the")
    print("   time; at 99% it is 85%. reasoning training is largely about raising the per-step number.")

    print("\n=== 6. distillation: teach a fresh policy from the trained one's traces ===")
    p_single = accuracy(cot, 400)
    student = StepByStep()
    traces = [(p, s) for p in range(N_PROBLEMS) for s in cot.sample(p, 30)[0] if verify(p, s)]
    for _ in range(30):
        for p, s in traces: student.logprob_grad(p, [s], [1.0], 0.5)      # plain SFT on correct traces
    print(f"   {len(traces)} correct traces from the RL-trained policy -> SFT a fresh policy on them")
    print(f"   student accuracy {accuracy(student):.3f}   (teacher {p_single:.3f})")
    print("   no RL, no verifier, no sampling loop at training time: just imitate correct")
    print("   reasoning. this is how most small 'reasoning' models are made.")
