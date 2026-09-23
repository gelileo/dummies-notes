#!/usr/bin/env python3
"""The sigmoid, and turning 'A is better than B' into a trainable model (Bradley-Terry).
Run: python3 demo.py"""
import numpy as np
rng = np.random.default_rng(0)
sig = lambda z: 1 / (1 + np.exp(-z))

print("=== sigmoid squashes any number into (0, 1) ===")
for z in (-6, -2, -1, 0, 1, 2, 6):
    print(f"   sigmoid({z:>3}) = {sig(z):.4f}")
print("   0 in -> 0.5. symmetric: sigmoid(-z) = 1 - sigmoid(z). smooth, so it has a gradient.")

print("\n=== Bradley-Terry: P(A beats B) = sigmoid(score_A - score_B) ===")
scores = {"A": 2.0, "B": 1.0, "C": -0.5}
for x, y in (("A", "B"), ("A", "C"), ("B", "C"), ("B", "A")):
    print(f"   P({x} beats {y}) = sigmoid({scores[x]} - {scores[y]}) = {sig(scores[x]-scores[y]):.3f}")
print("   only DIFFERENCES matter: add 100 to every score and nothing changes. a scale with")
print("   no fixed zero -- which is fine, because we only ever compare.")

print("\n=== learning scores from comparisons ===")
true = np.array([1.0, 2.0, 3.0, 4.5, 5.0])
pairs = []
for _ in range(400):
    i, j = rng.choice(5, 2, replace=False)
    win = rng.random() < sig(true[i] - true[j])
    pairs.append((i, j) if win else (j, i))
s = np.zeros(5); lr = 0.1
for step in range(300):
    g = np.zeros(5)
    for c, r in pairs:
        p_correct = sig(s[c] - s[r])
        g[c] += (1 - p_correct); g[r] -= (1 - p_correct)     # gradient of log sigmoid(s_c - s_r)
    s += lr * g / len(pairs)
s -= s.mean(); t = true - true.mean()
print(f"   {'item':>6}{'true (centred)':>16}{'learned (centred)':>19}")
for i in range(5): print(f"   {i:>6}{t[i]:>16.2f}{s[i]:>19.2f}")
print("   from 400 'which is better?' answers, the scores come back in the right order and")
print("   roughly the right spacing. this IS a reward model: score = w . features(response).")

print("\n=== the loss: -log sigmoid(chosen - rejected) ===")
for d in (-2, 0, 1, 3):
    print(f"   chosen - rejected = {d:>3}:  loss = {-np.log(sig(d)):.3f}")
print("   zero when the chosen one is far ahead; grows when the model gets the pair wrong.")
print("   DPO uses the same loss with 'score' replaced by beta * log(pi/pi_ref).")
