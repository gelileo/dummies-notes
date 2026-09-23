# Efficiency, traced

Every number here is produced by `efficiency.py`. Run `python3 systems.py` to regenerate.

The maths of the Transformer has not changed since 2017; the cost of running it has fallen by
orders of magnitude. All of that came from fitting the same computation to the hardware better.
This is the systems chapter, and it rests on one fact measured first.

---

## 1. The roofline: memory or arithmetic?

An H100 does about 990 TFLOP/s of bf16 arithmetic and moves about 3.35 TB/s from memory. The ratio
— **296 FLOPs per byte** — is the ridge. An operation that does fewer FLOPs than that per byte it
moves is waiting on memory; more, and it is waiting on arithmetic.

For a matrix multiply `[B, d] @ [d, n]` with Llama-3-8B's MLP shape:

```
   batch B       FLOPs  bytes (bf16)  FLOPs/byte   regime
         1    1.17e+08      1.17e+08           1   memory-bound
         8    9.40e+08      1.18e+08           8   memory-bound
        64    7.52e+09      1.20e+08          63   memory-bound
       256    3.01e+10      1.27e+08         237   memory-bound
      1024    1.20e+11      1.55e+08         775   compute-bound
```

Decoding one token for one user is `B = 1`: about **one FLOP per byte**. The weight matrix is
read from memory and used once. Nearly everything in this chapter is a way of not doing that.
→ [essentials: roofline](essentials/roofline-and-arithmetic-intensity/)

---

## 2. Tokens per second

```
  Llama-3-8B bf16 weights: 16.1 GB.  one full read: 4.8 ms  ->  at most 209 tok/s for ONE sequence

   batch  tokens/s total  per-user tok/s  compute per step
       1             209             209           0.02 ms
       8            1669             209           0.13 ms
      32            6675             209           0.52 ms
     128           26700             209           2.08 ms
```

Throughput scales almost linearly with batch until the arithmetic catches up with the memory
read — the same weight stream serves every sequence in the batch. That is the entire reason
**continuous batching** exists, and why serving cost per token falls so steeply with load.

---

## 3. Quantization

Fewer bits per weight means fewer bytes to stream — which, given section 1, is the same as
faster decoding. The question is what it costs in accuracy:

```
  format             bits GB for 8B  rel. output error
  bf16 (reference)     16      16.1             0.0000
  int8, per-row         8       8.0             0.0080
  int4, per-row         4       4.0             0.1453
  int4, group 128       4       4.0             0.1213
  int4, group 32        4       4.0             0.0988
  int2, group 32        2       2.0             0.6614
```

`int8` is nearly free. Naive `int4` with one scale per row is lossy, because a single outlier
weight stretches the scale and wastes levels on everyone else. Give each block of 32 weights its
own scale and the error falls by about a third; error-compensating rounding (GPTQ) and
pre-scaling the outlier channels (AWQ) do the rest. `int2` is destruction either way.

Per-layer output error overstates the damage — the network absorbs some of it — so the real
test is perplexity ([chapter 03](../03-training-objective/)) before and after.
→ [essentials: quantization arithmetic](essentials/quantization-arithmetic/)

---

## 4. Attention memory: FlashAttention

Attention's score matrix is `T × T` per head. Materialise it and memory is quadratic in context:

```
         T   score matrix, one head   × 32 heads  tiled, block 128 (approx.)
     1,024                     2 MB        67 MB                        1 MB
     4,096                    34 MB       1.1 GB                        2 MB
    32,768                   2.1 GB      68.7 GB                       17 MB
   131,072                  34.4 GB    1099.5 GB                       67 MB
```

At 128k context the full matrix is 34 GB *per head*. FlashAttention never builds it: it streams
keys and values through on-chip memory in blocks, keeps a running softmax, and recomputes what it
needs in the backward pass. Same mathematics, exact result, memory linear in `T`. That is the
canonical hardware-aware algorithm, and it is why long context exists at all.

---

## 5. Parallelism: what crosses the wire

One model, thousands of GPUs. Three ways to split it, each with a different communication bill:

```
  data parallel      all-reduce the GRADIENTS       2 × 16 GB (bf16) per step, per device
  tensor parallel    all-reduce ACTIVATIONS, twice per layer:  2 × 32 × 0.27 GB = 17.2 GB per micro-batch
  pipeline parallel  send one layer boundary's activations:   0.27 GB per micro-batch, point to point
```

**Data parallel** copies the model and splits the batch; every step it must average gradients
the size of the model (ZeRO/FSDP shard the copies to save memory). **Tensor parallel** splits
individual matrices and must exchange activations constantly — it needs NVLink-class bandwidth
and so stays inside one node. **Pipeline parallel** puts different layers on different devices
and sends little, but idles while the pipeline fills. Frontier runs combine all three.

---

## 6. Mixture of experts

```
  illustrative shapes; per layer: shared attention params + experts × params each; 32 layers

  dense 7B                           total    7.0B   active per token   7.0B   FLOPs/token ≈ 1.4e+10
  8 experts, top-2 (Mixtral-like)    total   46.4B   active per token  12.6B   FLOPs/token ≈ 2.5e+10
  64 small experts, top-8            total   46.4B   active per token   7.0B   FLOPs/token ≈ 1.4e+10
```

Replace each MLP with several **experts** and a router that sends each token to a few of them.
Total parameters — knowledge — go up several-fold; compute per token stays at the active
fraction. The price is memory (every expert must be resident) and a balancing loss so that no
expert starves. Mixtral 8×7B reports about 47B total and 13B active *(reported)*; the middle row
lands on that shape.

---

## 7. Cost per million tokens

```
  batch   8:      834 tok/s  ->  $ 1.00 per million output tokens   (at $3.0/GPU-hour, 50% efficiency)
  batch  64:    6,675 tok/s  ->  $ 0.12 per million output tokens   (at $3.0/GPU-hour, 50% efficiency)
```

The arithmetic is the product; the dollar figure and the utilisation are assumptions, and they
are the two numbers that change. Batch harder, quantize, share the KV cache, use MoE — every
technique in this chapter is a term in that division.

---

## 8. Invariants

1. **The ridge is ~300 FLOPs/byte. Decode at batch 1 is ~1.** Memory-bound; everything follows.
2. **Batching turns one weight read into many tokens.** Throughput scales until compute binds.
3. **Fewer bits = fewer bytes = faster.** int8 free; int4 needs group scales; int2 is destruction.
4. **FlashAttention trades recomputation for memory.** Exact; linear in `T`.
5. **Three parallelisms, three communication bills.** Combine them.
6. **MoE separates knowledge (total) from compute (active).** Pays in memory and balancing.
7. **Cost per token is arithmetic on the above.** Measure MFU, tokens/s, $/M — and convert fluently.
