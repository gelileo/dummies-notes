#!/usr/bin/env python3
"""Generates evaluation.md from evaluation.py's output. Run: python3 measure.py"""
import io, subprocess
o = io.StringIO(); W = o.write
out = subprocess.run(['python3', 'evaluation.py'], capture_output=True, text=True).stdout
def sect(start):
    i = out.index(start); return out[i:].split(chr(10), 1)[1].split('===')[0].rstrip()

W(f"""# Evaluation, traced

Every number here is produced by `evaluation.py`. Run `python3 measure.py` to regenerate.

Every decision in chapters 05–14 — data mixture, architecture, RL recipe, quantization level —
was made by measuring something. Loss is exact but only measures prediction on the training
distribution; what you care about needs benchmarks, and benchmarks lie in specific,
well-understood ways. This chapter simulates each of those ways so you can see the size of the
effect.

---

## 1. A benchmark score is a noisy measurement

```
{sect('=== 1. a benchmark')}
```

The same model, the same true accuracy, evaluated on 200 questions — and it scores anywhere from
64% to 76%. The spread follows `√(p(1−p)/N)` exactly. **A benchmark number without its sample size
is not a number.** → [essentials: standard error](essentials/standard-error-and-confidence-intervals/)

---

## 2. When does a 2-point gap mean anything?

```
{sect('=== 2. two models')}
```

On 200 independent questions, the worse of two models 2 points apart beats the better one nearly
a third of the time. Most claimed improvements in the field are inside this noise.

---

## 3. Paired comparison

```
{sect('=== 3. paired comparison')}
```

Same two models, same gap. What changes is whether they are scored on the *same* questions — and
real models' errors are correlated, because hard questions are hard for everyone. When they are,
the **difference** between two scores is far less noisy than either score alone, and the better
model wins reliably where before it was a coin flip. Always compare on the same items; report the
paired difference.

---

## 4. The winner's curse

```
{sect("=== 4. the winner's curse")}
```

Ten identical variants; report the best; five points of improvement appear from nothing — enough
to beat an honest run of a model that really is 2 points better, three times in four. Trying
many prompts, seeds or checkpoints and keeping the top score *manufactures* improvement. Hold out
a test set you touch once. → [essentials: multiple comparisons](essentials/multiple-comparisons-and-the-winners-curse/)

---

## 5. Contamination

```
{sect('=== 5. contamination')}
```

A test item that was in the training data is answered from memory, correctly. Thirty percent
leakage turns a 60% model into a 72% one. [Chapter 05](../05-data/) decontaminates by n-gram
overlap and it is porous — paraphrases pass — which is why fresh, private test sets exist and why
they, too, age.

---

## 6. LLM-as-judge and its biases

```
{sect('=== 6. LLM-as-judge')}
```

A model grading outputs is cheap and scalable, and it has biases you can measure: **position**
(shown here — 60% for whatever comes first, detected by swapping), **length** (longer looks
better), and **self-preference** (a judge favours outputs in its own style). Randomise positions,
control for length, and calibrate the judge against human labels before trusting it.

---

## 7. Leaderboards

```
{sect('=== 7. leaderboards')}
```

Human preference leaderboards (Chatbot Arena) collect pairwise votes and fit
[Bradley–Terry](../08-preference-optimization/essentials/sigmoid-and-pairwise-preference/) — the
same model that trains a reward model. Ratings converge as matches accumulate; with few, the
order is right and the gaps are noise. Read the confidence intervals, not the rank. Elo is the
online approximation of this fit.

---

## 8. pass@k, estimated correctly

```
{sect('=== 8. pass@k')}
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
""")
open('evaluation.md', 'w').write(o.getvalue())
print("wrote evaluation.md", len(o.getvalue()), "chars")
