#!/usr/bin/env python3
"""FLOPs, and the units training compute is measured in. Run: python3 demo.py"""
import numpy as np

print("=== a FLOP is one floating-point operation: one multiply, or one add ===")
n, k, m = 4, 3, 2
print(f"   [n,k]@[k,m] with n={n}, k={k}, m={m}: each of the n*m={n*m} outputs is a dot product")
print(f"   of length k={k}: {k} multiplies + {k-1} adds ~ 2k FLOPs. total ~ 2*n*k*m = {2*n*k*m}.")
print("   rule: a matrix multiply costs 2 * (rows) * (inner) * (cols) FLOPs.")

print("\n=== one token through a weight matrix with P parameters: 2P FLOPs ===")
for name, rows, cols in (("W_Q of Llama-3-8B", 4096, 4096), ("W_up of Llama-3-8B", 4096, 14336)):
    P = rows*cols
    print(f"   {name:<20} P = {P:>12,}   forward per token = 2P = {2*P:>13,} FLOPs")
print("   backward is ~2x forward (two matrix products), so forward+backward = 6P per token.")

print("\n=== the sizes involved, in one table ===")
units = [("FLOP", 1), ("GFLOP (1e9)", 1e9), ("TFLOP (1e12)", 1e12), ("PFLOP (1e15)", 1e15),
         ("EFLOP (1e18)", 1e18), ("ZFLOP (1e21)", 1e21)]
for name, v in units: print(f"   {name:<14} {v:>10.0e}")
print("   a training run is ~1e23-1e26 FLOPs: hundreds of thousands to billions of ZFLOPs' worth.")

print("\n=== throughput: FLOP/s, and what a GPU actually delivers ===")
peak = 990e12
for mfu in (1.0, 0.5, 0.4, 0.3):
    print(f"   H100 bf16 dense peak {peak:.0e} FLOP/s x MFU {mfu:.0%} = {peak*mfu:.2e} FLOP/s achieved")
print("   MFU (model FLOPs utilisation) = useful FLOPs / peak. 30-50% is typical; the rest is")
print("   memory traffic, communication, and idle time (chapter 11).")

print("\n=== converting a budget into hardware and time ===")
C = 7.2e23
for gpus in (1, 1000, 16000):
    hours = C / (peak*0.4) / 3600 / gpus
    print(f"   {C:.1e} FLOPs on {gpus:>6,} H100s at 40% MFU: {hours:>12,.0f} hours = {hours/24:>8,.1f} days")
print(f"   the same number as GPU-hours: {C/(peak*0.4)/3600:,.0f}  |  as PFLOP/s-days: {C/1e15/86400:,.0f}")
print("   PFLOP/s-days (petaFLOP-per-second for a day) is the unit the GPT-3 paper used.")

print("\n=== the two things a budget buys: parameters and tokens ===")
for N, D in ((1e9, 2e10), (8e9, 1.5e13), (7e10, 1.5e13), (4e11, 1.5e13)):
    print(f"   N={N:.0e} params, D={D:.1e} tokens -> 6ND = {6*N*D:.1e} FLOPs")
print("   ten times the parameters at the same data is ten times the compute. chapter 06's")
print("   whole question is how to split a fixed budget between the two.")
