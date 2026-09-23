# Essential · Gaussian noise and denoising

**Needed for:** *"diffusion"*, *"noise schedule"*, *"predict the noise"* in [chapter 13](../../README.md).

## The normal distribution

```
   100k draws from N(0,1): mean -0.001  std 1.000
   within 1 std of the mean: 68.4%   (the 68-95-99.7 rule)
   within 2 std of the mean: 95.5%   (the 68-95-99.7 rule)
   within 3 std of the mean: 99.7%   (the 68-95-99.7 rule)
   scale by sigma and shift by mu: N(mu, sigma^2). sums of Gaussians are Gaussian.
```

The bell curve. Two numbers describe it — mean and standard deviation — and the 68–95–99.7 rule
says where the mass sits. Sums of Gaussians are Gaussian, which is the property everything below
relies on.

## Adding noise

```
   sigma 0.1  -> [ 2.12 -1.02  0.48]   (signal [ 2.  -1.   0.5])
   sigma 0.5  -> [ 1.73 -0.9  -0.72]   (signal [ 2.  -1.   0.5])
   sigma 2.0  -> [ 1.39 -1.17 -2.73]   (signal [ 2.  -1.   0.5])
   at sigma=2 the signal is gone; at 0.1 it is barely touched.
```

## A schedule of small steps composes into one formula

```
   step t: x_t = sqrt(1 - beta_t) x_{t-1} + sqrt(beta_t) eps_t
   all at once: x_t = sqrt(abar_t) x_0 + sqrt(1 - abar_t) eps,   abar_t = prod(1 - beta)
      t   abar_t  signal weight  noise weight
      0    0.999          0.999         0.032
     10    0.788          0.888         0.460
     25    0.248          0.498         0.867
     40    0.028          0.167         0.986
     49    0.005          0.067         0.998
   check: variance of x_t is abar*var(x0) + (1-abar)*1 -- for unit-variance data, always 1.
   t=10: measured var(x_t) = 1.004
   t=49: measured var(x_t) = 1.004
```

Because sums of Gaussians are Gaussian, `T` small noising steps collapse into a single closed form:
`x_t = √ᾱ_t · x₀ + √(1−ᾱ_t) · ε`. You can jump to any noise level in one line, which is what makes
training cheap — sample a random `t`, noise once, done. The variance check confirms the two
coefficients are chosen so the total variance stays at 1.

## Denoising is regression

```
   given x_t and t, predict eps. the loss is plain mean squared error: (eps_hat - eps)^2.
   no adversary, no likelihood trick -- the same 'define a loss, take the gradient' as chapter 04.
   the best possible predictor of eps from x_t is E[eps | x_t]; for a single data point x_0 it is
   exactly recoverable: MSE 1.01e-32. with a spread of data it becomes an
   average over the points that could have produced x_t -- which is what the network learns.
```

The network's job: given a noisy `x_t` and the step `t`, predict the noise `ε` that was added. The
loss is mean squared error. No adversary, no likelihood trick — the same "define a loss, take its
gradient" as [chapter 04](../../../04-optimization-loop/). With a whole dataset the target becomes
the *average* noise consistent with `x_t`, which is what the network learns.

## Sampling

```
   start at pure noise, subtract the predicted noise a little, add a little fresh noise, repeat
   50-1000 times. each step is one forward pass of the denoiser: generation costs many passes,
   which is why diffusion is slow and why distilled few-step samplers exist.
```

## Run it

```bash
python3 demo.py
```

## Terms

| Term | Meaning |
| --- | --- |
| **normal / Gaussian distribution** | The bell curve, `N(μ, σ²)`. Sums of Gaussians are Gaussian. |
| **standard normal** | `N(0, 1)`. What `ε` is drawn from. |
| **noise schedule** `β_t` | How much noise each forward step adds. |
| **ᾱ_t (alpha-bar)** | Product of `(1 − β)` up to step `t`: how much signal survives. |
| **forward process** | Adding noise on the schedule until the data is pure noise. |
| **reverse process / sampling** | Starting from noise and denoising step by step. |
| **ε-prediction** | Training the network to output the noise, by MSE. The standard objective. |
| **classifier-free guidance** | Amplifying the difference between conditional and unconditional predictions: how hard to follow the caption. |
