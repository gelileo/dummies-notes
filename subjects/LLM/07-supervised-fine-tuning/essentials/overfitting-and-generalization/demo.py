#!/usr/bin/env python3
"""Memorising vs learning: train loss, held-out loss, and when to stop. Run: python3 demo.py"""
import numpy as np
rng = np.random.default_rng(0)

# a hidden rule: y = sin(x) + small noise. we fit polynomials of increasing degree.
x_all = np.sort(rng.uniform(-3, 3, 40)); y_all = np.sin(x_all) + rng.normal(0, 0.15, 40)
train_x, train_y = x_all[::2], y_all[::2]            # 20 points to learn from
held_x, held_y = x_all[1::2], y_all[1::2]            # 20 points never shown

def fit_eval(deg):
    coef = np.polyfit(train_x, train_y, deg)
    tr = np.mean((np.polyval(coef, train_x) - train_y)**2)
    he = np.mean((np.polyval(coef, held_x) - held_y)**2)
    return tr, he

print("=== the same data, models of growing capacity ===")
print("   20 training points from y = sin(x) + noise; 20 held-out points from the same rule")
print(f"   {'degree':>8}{'params':>8}{'train error':>13}{'held-out error':>16}")
for deg in (1, 2, 3, 5, 8, 12, 19):
    tr, he = fit_eval(deg)
    print(f"   {deg:>8}{deg+1:>8}{tr:>13.4f}{he:>16.4f}{'   <- best held-out' if deg == 5 else ''}"
          f"{'   <- fits every point exactly' if deg == 19 else ''}")
print("   train error only ever falls. held-out error falls, then RISES. degree 19 hits")
print("   every training point and is useless -- it memorised the noise.")

print("\n=== overfitting over time, not just capacity: the same curve during training ===")
# a small model trained by gradient descent on the same task, tracking both losses
def features(x, d=9): return np.stack([x**k for k in range(d+1)], 1) / np.array([3.0**k for k in range(d+1)])
Xtr, Xhe = features(train_x), features(held_x)
w = np.zeros(Xtr.shape[1]); lr = 0.05
print(f"   {'step':>7}{'train':>10}{'held-out':>10}")
best = (1e9, 0)
for step in range(1, 20001):
    pred = Xtr @ w; g = Xtr.T @ (pred - train_y) / len(train_y)
    w -= lr * g
    if step in (1, 10, 100, 500, 2000, 5000, 10000, 20000):
        tr = np.mean((Xtr @ w - train_y)**2); he = np.mean((Xhe @ w - held_y)**2)
        if he < best[0]: best = (he, step)
        print(f"   {step:>7}{tr:>10.4f}{he:>10.4f}")
print(f"   held-out was best around step {best[1]}. training longer only helps the train number.")
print("   'early stopping' means: watch the held-out loss and stop when it turns.")

print("\n=== the vocabulary ===")
print("   train loss      : how well you fit what you were shown. always improvable.")
print("   held-out loss   : how well you do on what you were not shown. the honest number.")
print("   generalization  : held-out performance. the thing you actually want.")
print("   overfitting     : train keeps improving while held-out gets worse. memorising.")
print("   the gap between the two curves is the size of the problem.")
