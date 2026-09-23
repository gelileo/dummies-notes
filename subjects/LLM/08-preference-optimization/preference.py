#!/usr/bin/env python3
"""Preference optimization, measured on a toy small enough to see through.

The 'policy' is a distribution over 8 candidate responses to one prompt. Each response
has a hidden TRUE quality (what a careful human would rate) and a length. Humans compare
pairs and prefer the higher-quality one -- but in this dataset longer responses happen to
be better, so a reward model trained on the comparisons learns to like length. The policy
then optimises that flawed reward, and we can measure exactly how much it helps and how
much it hacks. numpy.  Run: python3 preference.py
"""
import numpy as np
rng = np.random.default_rng(0)

R = 8
LENGTH  = np.array([ 3,  5,  8, 10, 12, 15, 20, 40], float)      # tokens
QUALITY = np.array([1.0, 2.0, 3.0, 4.5, 5.0, 5.5, 4.0, 2.0])     # hidden truth: best is #5; #7 is long and bad
NAMES   = [f"r{i}(len {int(l)})" for i, l in enumerate(LENGTH)]

def softmax(z): e = np.exp(z - z.max()); return e / e.sum()
def kl(p, q): return float(np.sum(p * np.log((p + 1e-12) / (q + 1e-12))))
def expected(p, v): return float(p @ v)

# ------------------------------------------------------------------ 1. preference data
def human_prefers(i, j, noise=1.0):
    """Bradley-Terry human: P(i beats j) = sigmoid(quality_i - quality_j)."""
    return rng.random() < 1 / (1 + np.exp(-(QUALITY[i] - QUALITY[j]) / noise))

def collect_pairs(n, exclude_long=True):
    pairs = []
    cands = [i for i in range(R) if not (exclude_long and i == 7)]   # the 40-token junk is rarely shown to raters
    for _ in range(n):
        i, j = rng.choice(cands, 2, replace=False)
        pairs.append((i, j) if human_prefers(i, j) else (j, i))     # (chosen, rejected)
    return pairs

# ------------------------------------------------------------------ 2. reward model
def train_reward_model(pairs, features, steps=2000, lr=0.05):
    """Learn r(x) = w . features(x) so that sigmoid(r_chosen - r_rejected) ~ 1. Bradley-Terry."""
    w = np.zeros(features.shape[1])
    for _ in range(steps):
        g = np.zeros_like(w)
        for c, r_ in pairs:
            d = features[c] - features[r_]
            p_correct = 1 / (1 + np.exp(-(w @ d)))
            g += (p_correct - 1) * d          # gradient of -log sigmoid(w.d)
        w -= lr * g / len(pairs)
    return w

# ------------------------------------------------------------------ 3. policy gradient
def reinforce(reward, steps, lr, ref_logits, beta=0.0, baseline=True, clip=None, samples=16):
    """Maximise E_pi[reward] - beta * KL(pi || ref) by sampling responses and pushing up the
    log-prob of ones that scored above the baseline. Returns the final policy and a history."""
    logits = ref_logits.copy(); hist = []
    for t in range(steps):
        p = softmax(logits)
        idx = rng.choice(R, samples, p=p)
        rw = reward[idx] - beta * (np.log(p[idx] + 1e-12) - np.log(softmax(ref_logits)[idx] + 1e-12))
        adv = rw - (rw.mean() if baseline else 0.0)
        g = np.zeros(R)
        for k, a in zip(idx, adv):
            onehot = np.zeros(R); onehot[k] = 1
            g += a * (onehot - p)                  # grad of log pi(k) wrt logits
        g /= samples
        if clip is not None:                       # PPO-style: cap how far the policy moves per step
            new = softmax(logits + lr * g); ratio = new / p
            if np.abs(ratio - 1).max() > clip:
                g *= clip / np.abs(ratio - 1).max()
        logits += lr * g
        if t % max(1, steps // 5) == 0 or t == steps - 1:
            hist.append((t, expected(softmax(logits), QUALITY), expected(softmax(logits), reward)))
    return logits, hist

# ------------------------------------------------------------------ 4. DPO
def dpo(pairs, ref_logits, steps=400, lr=0.1, beta=0.5):
    """Directly push log pi(chosen)/pi_ref(chosen) above log pi(rejected)/pi_ref(rejected)."""
    logits = ref_logits.copy(); ref = np.log(softmax(ref_logits))
    for _ in range(steps):
        lp = np.log(softmax(logits)); g = np.zeros(R)
        for c, r_ in pairs:
            margin = beta * ((lp[c] - ref[c]) - (lp[r_] - ref[r_]))
            s = 1 / (1 + np.exp(margin))          # sigmoid(-margin): how wrong we still are
            for k, sign in ((c, +1), (r_, -1)):
                onehot = np.zeros(R); onehot[k] = 1
                g += s * beta * sign * (onehot - softmax(logits))
        logits += lr * g / len(pairs)
    return logits

if __name__ == "__main__":
    np.set_printoptions(precision=3, suppress=True)
    ref_logits = np.zeros(R); ref = softmax(ref_logits)          # the SFT model: uniform over responses
    print("=== 0. the setup ===")
    print(f"   {'response':<14}{'length':>8}{'true quality':>14}   (quality is hidden from everything below)")
    for i in range(R): print(f"   {NAMES[i]:<14}{LENGTH[i]:>8.0f}{QUALITY[i]:>14.1f}")
    print(f"   reference policy: uniform.  expected true quality {expected(ref, QUALITY):.2f}")

    print("\n=== 1. humans compare pairs; a reward model learns from the comparisons ===")
    pairs = collect_pairs(300)
    feats = np.stack([LENGTH / 10, np.ones(R)], 1)              # the RM can only see LENGTH (+ bias)
    w = train_reward_model(pairs, feats)
    reward = feats @ w
    print(f"   {len(pairs)} comparisons.  reward model features: [length/10, 1].  learned w = {w}")
    print(f"   {'response':<14}{'true quality':>13}{'RM reward':>11}")
    for i in range(R): print(f"   {NAMES[i]:<14}{QUALITY[i]:>13.1f}{reward[i]:>11.2f}")
    print("   in the data longer WAS better (up to r5), so the RM learned 'longer = better'.")
    print("   it has never seen r7 (40 tokens, junk) and extrapolates: highest reward of all.")
    agree = np.mean([reward[c] > reward[r_] for c, r_ in pairs])
    print(f"   RM agrees with the human on {agree:.0%} of training pairs -- it looks good.")

    print("\n=== 2. policy gradient: push up responses the RM likes ===")
    print(f"   {'beta (KL)':>10}{'true quality':>14}{'RM reward':>11}{'KL to ref':>11}{'mass on r7':>12}   top response")
    for beta in (0.0, 0.3, 1.0, 3.0, 10.0):
        pol, hist = reinforce(reward, 300, 0.3, ref_logits, beta=beta)
        p = softmax(pol)
        print(f"   {beta:>10}{expected(p, QUALITY):>14.2f}{expected(p, reward):>11.2f}{kl(p, ref):>11.2f}{p[7]:>12.2f}   {NAMES[p.argmax()]}")
    print(f"   (uniform reference: true quality {expected(ref, QUALITY):.2f})")
    print("   beta=0: the policy collapses onto r7 -- max RM reward, true quality WORSE than the")
    print("   untrained reference. that is reward hacking: the policy found the RM's blind spot.")
    print("   the KL penalty is the leash, and note how strong it has to be: the RM's reward gap")
    print("   is so large that beta 0.3-1.0 barely restrains it. beta=10 holds the policy near")
    print("   the reference -- and also stops it improving. the leash costs what it protects.")

    print("\n=== 3. why a baseline: the variance of one gradient estimate ===")
    print("   at the reference policy, draw 16 samples, form the policy-gradient estimate, repeat 2000x:")
    p0 = softmax(ref_logits)
    for bl in (False, True):
        ests = []
        for _ in range(2000):
            idx = rng.choice(R, 16, p=p0); rw = reward[idx]
            adv = rw - (rw.mean() if bl else 0.0); g = np.zeros(R)
            for k, a in zip(idx, adv):
                onehot = np.zeros(R); onehot[k] = 1; g += a * (onehot - p0)
            ests.append(g / 16)
        ests = np.array(ests); mean = ests.mean(0); spread = np.sqrt(((ests - mean)**2).sum(1)).mean()
        print(f"   baseline={str(bl):<5} mean gradient |{np.linalg.norm(mean):.3f}|   typical distance of one estimate from the mean {spread:.3f}")
    print("   same mean direction, less scatter. subtracting the batch-mean reward changes nothing")
    print("   in expectation (the subtracted term has zero expected gradient) and cuts variance.")

    print("\n=== 4. a better reward model: give it the right features ===")
    feats2 = np.stack([LENGTH / 10, (LENGTH / 10)**2, np.ones(R)], 1)   # can now represent 'too long is bad'
    pairs2 = collect_pairs(300, exclude_long=False)                     # and raters DID see r7
    w2 = train_reward_model(pairs2, feats2); reward2 = feats2 @ w2
    pol, _ = reinforce(reward2, 300, 0.3, ref_logits, beta=0.3); p = softmax(pol)
    print(f"   RM reward for r7(junk): before {reward[7]:.2f}  now {reward2[7]:.2f}")
    print(f"   policy: true quality {expected(p, QUALITY):.2f}  top {NAMES[p.argmax()]}  mass on r7 {p[7]:.2f}   (true best is r5 at 5.5)")
    print("   coverage (raters saw r7) and capacity (a term that can say 'too long') fixed the")
    print("   hack. the reward model matters more than the RL algorithm. still imperfect: two")
    print("   features of length cannot place r5 above r6.")

    print("\n=== 5. PPO-style clipping: does capping the per-step move matter here? ===")
    print("   same good reward model. per-step policy change, with and without a cap, at two step sizes:")
    results = {}
    for lr_ in (3.0, 30.0):
        for clip in (None, 0.2):
            pol = ref_logits.copy(); moves = []; qs = []
            for _ in range(60):
                before = softmax(pol)
                pol, _ = reinforce(reward2, 1, lr_, pol, beta=0.3, clip=clip)
                after = softmax(pol); moves.append(np.abs(after - before).sum()); qs.append(expected(after, QUALITY))
            results[(lr_, clip)] = (np.max(moves), np.mean(moves), qs[-1], np.std(qs[-20:]))
            print(f"   lr={lr_:<5} clip={str(clip):<5} largest single-step move {np.max(moves):.3f}   "
                  f"mean move {np.mean(moves):.3f}   final quality {qs[-1]:.2f}   quality jitter (last 20 steps) {np.std(qs[-20:]):.3f}")
    if results[(30.0, None)][0] > 2 * results[(30.0, 0.2)][0]:
        print("   at the sane step size clipping changes nothing -- both runs move gently. at 10x")
        print("   the step, the unclipped policy lurches by whole probability masses in a single")
        print("   update; the clipped one is held to a bounded move. both still land in the same")
        print("   place HERE -- eight responses and a smooth reward are hard to break. on a real")
        print("   model that unbounded lurch is where training collapses. PPO's clipped objective")
        print("   exists to make a too-large update a bounded one instead of an overshoot.")
    else:
        print("   in this toy the cap barely binds even at 10x the step: eight discrete responses")
        print("   and a smooth reward make the policy hard to destabilise. PPO's clipping earns its")
        print("   keep on real models, where one update can move token probabilities catastrophically.")

    print("\n=== 6. DPO: skip the reward model, optimise the pairs directly ===")
    pol = dpo(pairs2, ref_logits); p = softmax(pol)
    print(f"   from the same {len(pairs2)} pairs, no reward model, no sampling loop:")
    print(f"   true quality {expected(p, QUALITY):.2f}  KL to ref {kl(p, ref):.2f}  top {NAMES[p.argmax()]}  mass on r7 {p[7]:.2f}")
    print(f"   {'response':<14}{'ref':>7}{'RLHF':>7}{'DPO':>7}")
    pr = softmax(reinforce(reward2, 300, 0.3, ref_logits, beta=0.3)[0])
    for i in range(R): print(f"   {NAMES[i]:<14}{ref[i]:>7.3f}{pr[i]:>7.3f}{p[i]:>7.3f}")
    print("   DPO gets to a similar place with a closed-form loss on the pairs. simpler and")
    print("   stabler; but it can only learn from pairs it was given (offline), while RLHF")
    print("   keeps sampling new responses and can improve beyond the dataset -- or hack it.")
