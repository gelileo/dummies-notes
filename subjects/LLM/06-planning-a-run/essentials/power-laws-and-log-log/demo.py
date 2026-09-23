#!/usr/bin/env python3
"""Power laws, log-log plots, and reading a slope. Run: python3 demo.py"""
import numpy as np

print("=== a power law: y = a * x^b ===")
a, b = 5.0, -0.5
print(f"   y = {a} * x^{b}")
print(f"   {'x':>8}{'y':>10}{'x doubles ->':>14}{'y changes by':>14}")
prev = None
for x in (1, 2, 4, 8, 16, 32):
    y = a * x**b
    print(f"   {x:>8}{y:>10.3f}" + (f"{'':>14}{y/prev:>14.3f}x" if prev else ""))
    prev = y
print(f"   every doubling of x multiplies y by the SAME factor, 2^{b} = {2**b:.3f}.")
print("   that constant ratio is the signature of a power law.")

print("\n=== take logs and it becomes a straight line ===")
print("   log y = log a + b * log x       <- slope b, intercept log a")
xs = np.array([1, 2, 4, 8, 16, 32], float); ys = a * xs**b
print(f"   {'log10 x':>9}{'log10 y':>10}")
for x, y in zip(xs, ys): print(f"   {np.log10(x):>9.3f}{np.log10(y):>10.3f}")
slope, intercept = np.polyfit(np.log10(xs), np.log10(ys), 1)
print(f"   fitted slope {slope:.3f} (true b = {b}), intercept {intercept:.3f} (true log10 a = {np.log10(a):.3f})")

print("\n=== an exponential is NOT a power law -- it curves on log-log ===")
ys_exp = 5.0 * 0.8**xs
print(f"   {'log10 x':>9}{'power law':>11}{'exponential':>13}")
for x, y1, y2 in zip(xs, ys, ys_exp): print(f"   {np.log10(x):>9.3f}{np.log10(y1):>11.3f}{np.log10(y2):>13.3f}")
print("   the power-law column drops by a constant per row; the exponential accelerates.")
print("   'straight on log-log' is a real test, and scaling-law papers pass it.")

print("\n=== reading a slope: how much do you gain per 10x? ===")
for b_ in (-0.05, -0.1, -0.3, -0.5):
    print(f"   slope {b_:>6}: 10x more x -> y multiplied by {10**b_:.3f}  ({(1-10**b_)*100:4.0f}% reduction)")
print("   language-model losses have slopes near -0.05 to -0.1 in compute: a 10x costs")
print("   buys ~10-20%. small per step, but there have been many 10x steps.")

print("\n=== extrapolation: powerful, and only as good as the straightness ===")
rng = np.random.default_rng(1)
xs_fit = np.logspace(0, 2, 5); ys_fit = 5 * xs_fit**-0.5 * (1 + rng.normal(0, 0.02, 5))
m, c = np.polyfit(np.log10(xs_fit), np.log10(ys_fit), 1)
for x_new in (1e3, 1e4):
    print(f"   fit on x in [1, 100], predict x={x_new:.0e}: {10**(m*np.log10(x_new)+c):.4f}   true {5*x_new**-0.5:.4f}")
print("   two orders of magnitude beyond the data, within a percent. that is why labs")
print("   trust ladders of small runs -- and why a floor (irreducible loss) must be")
print("   subtracted first, or the line bends.")
