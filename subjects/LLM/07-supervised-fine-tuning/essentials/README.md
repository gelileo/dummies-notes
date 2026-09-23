# Essentials — the ideas chapter 07 assumes

Two ideas in chapter 07 are not standard equipment for a programmer:

| Article | Read it when you hit… |
| --- | --- |
| [Low-rank matrices](./low-rank-matrices/) | "LoRA", "rank", `A @ B`, why fine-tuning fits on one GPU |
| [Overfitting and generalization](./overfitting-and-generalization/) | "held-out loss", "few epochs", "early stopping", "catastrophic forgetting" |

## How this folder is laid out

```text
essentials/
  README.md                       this index
  low-rank-matrices/
    README.md                     the article
    demo.py                       prints the numbers the article quotes
  overfitting-and-generalization/
    README.md
    demo.py
```

```bash
cd low-rank-matrices && python3 demo.py
```

numpy; deterministic.

## Owned here

Overfitting/generalization is referenced by [04](../../04-optimization-loop/) (mentioned) and
[15](../../15-evaluation/) (held-out sets). Low-rank matrices reappear in
[11](../../11-efficiency/) (compression). Matrices themselves are owned by
[chapter 02's essentials](../../02-transformer-forward-pass/essentials/matrices-as-functions/).
