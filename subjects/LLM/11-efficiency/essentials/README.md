# Essentials — the ideas chapter 11 assumes

Chapter 11 is systems reasoning, and a programmer has most of it. Two pieces are specific to this
hardware and worth their own page:

| Article | Read it when you hit… |
| --- | --- |
| [The roofline](./roofline-and-arithmetic-intensity/) | "memory-bound", "arithmetic intensity", "FLOPs per byte", why batching works |
| [Quantization arithmetic](./quantization-arithmetic/) | "scale", "group size", "outliers", why int4 works and int2 doesn't |

Floating-point formats are owned by [chapter 04](../../04-optimization-loop/essentials/floating-point/);
FLOPs and compute units by [chapter 06](../../06-planning-a-run/essentials/flops-and-units/).

## How this folder is laid out

```text
essentials/
  README.md                       this index
  roofline-and-arithmetic-intensity/
    README.md                     the article
    demo.py                       prints the numbers the article quotes
  quantization-arithmetic/
    README.md
    demo.py
```

```bash
cd roofline-and-arithmetic-intensity && python3 demo.py
```

numpy; deterministic.

## Owned here

The roofline is referenced by [10](../../10-inference-and-decoding/) and [12](../../12-context-and-knowledge/).
