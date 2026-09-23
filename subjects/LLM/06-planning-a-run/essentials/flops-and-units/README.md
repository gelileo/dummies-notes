# Essential · FLOPs and the units of compute

**Needed for:** `6ND`, "GPU-hours", "PFLOP/s-days", "MFU" in [chapter 06](../../README.md) and
the cost arithmetic in [chapter 11](../../../11-efficiency/).

## A FLOP is one arithmetic operation

```
   [n,k]@[k,m] with n=4, k=3, m=2: each of the n*m=8 outputs is a dot product
   of length k=3: 3 multiplies + 2 adds ~ 2k FLOPs. total ~ 2*n*k*m = 48.
   rule: a matrix multiply costs 2 * (rows) * (inner) * (cols) FLOPs.
```

The rule to memorise: **a matrix multiply costs `2 · rows · inner · cols` FLOPs**. Everything
else in this article is that rule applied to bigger numbers.

## One token through a weight matrix is `2P`

```
   W_Q of Llama-3-8B    P =   16,777,216   forward per token = 2P =    33,554,432 FLOPs
   W_up of Llama-3-8B   P =   58,720,256   forward per token = 2P =   117,440,512 FLOPs
   backward is ~2x forward (two matrix products), so forward+backward = 6P per token.
```

Forward `2P`, backward `4P`, so training costs **`6P` per parameter per token** — which is where
chapter 06's `6ND` comes from. Attention's `QKᵀ` is extra and grows with sequence length, so `6ND`
is a slight underestimate.

## The magnitudes

```
   FLOP                1e+00
   GFLOP (1e9)         1e+09
   TFLOP (1e12)        1e+12
   PFLOP (1e15)        1e+15
   EFLOP (1e18)        1e+18
   ZFLOP (1e21)        1e+21
   a training run is ~1e23-1e26 FLOPs: hundreds of thousands to billions of ZFLOPs' worth.
```

## Throughput: what a GPU delivers versus its label

```
   H100 bf16 dense peak 1e+15 FLOP/s x MFU 100% = 9.90e+14 FLOP/s achieved
   H100 bf16 dense peak 1e+15 FLOP/s x MFU 50% = 4.95e+14 FLOP/s achieved
   H100 bf16 dense peak 1e+15 FLOP/s x MFU 40% = 3.96e+14 FLOP/s achieved
   H100 bf16 dense peak 1e+15 FLOP/s x MFU 30% = 2.97e+14 FLOP/s achieved
   MFU (model FLOPs utilisation) = useful FLOPs / peak. 30-50% is typical; the rest is
   memory traffic, communication, and idle time (chapter 11).
```

**MFU** — model FLOPs utilisation — is the fraction of the chip's theoretical peak that goes into
useful model arithmetic. 30–50% is typical; the rest is waiting on memory, communication between
chips, and idle bubbles. [Chapter 11](../../../11-efficiency/) is about closing that gap.

## Turning a budget into hardware and time

```
   7.2e+23 FLOPs on      1 H100s at 40% MFU:      505,051 hours = 21,043.8 days
   7.2e+23 FLOPs on  1,000 H100s at 40% MFU:          505 hours =     21.0 days
   7.2e+23 FLOPs on 16,000 H100s at 40% MFU:           32 hours =      1.3 days
   the same number as GPU-hours: 505,051  |  as PFLOP/s-days: 8,333
   PFLOP/s-days (petaFLOP-per-second for a day) is the unit the GPT-3 paper used.
```

Three units for one number: total FLOPs, GPU-hours at an assumed MFU, and PFLOP/s-days (the
GPT-3 paper's unit: one petaFLOP per second, sustained for a day, is 8.64×10¹⁹ FLOPs). Convert
between them fluently; papers and vendors each pick a different one.

## What a budget buys

```
   N=1e+09 params, D=2.0e+10 tokens -> 6ND = 1.2e+20 FLOPs
   N=8e+09 params, D=1.5e+13 tokens -> 6ND = 7.2e+23 FLOPs
   N=7e+10 params, D=1.5e+13 tokens -> 6ND = 6.3e+24 FLOPs
   N=4e+11 params, D=1.5e+13 tokens -> 6ND = 3.6e+25 FLOPs
   ten times the parameters at the same data is ten times the compute. chapter 06's
   whole question is how to split a fixed budget between the two.
```

Ten times the parameters at the same data is ten times the compute — or ten times the data at
the same parameters. Chapter 06's whole question is how to split a fixed `C` between the two.

## Run it

```bash
python3 demo.py
```

## Terms

| Term | Meaning |
| --- | --- |
| **FLOP** | One floating-point operation: a multiply or an add. |
| **FLOP/s** | FLOPs per second — a rate. GPUs are labelled in TFLOP/s. |
| **`2·n·k·m`** | FLOPs for a `[n,k] @ [k,m]` matrix multiply. |
| **`6ND`** | Training FLOPs: 6 per parameter per token. Forward 2, backward 4. |
| **MFU** | Model FLOPs utilisation: achieved useful FLOP/s ÷ peak. Typically 30–50%. |
| **GPU-hour** | One GPU running for one hour. The billing unit. |
| **PFLOP/s-day** | 10¹⁵ FLOP/s for a day = 8.64×10¹⁹ FLOPs. The GPT-3 paper's unit. |
| **peak** | The chip's theoretical maximum FLOP/s. Never achieved in practice. |
