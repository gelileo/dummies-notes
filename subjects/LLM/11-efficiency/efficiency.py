#!/usr/bin/env python3
"""Efficiency, as arithmetic and small measurements: the roofline, quantization error,
attention memory with and without tiling, communication volume for the three
parallelisms, MoE active-vs-total parameters, and cost per token. numpy.
Run: python3 efficiency.py
"""
import numpy as np
rng = np.random.default_rng(0)

H100 = dict(peak_bf16=990e12, hbm=3.35e12, hbm_gb=80)          # published spec sheet figures
LLAMA8B = dict(N=8.03e9, layers=32, d=4096, ffn=14336, heads=32, kv_heads=8, dh=128, vocab=128256)

if __name__ == "__main__":
    np.set_printoptions(precision=3, suppress=True)
    print("=== 1. the roofline: are you limited by arithmetic or by memory traffic? ===")
    ridge = H100["peak_bf16"] / H100["hbm"]
    print(f"   H100: {H100['peak_bf16']/1e12:.0f} TFLOP/s bf16, {H100['hbm']/1e12:.2f} TB/s memory -> ridge point {ridge:.0f} FLOPs per byte")
    print("   an operation with fewer FLOPs per byte moved than that is memory-bound: the chip idles")
    print("   waiting for data. more, and it is compute-bound. so count both for a matmul [B,d]@[d,n]:")
    d, n = LLAMA8B["d"], LLAMA8B["ffn"]
    print(f"   {'batch B':>8}{'FLOPs':>12}{'bytes (bf16)':>14}{'FLOPs/byte':>12}   regime")
    for B in (1, 8, 64, 256, 1024):
        flops = 2 * B * d * n; byts = 2 * (B*d + d*n + B*n)
        print(f"   {B:>8}{flops:>12.2e}{byts:>14.2e}{flops/byts:>12.0f}   {'memory-bound' if flops/byts < ridge else 'compute-bound'}")
    print("   decoding one token for one user is B=1: ~1 FLOP per byte. the weight matrix is read")
    print("   once and used once. batch users together and the same read serves all of them.")

    print("\n=== 2. what that means for tokens per second ===")
    wbytes = LLAMA8B["N"] * 2
    t_read = wbytes / H100["hbm"]
    print(f"   Llama-3-8B bf16 weights: {wbytes/1e9:.1f} GB. one full read: {t_read*1e3:.1f} ms -> at most {1/t_read:.0f} tok/s for ONE sequence")
    print(f"   {'batch':>6}{'tokens/s total':>16}{'per-user tok/s':>16}{'compute needed':>16}")
    for B in (1, 8, 32, 128):
        flops_per_step = 2 * LLAMA8B["N"] * B
        t = max(t_read, flops_per_step / H100["peak_bf16"])
        print(f"   {B:>6}{B/t:>16.0f}{1/t:>16.0f}{flops_per_step/H100['peak_bf16']*1e3:>13.2f} ms")
    print("   throughput scales almost linearly with batch until compute catches up with memory.")
    print("   that is continuous batching's entire reason to exist.")

    print("\n=== 3. quantization: fewer bits per weight ===")
    W = rng.normal(0, 0.02, (512, 512)); W[rng.integers(0, 512, 20), rng.integers(0, 512, 20)] *= 8   # a few outliers, as real weights have
    x = rng.normal(size=(64, 512)); y = x @ W
    def quant(W, bits, group):
        levels = 2**(bits-1) - 1
        Wq = np.empty_like(W)
        for g in range(0, W.shape[1], group):
            blk = W[:, g:g+group]; scale = np.abs(blk).max(1, keepdims=True) / levels
            Wq[:, g:g+group] = np.round(blk / scale).clip(-levels, levels) * scale
        return Wq
    print(f"   {'format':<18}{'bits':>5}{'GB for 8B':>10}{'rel. output error':>19}")
    print(f"   {'bf16 (reference)':<18}{16:>5}{LLAMA8B['N']*16/8/1e9:>10.1f}{0.0:>19.4f}")
    for name, bits, group in (("int8, per-row", 8, 512), ("int4, per-row", 4, 512), ("int4, group 128", 4, 128),
                              ("int4, group 32", 4, 32), ("int2, group 32", 2, 32)):
        err = np.linalg.norm(x @ quant(W, bits, group) - y) / np.linalg.norm(y)
        print(f"   {name:<18}{bits:>5}{LLAMA8B['N']*bits/8/1e9:>10.1f}{err:>19.4f}")
    print("   int8 is nearly free. naive int4 with one scale per row is lossy, because a single")
    print("   outlier stretches the scale and wastes levels on everyone else. give each block of")
    print("   32 weights its own scale and int4 error falls by about a third -- that is the 'group")
    print("   size' in GGUF/AWQ/GPTQ. error-compensating rounding (GPTQ) and scaling the outlier")
    print("   channels before quantising (AWQ) do the rest of the work. int2 is")
    print("   destruction either way. (per-layer output error overstates the loss impact; the")
    print("   network absorbs some of it. measure perplexity, not this.)")

    print("\n=== 4. attention memory: materialise the T x T scores, or tile? ===")
    print(f"   {'T':>7}{'score matrix per head (bf16)':>30}{'x32 heads':>13}{'tiled, block 128 (approx.)':>28}")
    def fmt(b): return f"{b/1e9:.1f} GB" if b >= 1e9 else f"{b/1e6:.0f} MB"
    for T in (1024, 4096, 32768, 131072):
        full = T * T * 2; tiled = 2 * 128 * T * 2   # one block of Q rows against all K, for S and P
        print(f"   {T:>7,}{fmt(full):>30}{fmt(full*32):>13}{fmt(tiled):>28}")
    print("   at 128k context the full score matrix is 34 GB per head. FlashAttention never builds")
    print("   it: it streams K,V in blocks, keeps a running softmax, and recomputes in the backward")
    print("   pass. same maths, exact result, memory linear in T. that is why long context exists.")

    print("\n=== 5. parallelism: what each strategy sends over the wire, per step ===")
    N, L, d, B_tok = LLAMA8B["N"], LLAMA8B["layers"], LLAMA8B["d"], 16_000_000
    micro = 4096 * 8                                             # one micro-batch of tokens per device
    print(f"   data parallel:     all-reduce the GRADIENTS: 2 x {N*2/1e9:.0f} GB (bf16) per step per device")
    print(f"   tensor parallel:   all-reduce ACTIVATIONS twice per layer: 2 x {L} x {micro*d*2/1e9:.2f} GB = {2*L*micro*d*2/1e9:.1f} GB per micro-batch")
    print(f"   pipeline parallel: send one layer boundary's activations: {micro*d*2/1e9:.2f} GB per micro-batch, point to point")
    print("   data parallel sends the model; tensor parallel sends activations constantly (needs")
    print("   NVLink-class bandwidth, so it stays inside a node); pipeline sends little but idles")
    print("   while the bubble fills. real runs combine all three -- '3D parallelism'.")

    print("\n=== 6. mixture of experts: parameters you store vs parameters you use ===")
    print("   illustrative shapes; per-layer: shared (attention) params + experts x params each, 32 layers")
    for name, experts, active, expert_params, shared in (("dense 7B", 1, 1, 176e6, 42e6),
                                                        ("8 experts, top-2 (Mixtral-like)", 8, 2, 176e6, 42e6),
                                                        ("64 small experts, top-8", 64, 8, 22e6, 42e6)):
        total = 32 * (shared + experts * expert_params); act = 32 * (shared + active * expert_params)
        print(f"   {name:<34} total {total/1e9:>6.1f}B   active per token {act/1e9:>5.1f}B   FLOPs/token ~ {2*act:.1e}")
    print("   (Mixtral 8x7B reports ~47B total / ~13B active -- reported, and the shape above lands there.)")
    print("   MoE buys knowledge (total params) at the price of memory, while paying compute only")
    print("   for the active experts. a router picks which experts each token visits; balancing")
    print("   the router so every expert gets traffic is its own loss term.")

    print("\n=== 7. cost per million tokens (illustrative) ===")
    gpu_hour = 3.0                                                 # illustrative $/GPU-hour
    for B in (8, 64):
        flops_per_step = 2 * LLAMA8B["N"] * B; t = max(t_read, flops_per_step / H100["peak_bf16"]) / 0.5   # 50% efficiency
        tok_s = B / t
        print(f"   batch {B:>3}: {tok_s:>7,.0f} tok/s -> ${gpu_hour/(tok_s*3600)*1e6:>6.2f} per million output tokens at ${gpu_hour}/GPU-hour")
    print("   the arithmetic is the product; the constants ($/hour, utilisation) are assumptions.")
