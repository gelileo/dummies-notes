#!/usr/bin/env python3
"""The chain rule, and why backpropagation runs backwards. Run: python3 demo.py"""
import math
h = 1e-6

print("=== composing functions multiplies their slopes ===")
inner = lambda x: 3*x + 1          # u = 3x + 1       slope 3
outer = lambda u: u*u              # y = u^2          slope 2u
comp  = lambda x: outer(inner(x))
x = 2.0
u = inner(x)
print(f"   y = (3x+1)^2 at x={x}:  u = {u}")
print(f"   dy/du = 2u = {2*u}      du/dx = 3")
print(f"   chain rule: dy/dx = dy/du * du/dx = {2*u} * 3 = {2*u*3}")
print(f"   numeric check:            {(comp(x+h)-comp(x))/h:.3f}")

print("\n=== a longer chain: just keep multiplying ===")
x = 0.5
a = x*x;  da = 2*x              # a = x^2
b = math.sin(a); db = math.cos(a)  # b = sin(a)
c = math.exp(b); dc = math.exp(b)  # c = exp(b)
d = 5*c;  dd = 5                # d = 5c
print(f"   d = 5*exp(sin(x^2)) at x={x}")
print(f"   local slopes: dd/dc={dd}  dc/db={dc:.4f}  db/da={db:.4f}  da/dx={da}")
print(f"   product = {dd*dc*db*da:.4f}")
F = lambda x: 5*math.exp(math.sin(x*x))
print(f"   numeric  = {(F(x+h)-F(x))/h:.4f}")

print("\n=== why 'backward': one output, many inputs ===")
print("   a loss is ONE number that depends on MILLIONS of parameters.")
print("   forward-mode: one pass per input -> millions of passes.")
print("   reverse-mode: start at the output with slope 1, walk back once,")
print("   multiplying local slopes; every input gets its gradient in ONE pass.")
for n in (10, 1_000, 8_000_000_000):
    print(f"   {n:>14,} parameters: forward-mode {n:>14,} passes   reverse-mode 1 pass")

print("\n=== vanishing: multiply many slopes below 1 and nothing is left ===")
for depth in (1, 5, 10, 20, 50):
    print(f"   {depth:>3} layers, local slope 0.5 each: gradient x {0.5**depth:.2e}")
print("   this is why deep nets were untrainable -- and why the residual connection's")
print("   '+1' slope (chapter 02) fixed it: 1 + small, multiplied, stays near 1.")
for depth in (10, 50):
    print(f"   {depth:>3} layers of (1 + 0.5*small): x {(1+0.05)**depth:.2f}  -- survives")
