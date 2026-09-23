#!/usr/bin/env python3
"""Derivatives, gradients, and stepping downhill. Run: python3 demo.py"""
import math

print("=== a derivative is a slope: how much f changes per tiny nudge of x ===")
f = lambda x: x*x
h = 1e-6
print(f"   f(x) = x^2")
print(f"   {'x':>5}{'(f(x+h)-f(x))/h':>18}{'2x':>6}")
for xv in (-2, -1, 0, 1, 3):
    print(f"   {xv:>5}{(f(xv+h)-f(xv))/h:>18.4f}{2*xv:>6}")
print("   The slope of x^2 is 2x. Negative slope = f is falling as x grows.")

print("\n=== a gradient is one slope per input, bundled into a vector ===")
g = lambda x, y: x*x + 3*y*y
def grad(x, y): return ((g(x+h,y)-g(x,y))/h, (g(x,y+h)-g(x,y))/h)
for pt in ((1, 1), (2, -1), (0, 0)):
    gx, gy = grad(*pt)
    print(f"   f(x,y) = x^2 + 3y^2   at {pt}: gradient = ({gx:.3f}, {gy:.3f})   [exact: ({2*pt[0]}, {6*pt[1]})]")
print("   Each entry: hold everything else still, nudge one input, measure. That is a")
print("   'partial derivative'. The vector of all of them is the gradient.")

print("\n=== the gradient points UPHILL, so step the other way ===")
x, y = 2.0, -1.0
print(f"   start at ({x}, {y}), f = {g(x,y):.3f}")
for name, lr in (("small step  lr=0.05", 0.05), ("good step   lr=0.15", 0.15), ("too big     lr=0.40", 0.40)):
    px, py = x, y
    trail = []
    for _ in range(6):
        gx, gy = grad(px, py)
        px, py = px - lr*gx, py - lr*gy
        trail.append(g(px, py))
    print(f"   {name}: f after each step -> " + "  ".join(f"{v:7.3f}" for v in trail))
print("   Small: creeps. Good: converges. Too big: overshoots and grows -- the same")
print("   picture as a learning rate that is too high.")

print("\n=== with billions of inputs the picture is identical ===")
print("   the loss is f, the parameters are x, y, ... (8 billion of them), and the")
print("   gradient is 8 billion slopes. Backprop computes them all in one pass.")
