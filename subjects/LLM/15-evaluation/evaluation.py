#!/usr/bin/env python3
"""Evaluation, as statistics you can run: the noise in a benchmark score, when a 2-point gap
means anything, paired comparisons, the winner's curse of trying many variants, contamination,
judge bias, Elo from pairwise matches, and the unbiased pass@k estimator. numpy.
Run: python3 evaluation.py
"""
import numpy as np
from math import comb
rng = np.random.default_rng(0)

def se(p, n): return np.sqrt(p * (1 - p) / n)

if __name__ == "__main__":
    print("=== 1. a benchmark score is a noisy measurement ===")
    p = 0.70
    print(f"   a model with TRUE accuracy {p} on the task, evaluated on N questions, 5000 times:")
    print(f"   {'N':>7}{'observed range (2.5%..97.5%)':>30}{'std of observed':>17}{'formula sqrt(p(1-p)/N)':>24}")
    for N in (50, 200, 1000, 10000):
        obs = rng.binomial(N, p, 5000) / N
        lo, hi = np.percentile(obs, [2.5, 97.5])
        print(f"   {N:>7}{f'{lo:.3f} .. {hi:.3f}':>30}{obs.std():>17.4f}{se(p, N):>24.4f}")
    print("   with 200 questions the same model scores anywhere from 64% to 76%. a 95% interval is")
    print("   roughly +/- 2 standard errors: +/- 6 points at N=200, +/- 1 point at N=10,000.")

    print("\n=== 2. two models 2 points apart: how often does the WORSE one win? ===")
    print(f"   {'N':>7}{'P(worse model scores higher)':>32}   (true 0.70 vs 0.72, independent questions)")
    for N in (100, 200, 1000, 5000):
        a = rng.binomial(N, 0.70, 20000); b = rng.binomial(N, 0.72, 20000)
        print(f"   {N:>7}{np.mean(a > b):>32.3f}")
    print("   at N=200 a 2-point 'improvement' is a coin flip. most claimed improvements are inside the noise.")

    print("\n=== 3. paired comparison: same questions, tighter test ===")
    N = 200; trials = 5000
    print("   model A is 70% accurate, model B 72%, on the SAME 200 questions. what changes is how")
    print("   correlated their correctness is (both tend to fail the same hard items):")
    print(f"   {'correlation':>12}{'std of (acc_B - acc_A)':>24}{'P(B scores higher)':>20}")
    for rho in (0.0, 0.5, 0.9):
        diffs = []
        for _ in range(trials):
            u_shared = rng.random(N); u_a = rng.random(N); u_b = rng.random(N)
            share = rng.random(N) < rho                       # for these items, both models see the same 'difficulty draw'
            ua = np.where(share, u_shared, u_a); ub = np.where(share, u_shared, u_b)
            a = ua < 0.70; b = ub < 0.72                      # marginals fixed at exactly 0.70 / 0.72
            diffs.append(b.mean() - a.mean())
        diffs = np.array(diffs)
        print(f"   {rho:>12.1f}{diffs.std():>24.4f}{np.mean(diffs > 0):>20.3f}")
    print("   same two models, same gap. when their errors are correlated -- as real models' are, since")
    print("   hard questions are hard for everyone -- the DIFFERENCE is far less noisy than either")
    print("   score, and the better model wins far more reliably. always compare on the same items,")
    print("   and report the paired difference, not two separate scores.")

    print("\n=== 4. the winner's curse: try ten variants, report the best ===")
    N = 200; K = 10
    best = [rng.binomial(N, 0.70, K).max() / N for _ in range(5000)]
    print(f"   ten IDENTICAL variants (true accuracy 0.70 each) on N={N}. report the best-scoring one:")
    print(f"   mean of the reported 'best' = {np.mean(best):.3f}   ({(np.mean(best)-0.70)*100:.1f} points of pure selection bias)")
    print(f"   P(best-of-10 beats a single honest run of a truly-2-points-better model) = {np.mean(np.array(best) > rng.binomial(N, 0.72, 5000)/N):.3f}")
    print("   trying many prompts, seeds or checkpoints and keeping the top score manufactures")
    print("   improvement from noise. hold out a test set you touch once.")

    print("\n=== 5. contamination: the arithmetic of a leaked test set ===")
    true_acc = 0.60
    for frac in (0.0, 0.1, 0.3, 0.5):
        print(f"   {frac:.0%} of test items seen in training (answered correctly): measured accuracy {frac*1.0 + (1-frac)*true_acc:.3f}   (true {true_acc})")
    print("   memorised items score 100%. thirty percent leakage turns a 60% model into a 72% one.")

    print("\n=== 6. LLM-as-judge: position bias, detected by swapping ===")
    print("   a judge that prefers whatever is shown FIRST 60% of the time, regardless of content.")
    print("   two equally good answers, 1000 comparisons:")
    first_wins = rng.random(1000) < 0.6
    print(f"   A shown first every time:  A 'wins' {first_wins.mean():.1%}")
    swapped = np.concatenate([rng.random(500) < 0.6, rng.random(500) < 0.4])   # second half: B first, so A wins 40%
    print(f"   positions alternated:      A 'wins' {swapped.mean():.1%}")
    print("   randomise or swap positions and average. the same goes for length bias and self-preference.")

    print("\n=== 7. leaderboards: Bradley-Terry ratings from pairwise matches (chapter 08's model) ===")
    true_strength = np.array([0.0, 0.5, 1.0, 1.5])
    def fit(n_matches):
        pairs = []
        for _ in range(n_matches):
            i, j = rng.choice(4, 2, replace=False)
            win = rng.random() < 1/(1+np.exp(-(true_strength[i]-true_strength[j])))
            pairs.append((i, j) if win else (j, i))
        s = np.zeros(4)
        for _ in range(500):                                  # maximum-likelihood fit by gradient ascent
            g = np.zeros(4)
            for w, l in pairs:
                p_w = 1/(1+np.exp(-(s[w]-s[l]))); g[w] += 1-p_w; g[l] -= 1-p_w
            s += 2.0 * g / len(pairs)
        return s - s.mean()
    ctr = true_strength - true_strength.mean()
    print(f"   {'matches':>8}{'fitted (centred) strengths':>36}{'max error':>11}   true: {ctr}")
    for n in (100, 1000, 10000):
        f = fit(n); print(f"   {n:>8}{str(np.round(f, 2)):>36}{np.abs(f-ctr).max():>11.2f}")
    print("   ratings converge as matches accumulate. with few matches the ORDER is usually right and the")
    print("   GAPS are noise. Elo is the online approximation of this fit; Chatbot Arena reports these")
    print("   ratings with confidence intervals -- read the intervals, not the rank.")

    print("\n=== 8. pass@k: the unbiased estimator ===")
    n, c = 20, 6                    # generate 20 samples per problem, 6 correct
    print(f"   {n} samples per problem, {c} correct. estimate pass@k = P(at least one of k random samples is correct):")
    print(f"   {'k':>4}{'naive 1-(1-c/n)^k':>20}{'unbiased 1 - C(n-c,k)/C(n,k)':>30}")
    for k in (1, 5, 10, 20):
        naive = 1 - (1 - c/n)**k; unb = 1 - comb(n-c, k)/comb(n, k) if k <= n else 1.0
        print(f"   {k:>4}{naive:>20.3f}{unb:>30.3f}")
    print("   the naive formula assumes the k draws are independent with replacement; they are drawn")
    print("   WITHOUT replacement from the n you generated. at k=n it must be exactly 1.0 if any sample")
    print("   was correct -- the naive estimate is not. (Chen et al. 2021; chapter 09's compounding.)")
