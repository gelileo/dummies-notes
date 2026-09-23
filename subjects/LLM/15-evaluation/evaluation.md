# Evaluation, traced

Every number here is produced by `evaluation.py`. Run `python3 measure.py` to regenerate.

Every decision in chapters 05–14 — data mixture, architecture, RL recipe, quantization level —
was made by measuring something. Loss is exact but only measures prediction on the training
distribution; what you care about needs benchmarks, and benchmarks lie in specific,
well-understood ways. This chapter simulates each of those ways so you can see the size of the
effect.

---

## 1. A benchmark score is a noisy measurement

```
   a model with TRUE accuracy 0.7 on the task, evaluated on N questions, 5000 times:
         N  observed range (2.5%..97.5%)  std of observed  formula sqrt(p(1-p)/N)
        50                0.580 .. 0.820           0.0651                  0.0648
       200                0.635 .. 0.760           0.0326                  0.0324
      1000                0.672 .. 0.728           0.0143                  0.0145
     10000                0.691 .. 0.709           0.0046                  0.0046
   with 200 questions the same model scores anywhere from 64% to 76%. a 95% interval is
   roughly +/- 2 standard errors: +/- 6 points at N=200, +/- 1 point at N=10,000.
```

The same model, the same true accuracy, evaluated on 200 questions — and it scores anywhere from
64% to 76%. The spread follows `√(p(1−p)/N)` exactly. **A benchmark number without its sample size
is not a number.** → [essentials: standard error](essentials/standard-error-and-confidence-intervals/)

---

## 2. When does a 2-point gap mean anything?

```
         N    P(worse model scores higher)   (true 0.70 vs 0.72, independent questions)
       100                           0.348
       200                           0.307
      1000                           0.152
      5000                           0.014
   at N=200 a 2-point 'improvement' is a coin flip. most claimed improvements are inside the noise.
```

On 200 independent questions, the worse of two models 2 points apart beats the better one nearly
a third of the time. Most claimed improvements in the field are inside this noise.

---

## 3. Paired comparison

```
   model A is 70% accurate, model B 72%, on the SAME 200 questions. what changes is how
   correlated their correctness is (both tend to fail the same hard items):
    correlation  std of (acc_B - acc_A)  P(B scores higher)
            0.0                  0.0453               0.645
            0.5                  0.0330               0.702
            0.9                  0.0170               0.852
   same two models, same gap. when their errors are correlated -- as real models' are, since
   hard questions are hard for everyone -- the DIFFERENCE is far less noisy than either
   score, and the better model wins far more reliably. always compare on the same items,
   and report the paired difference, not two separate scores.
```

Same two models, same gap. What changes is whether they are scored on the *same* questions — and
real models' errors are correlated, because hard questions are hard for everyone. When they are,
the **difference** between two scores is far less noisy than either score alone, and the better
model wins reliably where before it was a coin flip. Always compare on the same items; report the
paired difference.

---

## 4. The winner's curse

```
   ten IDENTICAL variants (true accuracy 0.70 each) on N=200. report the best-scoring one:
   mean of the reported 'best' = 0.749   (4.9 points of pure selection bias)
   P(best-of-10 beats a single honest run of a truly-2-points-better model) = 0.770
   trying many prompts, seeds or checkpoints and keeping the top score manufactures
   improvement from noise. hold out a test set you touch once.
```

Ten identical variants; report the best; five points of improvement appear from nothing — enough
to beat an honest run of a model that really is 2 points better, three times in four. Trying
many prompts, seeds or checkpoints and keeping the top score *manufactures* improvement. Hold out
a test set you touch once. → [essentials: multiple comparisons](essentials/multiple-comparisons-and-the-winners-curse/)

---

## 5. Contamination

```
   0% of test items seen in training (answered correctly): measured accuracy 0.600   (true 0.6)
   10% of test items seen in training (answered correctly): measured accuracy 0.640   (true 0.6)
   30% of test items seen in training (answered correctly): measured accuracy 0.720   (true 0.6)
   50% of test items seen in training (answered correctly): measured accuracy 0.800   (true 0.6)
   memorised items score 100%. thirty percent leakage turns a 60% model into a 72% one.
```

A test item that was in the training data is answered from memory, correctly. Thirty percent
leakage turns a 60% model into a 72% one. [Chapter 05](../05-data/) decontaminates by n-gram
overlap and it is porous — paraphrases pass — which is why fresh, private test sets exist and why
they, too, age.

---

## 6. LLM-as-judge and its biases

```
   a judge that prefers whatever is shown FIRST 60% of the time, regardless of content.
   two equally good answers, 1000 comparisons:
   A shown first every time:  A 'wins' 60.5%
   positions alternated:      A 'wins' 48.8%
   randomise or swap positions and average. the same goes for length bias and self-preference.
```

A model grading outputs is cheap and scalable, and it has biases you can measure: **position**
(shown here — 60% for whatever comes first, detected by swapping), **length** (longer looks
better), and **self-preference** (a judge favours outputs in its own style). Randomise positions,
control for length, and calibrate the judge against human labels before trusting it.

---

## 7. Leaderboards

```
    matches          fitted (centred) strengths  max error   true: [-0.75 -0.25  0.25  0.75]
        100           [-0.74 -0.48  0.45  0.76]       0.23
       1000           [-0.8  -0.21  0.21  0.8 ]       0.05
      10000           [-0.75 -0.28  0.28  0.75]       0.03
   ratings converge as matches accumulate. with few matches the ORDER is usually right and the
   GAPS are noise. Elo is the online approximation of this fit; Chatbot Arena reports these
   ratings with confidence intervals -- read the intervals, not the rank.
```

Human preference leaderboards (Chatbot Arena) collect pairwise votes and fit
[Bradley–Terry](../08-preference-optimization/essentials/sigmoid-and-pairwise-preference/) — the
same model that trains a reward model. Ratings converge as matches accumulate; with few, the
order is right and the gaps are noise. Read the confidence intervals, not the rank. Elo is the
online approximation of this fit.

---

## 8. pass@k, estimated correctly

```
   20 samples per problem, 6 correct. estimate pass@k = P(at least one of k random samples is correct):
      k   naive 1-(1-c/n)^k  unbiased 1 - C(n-c,k)/C(n,k)
      1               0.300                         0.300
      5               0.832                         0.871
     10               0.972                         0.995
     20               0.999                         1.000
   the naive formula assumes the k draws are independent with replacement; they are drawn
   WITHOUT replacement from the n you generated. at k=n it must be exactly 1.0 if any sample
   was correct -- the naive estimate is not. (Chen et al. 2021; chapter 09's compounding.)
```

For code and maths you generate `n` samples per problem and ask how often at least one of `k`
would be right. The naive `1 − (1 − c/n)ᵏ` assumes draws *with* replacement; the samples are drawn
*without* replacement from the `n` you have, and the unbiased estimator is `1 − C(n−c, k)/C(n, k)`.
At `k = n` it is exactly 1 whenever any sample was correct; the naive one is not.
→ [chapter 09's compounding](../09-reasoning-training/essentials/compounding-probabilities/)

---

## 9. What this means for evaluating your own fine-tune

Hold out a set from the same distribution *before* training. Write a small suite of the specific
cases you care about. Evaluate before and after, on both, paired. Report the difference with its
standard error. Watch for regressions on what you did not train on — [chapter 07](../07-supervised-fine-tuning/)'s
forgetting shows up here. And touch the test set once.

---

## 10. Invariants

1. **A score without `N` is not a number.** `SE = √(p(1−p)/N)`; ± 2 SE.
2. **Two-point gaps on hundreds of questions are noise.** Paired on the same items, they may not be.
3. **The best of many is inflated.** Select on validation; report on a test set you touch once.
4. **Contamination inflates linearly with leakage.** Decontamination is porous.
5. **Judges have biases you can measure.** Swap positions; control length; calibrate.
6. **Leaderboards are Bradley–Terry fits.** Read the intervals.
7. **pass@k without replacement.** Use the unbiased estimator.
