#!/usr/bin/env python3
"""Averages, spread, and why attention divides by sqrt(d_head).
Run: python3 normalize_demo.py"""
import math, random
dot = lambda a, b: sum(x*y for x, y in zip(a, b))

print("=== mean, variance, standard deviation ===")
data = [2, 4, 4, 4, 5, 5, 7, 9]
mean = sum(data)/len(data)
var  = sum((x-mean)**2 for x in data)/len(data)
print(f"   data      {data}")
print(f"   mean      {mean}                 <- the balance point")
print(f"   variance  {var}                 <- average squared distance from the mean")
print(f"   std dev   {math.sqrt(var)}                 <- typical distance from the mean")

print("\n=== root mean square: size, ignoring sign ===")
for v in ([3, 4], [-3, -4], [1, 1, 1, 1], [0, 0, 0, 8]):
    rms = math.sqrt(sum(x*x for x in v)/len(v))
    print(f"   rms({str(v):<14}) = {rms:.3f}   (mean = {sum(v)/len(v):>5.1f})")
print("   RMSNorm divides a vector by this, so its typical entry becomes about 1.")

print("\n=== the key fact: a dot product's spread grows with sqrt(d) ===")
print("   two random vectors of length d, 2000 trials each:")
print(f"   {'d':>6}{'mean |a.b|':>13}{'std of a.b':>13}{'std / sqrt(d)':>15}")
for d in (4, 16, 64, 256, 1024, 4096):
    random.seed(0)
    s = [dot([random.gauss(0,1) for _ in range(d)],
             [random.gauss(0,1) for _ in range(d)]) for _ in range(2000)]
    m = sum(s)/len(s)
    sd = math.sqrt(sum((x-m)**2 for x in s)/len(s))
    print(f"   {d:>6}{sum(abs(x) for x in s)/len(s):>13.2f}{sd:>13.2f}{sd/math.sqrt(d):>15.3f}")
print("   The last column is flat at ~1.0. So the spread is exactly proportional")
print("   to sqrt(d) -- which is why dividing by sqrt(d_head) cancels it.")

def softmax(v):
    m = max(v); e = [math.exp(x-m) for x in v]; s = sum(e); return [x/s for x in e]

print("\n=== what that does to attention ===")
for d, label in ((4, "toy d_head=4"), (128, "Llama-3 d_head=128")):
    random.seed(1)
    q  = [random.gauss(0,1) for _ in range(d)]
    ks = [[random.gauss(0,1) for _ in range(d)] for _ in range(5)]
    raw = [dot(q,k) for k in ks]
    print(f"   {label}")
    print(f"      without /sqrt(d): scores {[f'{x:6.1f}' for x in raw]}")
    print(f"                        weights {[f'{p:.3f}' for p in softmax(raw)]}")
    sc = [x/math.sqrt(d) for x in raw]
    print(f"      with    /sqrt(d): scores {[f'{x:6.1f}' for x in sc]}")
    print(f"                        weights {[f'{p:.3f}' for p in softmax(sc)]}")
