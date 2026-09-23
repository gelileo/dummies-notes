#!/usr/bin/env python3
"""Generates efficiency.md from efficiency.py. Run: python3 systems.py"""
import io, numpy as np
import efficiency as E
o = io.StringIO(); W = o.write
rng = np.random.default_rng(0)
H, M = E.H100, E.LLAMA8B

W(f"""# Efficiency, traced

Every number here is produced by `efficiency.py`. Run `python3 systems.py` to regenerate.

The maths of the Transformer has not changed since 2017; the cost of running it has fallen by
orders of magnitude. All of that came from fitting the same computation to the hardware better.
This is the systems chapter, and it rests on one fact measured first.

---

## 1. The roofline: memory or arithmetic?

An H100 does about {H['peak_bf16']/1e12:.0f} TFLOP/s of bf16 arithmetic and moves about {H['hbm']/1e12:.2f} TB/s from memory. The ratio
— **{H['peak_bf16']/H['hbm']:.0f} FLOPs per byte** — is the ridge. An operation that does fewer FLOPs than that per byte it
moves is waiting on memory; more, and it is waiting on arithmetic.

For a matrix multiply `[B, d] @ [d, n]` with Llama-3-8B's MLP shape:

```
  {'batch B':>8}{'FLOPs':>12}{'bytes (bf16)':>14}{'FLOPs/byte':>12}   regime
""")
ridge = H["peak_bf16"] / H["hbm"]; d, n = M["d"], M["ffn"]
for B in (1, 8, 64, 256, 1024):
    flops = 2*B*d*n; byts = 2*(B*d + d*n + B*n)
    W(f"  {B:>8}{flops:>12.2e}{byts:>14.2e}{flops/byts:>12.0f}   {'memory-bound' if flops/byts < ridge else 'compute-bound'}\n")
W(f"""```

Decoding one token for one user is `B = 1`: about **one FLOP per byte**. The weight matrix is
read from memory and used once. Nearly everything in this chapter is a way of not doing that.
→ [essentials: roofline](essentials/roofline-and-arithmetic-intensity/)

---

## 2. Tokens per second

```
""")
wbytes = M["N"]*2; t_read = wbytes / H["hbm"]
W(f"  Llama-3-8B bf16 weights: {wbytes/1e9:.1f} GB.  one full read: {t_read*1e3:.1f} ms  ->  at most {1/t_read:.0f} tok/s for ONE sequence\n\n")
W(f"  {'batch':>6}{'tokens/s total':>16}{'per-user tok/s':>16}{'compute per step':>18}\n")
for B in (1, 8, 32, 128):
    fps = 2*M["N"]*B; t = max(t_read, fps/H["peak_bf16"])
    W(f"  {B:>6}{B/t:>16.0f}{1/t:>16.0f}{fps/H['peak_bf16']*1e3:>15.2f} ms\n")
W(f"""```

Throughput scales almost linearly with batch until the arithmetic catches up with the memory
read — the same weight stream serves every sequence in the batch. That is the entire reason
**continuous batching** exists, and why serving cost per token falls so steeply with load.

---

## 3. Quantization

Fewer bits per weight means fewer bytes to stream — which, given section 1, is the same as
faster decoding. The question is what it costs in accuracy:

```
""")
W_ = rng.normal(0, 0.02, (512, 512)); W_[rng.integers(0, 512, 20), rng.integers(0, 512, 20)] *= 8
x = rng.normal(size=(64, 512)); y = x @ W_
def quant(Wm, bits, group):
    levels = 2**(bits-1) - 1; Wq = np.empty_like(Wm)
    for g in range(0, Wm.shape[1], group):
        blk = Wm[:, g:g+group]; scale = np.abs(blk).max(1, keepdims=True) / levels
        Wq[:, g:g+group] = np.round(blk / scale).clip(-levels, levels) * scale
    return Wq
W(f"  {'format':<18}{'bits':>5}{'GB for 8B':>10}{'rel. output error':>19}\n")
W(f"  {'bf16 (reference)':<18}{16:>5}{M['N']*16/8/1e9:>10.1f}{0.0:>19.4f}\n")
for name, bits, group in (("int8, per-row", 8, 512), ("int4, per-row", 4, 512), ("int4, group 128", 4, 128), ("int4, group 32", 4, 32), ("int2, group 32", 2, 32)):
    err = np.linalg.norm(x @ quant(W_, bits, group) - y) / np.linalg.norm(y)
    W(f"  {name:<18}{bits:>5}{M['N']*bits/8/1e9:>10.1f}{err:>19.4f}\n")
W(f"""```

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
""")
def fmt(b): return f"{b/1e9:.1f} GB" if b >= 1e9 else f"{b/1e6:.0f} MB"
W(f"  {'T':>8}{'score matrix, one head':>25}{'× 32 heads':>13}{'tiled, block 128 (approx.)':>28}\n")
for T in (1024, 4096, 32768, 131072):
    full = T*T*2; tiled = 2*128*T*2
    W(f"  {T:>8,}{fmt(full):>25}{fmt(full*32):>13}{fmt(tiled):>28}\n")
W(f"""```

At 128k context the full matrix is 34 GB *per head*. FlashAttention never builds it: it streams
keys and values through on-chip memory in blocks, keeps a running softmax, and recomputes what it
needs in the backward pass. Same mathematics, exact result, memory linear in `T`. That is the
canonical hardware-aware algorithm, and it is why long context exists at all.

---

## 5. Parallelism: what crosses the wire

One model, thousands of GPUs. Three ways to split it, each with a different communication bill:

```
""")
N, L, d_ = M["N"], M["layers"], M["d"]; micro = 4096*8
W(f"  data parallel      all-reduce the GRADIENTS       2 × {N*2/1e9:.0f} GB (bf16) per step, per device\n")
W(f"  tensor parallel    all-reduce ACTIVATIONS, twice per layer:  2 × {L} × {micro*d_*2/1e9:.2f} GB = {2*L*micro*d_*2/1e9:.1f} GB per micro-batch\n")
W(f"  pipeline parallel  send one layer boundary's activations:   {micro*d_*2/1e9:.2f} GB per micro-batch, point to point\n")
W(f"""```

**Data parallel** copies the model and splits the batch; every step it must average gradients
the size of the model (ZeRO/FSDP shard the copies to save memory). **Tensor parallel** splits
individual matrices and must exchange activations constantly — it needs NVLink-class bandwidth
and so stays inside one node. **Pipeline parallel** puts different layers on different devices
and sends little, but idles while the pipeline fills. Frontier runs combine all three.

---

## 6. Mixture of experts

```
""")
W(f"  illustrative shapes; per layer: shared attention params + experts × params each; 32 layers\n\n")
for name, experts, active, ep, shared in (("dense 7B", 1, 1, 176e6, 42e6), ("8 experts, top-2 (Mixtral-like)", 8, 2, 176e6, 42e6), ("64 small experts, top-8", 64, 8, 22e6, 42e6)):
    total = 32*(shared + experts*ep); act = 32*(shared + active*ep)
    W(f"  {name:<34} total {total/1e9:>6.1f}B   active per token {act/1e9:>5.1f}B   FLOPs/token ≈ {2*act:.1e}\n")
W(f"""```

Replace each MLP with several **experts** and a router that sends each token to a few of them.
Total parameters — knowledge — go up several-fold; compute per token stays at the active
fraction. The price is memory (every expert must be resident) and a balancing loss so that no
expert starves. Mixtral 8×7B reports about 47B total and 13B active *(reported)*; the middle row
lands on that shape.

---

## 7. Cost per million tokens

```
""")
gpu_hour = 3.0
for B in (8, 64):
    fps = 2*M["N"]*B; t = max(t_read, fps/H["peak_bf16"]) / 0.5; tok_s = B/t
    W(f"  batch {B:>3}:  {tok_s:>7,.0f} tok/s  ->  ${gpu_hour/(tok_s*3600)*1e6:>5.2f} per million output tokens   (at ${gpu_hour}/GPU-hour, 50% efficiency)\n")
W(f"""```

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
""")
open('efficiency.md', 'w').write(o.getvalue())
print("wrote efficiency.md", len(o.getvalue()), "chars")
