# Essentials — the statistics chapter 15 assumes

Chapter 15 is measurement, and two pieces of statistics carry it:

| Article | Read it when you hit… |
| --- | --- |
| [Standard error and confidence intervals](./standard-error-and-confidence-intervals/) | "± 2 SE", "noise", "how many questions", "is a 2-point gap real?" |
| [Multiple comparisons and the winner's curse](./multiple-comparisons-and-the-winners-curse/) | "tried ten prompts", "selection bias", "hold out a test set" |

Bradley–Terry (leaderboards) is owned by
[chapter 08](../../08-preference-optimization/essentials/sigmoid-and-pairwise-preference/);
the binomial and pass@k by [chapter 09](../../09-reasoning-training/essentials/compounding-probabilities/).

## How this folder is laid out

```text
essentials/
  README.md                       this index
  standard-error-and-confidence-intervals/
    README.md                     the article
    demo.py                       prints the numbers the article quotes
  multiple-comparisons-and-the-winners-curse/
    README.md
    demo.py
```

```bash
cd standard-error-and-confidence-intervals && python3 demo.py
```

numpy; deterministic.

## Owned here, used before

Chapter 06 (small-run ablations) and chapter 07 (held-out sets) lean on these; they link here.
