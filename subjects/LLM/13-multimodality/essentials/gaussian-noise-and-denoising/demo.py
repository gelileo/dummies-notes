#!/usr/bin/env python3
"""The normal distribution, adding noise on a schedule, and why denoising is regression.
Run: python3 demo.py"""
import numpy as np
rng = np.random.default_rng(0)

print("=== the normal (Gaussian) distribution: mean, std, the bell ===")
x = rng.normal(0, 1, 100000)
print(f"   100k draws from N(0,1): mean {x.mean():+.3f}  std {x.std():.3f}")
for k in (1, 2, 3):
    print(f"   within {k} std of the mean: {np.mean(np.abs(x) < k):.1%}   (the 68-95-99.7 rule)")
print("   scale by sigma and shift by mu: N(mu, sigma^2). sums of Gaussians are Gaussian.")

print("\n=== adding noise: x_noisy = x + sigma * eps,  eps ~ N(0,1) ===")
x0 = np.array([2.0, -1.0, 0.5])
for sig in (0.1, 0.5, 2.0):
    print(f"   sigma {sig:<4} -> {np.round(x0 + sig*rng.normal(size=3), 2)}   (signal {x0})")
print("   at sigma=2 the signal is gone; at 0.1 it is barely touched.")

print("\n=== a schedule: many small noising steps compose into one closed form ===")
STEPS = 50; betas = np.linspace(1e-3, 0.2, STEPS); alphas = 1 - betas; abar = np.cumprod(alphas)
print("   step t: x_t = sqrt(1 - beta_t) x_{t-1} + sqrt(beta_t) eps_t")
print("   all at once: x_t = sqrt(abar_t) x_0 + sqrt(1 - abar_t) eps,   abar_t = prod(1 - beta)")
print(f"   {'t':>4}{'abar_t':>9}{'signal weight':>15}{'noise weight':>14}")
for t in (0, 10, 25, 40, 49):
    print(f"   {t:>4}{abar[t]:>9.3f}{np.sqrt(abar[t]):>15.3f}{np.sqrt(1-abar[t]):>14.3f}")
print("   check: variance of x_t is abar*var(x0) + (1-abar)*1 -- for unit-variance data, always 1.")
x0s = rng.normal(size=100000)
for t in (10, 49):
    xt = np.sqrt(abar[t])*x0s + np.sqrt(1-abar[t])*rng.normal(size=100000)
    print(f"   t={t}: measured var(x_t) = {xt.var():.3f}")

print("\n=== denoising is regression ===")
print("   given x_t and t, predict eps. the loss is plain mean squared error: (eps_hat - eps)^2.")
print("   no adversary, no likelihood trick -- the same 'define a loss, take the gradient' as chapter 04.")
print("   the best possible predictor of eps from x_t is E[eps | x_t]; for a single data point x_0 it is")
eps = rng.normal(size=100000); t = 25
xt = np.sqrt(abar[t])*1.5 + np.sqrt(1-abar[t])*eps          # data is the single point 1.5
eps_hat = (xt - np.sqrt(abar[t])*1.5) / np.sqrt(1-abar[t])    # exact inversion
print(f"   exactly recoverable: MSE {np.mean((eps_hat-eps)**2):.2e}. with a spread of data it becomes an")
print("   average over the points that could have produced x_t -- which is what the network learns.")

print("\n=== sampling runs the schedule backwards ===")
print("   start at pure noise, subtract the predicted noise a little, add a little fresh noise, repeat")
print("   50-1000 times. each step is one forward pass of the denoiser: generation costs many passes,")
print("   which is why diffusion is slow and why distilled few-step samplers exist.")
