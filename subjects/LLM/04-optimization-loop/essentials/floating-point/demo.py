#!/usr/bin/env python3
"""How computers store decimals, and why training uses bf16. Run: python3 demo.py"""
import numpy as np

def bf16(v):
    b = np.asarray(v, dtype=np.float32).view(np.uint32) & np.uint32(0xFFFF0000)
    return float(b.view(np.float32))

print("=== a float is sign + exponent + mantissa, in a fixed number of bits ===")
print(f"   {'format':<8}{'total':>7}{'exponent':>10}{'mantissa':>10}{'largest value':>16}{'gap at 1.0':>13}")
for name, tot, e, m, mx in (("fp32", 32, 8, 23, 3.4e38), ("fp16", 16, 5, 10, 65504), ("bf16", 16, 8, 7, 3.4e38)):
    print(f"   {name:<8}{tot:>7}{e:>10}{m:>10}{mx:>16g}{2.0**-m:>13.2e}")
print("   exponent bits buy RANGE (how big/small). mantissa bits buy PRECISION (how fine).")

print("\n=== precision: what can each format tell apart near 1.0? ===")
for v in (1 + 1e-2, 1 + 1e-3, 1 + 1e-4):
    print(f"   {v:<10.4f} fp32 {np.float32(v):<12.6f} fp16 {float(np.float16(v)):<12.6f} bf16 {bf16(v):<12.6f}")
print("   bf16 cannot see 1.001: it rounds to 1.0. fp16 can. fp16 has more precision.")

print("\n=== range: what happens to a big number? ===")
for v in (60000.0, 65504.0, 70000.0, 1e10, 3e38):
    with np.errstate(over="ignore"):
        print(f"   {v:<10g} fp16 {float(np.float16(v)):<12g} bf16 {bf16(v):<12g}")
print("   fp16 dies at 65504 -> inf. bf16 reaches 3e38 like fp32. bf16 has more range.")

print("\n=== decimals are not exact ===")
print(f"   0.1 + 0.2 == 0.3 ?  {0.1 + 0.2 == 0.3}    (0.1 + 0.2 = {0.1 + 0.2:.20f})")
s16 = np.float16(0); s32 = np.float32(0)
for _ in range(10000):
    s16 += np.float16(0.1); s32 += np.float32(0.1)
print(f"   add 0.1 ten thousand times: fp16 {float(s16):.1f}   fp32 {float(s32):.3f}   exact 1000")
print("   errors accumulate. this is why the optimizer keeps a fp32 'master' copy of")
print("   the weights and only uses 16-bit for the big matrix multiplies.")

print("\n=== why bf16 won for training ===")
print("   gradients range across many orders of magnitude within one model.")
print("   losing precision in the 3rd decimal is harmless; overflowing to inf is fatal.")
print("   fp16 needs 'loss scaling' (multiply the loss by ~1000 so tiny gradients")
print("   stay above fp16's floor, then divide back). bf16 does not.")
