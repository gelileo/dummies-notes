#!/usr/bin/env python3
"""Logarithms, and why a loss is measured in bits or nats. Run: python3 demo.py"""
import math

print("=== log is the inverse of exp: it asks 'what power?' ===")
for x in (1, 2, 4, 8, 1024):
    print(f"   log2({x:>5}) = {math.log2(x):>4.0f}    because 2^{math.log2(x):.0f} = {x}")
print(f"   ln(e)  = {math.log(math.e):.0f},   ln(1) = {math.log(1):.0f},   log2(1) = {math.log2(1):.0f}")

print("\n=== the rule everything hinges on: log(a*b) = log(a) + log(b) ===")
a, b = 0.3, 0.02
print(f"   log({a}*{b}) = {math.log(a*b):.4f}")
print(f"   log({a}) + log({b}) = {math.log(a) + math.log(b):.4f}")
print("   multiplication becomes addition. That is the only reason logs appear.")

print("\n=== why you cannot avoid logs: probabilities multiply into nothing ===")
p = 0.05
prod = 1.0
for i in range(1, 401):
    prod *= p
    if i in (10, 50, 100, 200, 300, 400):
        print(f"   {i:>3} tokens at p={p}:  product = {prod:.3e}    sum of logs = {i*math.log(p):>9.1f}")
print("   By 300 tokens the product has underflowed to exactly 0.0 and the")
print("   information is gone. The sum of logs is a perfectly ordinary number.")

print("\n=== -log(p) is 'surprise': small p, big number ===")
for p in (1.0, 0.5, 0.25, 0.1, 0.01, 0.001):
    print(f"   p = {p:<6}  -ln p = {-math.log(p):6.3f} nats   -log2 p = {-math.log2(p):6.3f} bits")
print("   A certain event (p=1) costs 0. Halving p adds exactly 1 bit, every time.")

print("\n=== bits are yes/no questions ===")
for n in (2, 4, 8, 16, 1024):
    print(f"   one of {n:>4} equally likely options -> log2({n}) = {math.log2(n):>4.0f} questions to pin it down")

print("\n=== nats and bits are the same thing in different units ===")
nats = 1.232
print(f"   {nats} nats = {nats/math.log(2):.3f} bits     (divide by ln 2 = {math.log(2):.4f})")
print(f"   {nats} nats -> perplexity exp({nats}) = {math.exp(nats):.2f}")
print("   Papers quote loss in nats (natural log), compression people in bits.")
