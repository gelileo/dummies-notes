# Essential · Standard error and confidence intervals

**Needed for:** *"a 2-point gap on 200 questions is noise"*, *"± 2 standard errors"* in
[chapter 15](../../README.md), and every benchmark number you will ever read.

## An accuracy is a proportion, and proportions have a known spread

```
   standard error = sqrt( p (1-p) / N )
         N  SE (formula)  SE (simulated)      95% interval
        50        0.0648          0.0651    0.570 .. 0.830
       100        0.0458          0.0451    0.608 .. 0.792
       200        0.0324          0.0327    0.635 .. 0.765
       500        0.0205          0.0201    0.659 .. 0.741
      1000        0.0145          0.0144    0.671 .. 0.729
      5000        0.0065          0.0065    0.687 .. 0.713
     10000        0.0046          0.0046    0.691 .. 0.709
   the interval is roughly +/- 2 SE. quadrupling N halves the SE -- diminishing returns.
```

Score a model on `N` questions and you get a proportion. Do it again on `N` fresh questions of the
same kind and you get a different proportion. The **standard error** `√(p(1−p)/N)` is how far
those repeated measurements typically land from the truth, and the formula matches simulation to
three decimals. A rough **95% interval** is the observed score ± 2 standard errors: ± 6 points on
200 questions, ± 1 on 10,000.

## How many questions to trust a difference?

```
   to distinguish a 2-point gap you need the SE of the DIFFERENCE well below 0.02:
   N=   200: SE of (acc_a - acc_b) = 0.0458   gap is ~0.4 SE
   N=  1000: SE of (acc_a - acc_b) = 0.0205   gap is ~1.0 SE
   N=  5000: SE of (acc_a - acc_b) = 0.0092   gap is ~2.2 SE
   N= 20000: SE of (acc_a - acc_b) = 0.0046   gap is ~4.4 SE
   a 2-point gap on 200 questions is under one standard error. on 5,000 it is about 3.
```

Comparing two models on independent questions adds their variances. A 2-point gap on 200
questions is under one standard error — indistinguishable from noise. It takes about 5,000 to
make that gap three standard errors. ([Paired comparison](../../README.md) on the same questions
does far better.)

## Where the noise is worst

```
   p=0.5   N=500: SE 0.0224
   p=0.7   N=500: SE 0.0205
   p=0.9   N=500: SE 0.0134
   p=0.98  N=500: SE 0.0063
   a saturated benchmark (everyone at 97%) has tiny SE but also tiny gaps -- it stops discriminating.
```

## What "95%" means

```
   of 5000 experiments at N=200, the interval [obs +/- 2 SE] contained the true p in 95.5%
   'the true value is in here 95% of the time' -- not 'there is a 95% chance it is here'.
```

*The procedure* catches the true value 95% of the time. It is a statement about the interval's
reliability, not a probability that the truth is inside this particular one.

## Run it

```bash
python3 demo.py
```

## Terms

| Term | Meaning |
| --- | --- |
| **proportion** | Successes ÷ trials. An accuracy is one. |
| **standard error (SE)** | Typical distance of a measurement from the truth: `√(p(1−p)/N)` for a proportion. |
| **confidence interval** | `observed ± 2·SE` catches the truth ~95% of the time. |
| **sampling noise** | The variation between repeated measurements on different questions. |
| **statistically distinguishable** | A gap of several standard errors. Two is the usual bar. |
| **saturation** | A benchmark where everyone scores near 100%: small SE, but no room to differ. |
