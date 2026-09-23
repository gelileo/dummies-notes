#!/usr/bin/env python3
"""Where d_model shows up, how it scales, and a parameter-count check against
published model sizes. Run: python3 dmodel_check.py"""
print("=== parameters per layer grow with d_model SQUARED ===")
print(f"   {'d_model':>8}{'params/layer':>16}{'x':>8}")
prev = None
for d in (512, 1024, 2048, 4096, 8192):
    ffn = int(d*3.5)
    p = 4*d*d + 3*d*ffn + 2*d
    print(f"   {d:>8}{p:>16,}" + ("" if prev is None else f"{p/prev:>8.1f}"))
    prev = p

def gpt2(d, L, ffn, V, ctx):
    per = 2*d + (d*3*d + 3*d) + (d*d + d) + 2*d + (d*ffn + ffn) + (ffn*d + d)
    return V*d + ctx*d + L*per + 2*d

def llama(d, L, H, KV, dh, ffn, V):
    per = d*(H*dh) + 2*d*(KV*dh) + (H*dh)*d + 3*d*ffn + 2*d
    return V*d + L*per + d + V*d

print("\n=== check d_model values against published parameter counts ===")
for label, got, published in [
        ("GPT-2 small  d_model=768 ", gpt2(768, 12, 3072, 50257, 1024),        124e6),
        ("Llama-3-8B   d_model=4096", llama(4096, 32, 32, 8, 128, 14336, 128256), 8.03e9),
        ("Llama-3-70B  d_model=8192", llama(8192, 80, 64, 8, 128, 28672, 128256), 70.6e9)]:
    ok = "OK" if abs(got - published) < max(1e6, published*0.02) else "MISMATCH"
    print(f"   {label} -> {got:>15,}   (published ~{published/1e9:.2f}B)   {ok}")

print("\n=== d_model = n_heads x d_head ===")
for name, H, dh, d in [("GPT-2 small", 12, 64, 768), ("Llama-3-8B", 32, 128, 4096),
                       ("Llama-3-70B", 64, 128, 8192)]:
    print(f"   {name:<14}{H:>3} heads x {dh:>4} = {H*dh:>6}   d_model={d}   "
          f"{'OK' if H*dh == d else 'NO'}")
