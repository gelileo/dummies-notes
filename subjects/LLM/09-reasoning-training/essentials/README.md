# Essentials — the maths chapter 09 assumes

Two small pieces of arithmetic carry chapter 09's claims about compute and reliability:

| Article | Read it when you hit… |
| --- | --- |
| [Compounding probabilities](./compounding-probabilities/) | `pᵏ`, "20 steps at 90%", "best-of-n", "majority vote", the binomial |
| [Z-scores and group normalisation](./z-scores-and-group-normalisation/) | GRPO's `(r − mean)/std`, "no critic", "frontier prompts" |

The policy gradient itself is owned by
[chapter 08](../../08-preference-optimization/essentials/the-policy-gradient/).

## How this folder is laid out

```text
essentials/
  README.md                       this index
  compounding-probabilities/
    README.md                     the article
    demo.py                       prints the numbers the article quotes
  z-scores-and-group-normalisation/
    README.md
    demo.py
```

```bash
cd compounding-probabilities && python3 demo.py
```

Standard library and numpy; deterministic.

## Owned here

Compounding probabilities are referenced by [10](../../10-inference-and-decoding/) (speculative
decoding, test-time compute) and [15](../../15-evaluation/) (pass@k).
