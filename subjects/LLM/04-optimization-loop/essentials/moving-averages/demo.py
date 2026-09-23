#!/usr/bin/env python3
"""Exponential moving averages -- the mechanism inside momentum and Adam.
Run: python3 demo.py"""
import numpy as np
rng = np.random.default_rng(0)

print("=== a noisy signal, and a running average that forgets the past gradually ===")
true = 2.0
noisy = true + rng.normal(0, 1.5, 12)
for beta in (0.5, 0.9):
    m = 0.0; trail = []
    for g in noisy:
        m = beta*m + (1-beta)*g
        trail.append(m)
    print(f"   beta={beta}: " + " ".join(f"{v:5.2f}" for v in trail))
print(f"   raw     : " + " ".join(f"{v:5.2f}" for v in noisy))
print(f"   truth = {true}. beta=0.9 is smoother but slower to arrive. rule of thumb:")
print(f"   beta=0.9 averages over ~1/(1-0.9) = 10 steps; beta=0.999 over ~1000.")

print("\n=== the startup bias, and how Adam corrects it ===")
m = 0.0; beta = 0.9
print(f"   {'step t':>7}{'ema':>8}{'ema/(1-beta^t)':>17}   (true value 2.0)")
for t in range(1, 8):
    m = beta*m + (1-beta)*2.0
    print(f"   {t:>7}{m:>8.3f}{m/(1-beta**t):>17.3f}")
print("   the ema starts at 0 and is biased low early on. dividing by (1-beta^t)")
print("   removes exactly that bias. those are Adam's 'mhat' and 'vhat'.")

print("\n=== Adam: two averages give a per-parameter step size ===")
print("   m = ema of the gradient      (which way, on average)")
print("   v = ema of gradient squared  (how big, on average)")
print("   step = lr * m / sqrt(v)")
print("   two parameters with very different gradient scales:")
for name, scale in (("param A, gradients ~ 0.001", 0.001), ("param B, gradients ~ 10", 10.0)):
    gs = scale * (1 + 0.3*rng.normal(size=200))
    m = v = 0.0
    for g in gs:
        m = 0.9*m + 0.1*g; v = 0.999*v + 0.001*g*g
    mhat, vhat = m/(1-0.9**200), v/(1-0.999**200)
    print(f"   {name:<30} m={mhat:9.4f}  sqrt(v)={np.sqrt(vhat):8.4f}  m/sqrt(v)={mhat/np.sqrt(vhat):6.3f}")
print("   both get a step of about lr * 1.0. Adam normalises away the gradient's")
print("   scale, so one learning rate serves every parameter -- that is its whole appeal.")
