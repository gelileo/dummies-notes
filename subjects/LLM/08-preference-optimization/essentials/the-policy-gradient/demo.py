#!/usr/bin/env python3
"""The policy-gradient identity, checked numerically. Run: python3 demo.py"""
import numpy as np
rng = np.random.default_rng(0)

R = 5
reward = np.array([1.0, 3.0, 0.5, 2.0, 4.0])
theta = np.array([0.2, -0.1, 0.0, 0.3, 0.1])           # logits: the policy's parameters
def pi(th): e = np.exp(th - th.max()); return e / e.sum()
def J(th): return pi(th) @ reward                    # objective: expected reward

print("=== the objective: expected reward under the policy ===")
print(f"   rewards  {reward}")
print(f"   policy   {np.round(pi(theta), 3)}")
print(f"   J(theta) = E_pi[reward] = {J(theta):.4f}")

print("\n=== the exact gradient, by finite differences ===")
h = 1e-6; exact = np.array([(J(theta + h*np.eye(R)[i]) - J(theta - h*np.eye(R)[i])) / (2*h) for i in range(R)])
print(f"   dJ/dtheta = {np.round(exact, 4)}")

print("\n=== the trick: grad E[r] = E[ r * grad log pi ] ===")
print("   the gradient of an expectation becomes an expectation of a gradient -- which")
print("   means it can be ESTIMATED FROM SAMPLES, without knowing pi in closed form.")
print("   for softmax logits, grad log pi(k) = onehot(k) - pi.")
p = pi(theta)
analytic = sum(p[k] * reward[k] * (np.eye(R)[k] - p) for k in range(R))
print(f"   sum_k pi(k) * r(k) * grad log pi(k) = {np.round(analytic, 4)}   <- matches")

print("\n=== estimating it from samples (this is REINFORCE) ===")
print(f"   {'samples':>8}{'estimate':>36}{'error':>8}")
for n in (4, 32, 256, 4096):
    idx = rng.choice(R, n, p=p)
    est = np.mean([reward[k] * (np.eye(R)[k] - p) for k in idx], axis=0)
    print(f"   {n:>8}{str(np.round(est, 3)):>36}{np.linalg.norm(est - exact):>8.3f}")
print("   unbiased, converging with more samples. in RLHF each 'sample' is a full response")
print("   the model generated and the reward model scored.")

print("\n=== with a baseline: same expectation, less noise ===")
b = p @ reward
for name, base in (("no baseline", 0.0), ("baseline = E[r]", b)):
    ests = [np.mean([(reward[k] - base) * (np.eye(R)[k] - p) for k in rng.choice(R, 16, p=p)], axis=0) for _ in range(1000)]
    ests = np.array(ests)
    print(f"   {name:<16} mean error {np.linalg.norm(ests.mean(0) - exact):.4f}   scatter {np.sqrt(((ests-ests.mean(0))**2).sum(1)).mean():.3f}")
print("   (reward - baseline) is the ADVANTAGE. it is why every RL method for LLMs -- PPO,")
print("   GRPO -- centres rewards before using them.")

print("\n=== one step of ascent ===")
lr = 0.5
new = theta + lr * exact
print(f"   J before {J(theta):.4f}   J after one step {J(new):.4f}   policy now {np.round(pi(new), 3)}")
print("   mass moved toward the high-reward responses. repeat, and the policy converges on r4.")
