# Essentials — the maths chapter 06 assumes

Chapter 06 is arithmetic on two ideas a programmer may not have met since school, if then:

| Article | Read it when you hit… |
| --- | --- |
| [Power laws and log-log plots](./power-laws-and-log-log/) | "power law", "straight on log-log", "slope", "extrapolate the ladder" |
| [FLOPs and the units of compute](./flops-and-units/) | `6ND`, "GPU-hours", "PFLOP/s-days", "MFU", how much a run costs |

## How this folder is laid out

```text
essentials/
  README.md                       this index
  power-laws-and-log-log/
    README.md                     the article
    demo.py                       prints the numbers the article quotes
  flops-and-units/
    README.md
    demo.py
```

```bash
cd power-laws-and-log-log && python3 demo.py
```

numpy for the curve fits; deterministic.

## Owned here

Power-law maths is used by [chapter 05](../../05-data/essentials/zipf-and-the-long-tail/) (Zipf
is the linguistic instance) and [chapter 11](../../11-efficiency/). FLOPs accounting is used by
chapters 10 and 11 for inference cost.
