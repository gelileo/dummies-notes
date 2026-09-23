# Essentials — the maths chapter 10 assumes

Chapter 10 is mostly systems reasoning a programmer already has. Two pieces of arithmetic are not:

| Article | Read it when you hit… |
| --- | --- |
| [Sampling from a distribution](./sampling-from-a-distribution/) | "pick a token", temperature, top-k, top-p, "why is the output random?" |
| [Geometric series and expected tries](./geometric-series-and-expected-tries/) | speculative decoding's `(1 − qᵏ⁺¹)/(1 − q)`, "samples until one passes" |

Softmax is owned by [chapter 02](../../02-transformer-forward-pass/essentials/softmax-and-probability/);
the memory-bandwidth arithmetic is owned by [chapter 11](../../11-efficiency/).

## How this folder is laid out

```text
essentials/
  README.md                       this index
  sampling-from-a-distribution/
    README.md                     the article
    demo.py                       prints the numbers the article quotes
  geometric-series-and-expected-tries/
    README.md
    demo.py
```

```bash
cd sampling-from-a-distribution && python3 demo.py
```

numpy; deterministic.
