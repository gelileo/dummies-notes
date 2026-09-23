#!/usr/bin/env python3
"""Bytes vs FLOPs: the roofline model, and why batch size decides everything.
Run: python3 demo.py"""
import numpy as np

PEAK, BW = 990e12, 3.35e12      # H100: bf16 dense FLOP/s, HBM bytes/s (spec sheet)
print("=== two speed limits ===")
print(f"   arithmetic: {PEAK:.2e} FLOP/s      memory: {BW:.2e} bytes/s")
print(f"   ridge point = arithmetic / memory = {PEAK/BW:.0f} FLOPs per byte")
print("   an operation doing fewer FLOPs per byte it moves is waiting on memory (memory-bound).")
print("   more, and it is waiting on arithmetic (compute-bound). the roofline is min(peak, BW x intensity).")

print("\n=== arithmetic intensity of a matrix multiply [B,d] @ [d,n] ===")
print("   FLOPs = 2*B*d*n.  bytes = 2*(B*d + d*n + B*n) in bf16.  for large d,n the weight term d*n dominates:")
print("   intensity ~ 2*B*d*n / (2*d*n) = B.   each row of the batch reuses the same weights once more.")
d, n = 4096, 14336
print(f"   {'B':>6}{'FLOPs':>12}{'bytes':>12}{'FLOPs/byte':>12}{'time (ms)':>11}   bound")
for B in (1, 4, 16, 64, 256, 1024, 4096):
    flops = 2*B*d*n; byts = 2*(B*d + d*n + B*n); inten = flops/byts
    t = max(flops/PEAK, byts/BW)
    print(f"   {B:>6}{flops:>12.1e}{byts:>12.1e}{inten:>12.0f}{t*1e3:>11.3f}   {'memory' if inten < PEAK/BW else 'compute'}")
print("   below the ridge, doubling B is nearly free -- the time is the weight read either way.")

print("\n=== the same fact from the other side: utilisation ===")
for B in (1, 16, 256, 1024):
    flops = 2*B*d*n; byts = 2*(B*d + d*n + B*n); t = max(flops/PEAK, byts/BW)
    print(f"   B={B:<5} achieved {flops/t/1e12:>7.0f} TFLOP/s = {flops/t/PEAK:>5.0%} of peak")
print("   at B=1 the chip is ~0.3% utilised. this is why single-user decode is so wasteful and why")
print("   serving systems batch requests together.")

print("\n=== not just matmuls: every op has an intensity ===")
for name, flops_per_elem, bytes_per_elem in (("elementwise add", 1, 6), ("softmax (approx)", 5, 4), ("layernorm (approx)", 8, 4), ("matmul B=256", 256, 1)):
    print(f"   {name:<20} ~{flops_per_elem/bytes_per_elem:>6.2f} FLOPs/byte -> {'memory-bound' if flops_per_elem/bytes_per_elem < PEAK/BW else 'compute-bound'}")
print("   almost everything except a big matmul is memory-bound. kernel fusion exists to avoid")
print("   writing an intermediate to memory and reading it straight back.")
