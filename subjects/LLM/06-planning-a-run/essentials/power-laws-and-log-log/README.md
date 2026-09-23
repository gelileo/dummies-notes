# Essential · Power laws and log-log plots

**Needed for:** *"loss falls as a power law"*, *"straight on log-log axes"*, and *"fit the
ladder, extrapolate"* in [chapter 06](../../README.md). Also the general maths behind
[Zipf's law](../../../05-data/essentials/zipf-and-the-long-tail/).

## A power law: `y = a · xᵇ`

```
   y = 5.0 * x^-0.5
          x         y  x doubles ->  y changes by
          1     5.000
          2     3.536                       0.707x
          4     2.500                       0.707x
          8     1.768                       0.707x
         16     1.250                       0.707x
         32     0.884                       0.707x
   every doubling of x multiplies y by the SAME factor, 2^-0.5 = 0.707.
   that constant ratio is the signature of a power law.
```

The defining property: **every doubling of `x` multiplies `y` by the same factor**, `2ᵇ`. Not the
same *amount* — the same *ratio*. That is what makes it scale-free: the relationship looks the
same at 10 as at 10 million.

## Take logs and it is a straight line

```
  log y = log a + b · log x
```

A straight line, slope `b`, intercept `log a`:

```
   log y = log a + b * log x       <- slope b, intercept log a
     log10 x   log10 y
       0.000     0.699
       0.301     0.548
       0.602     0.398
       0.903     0.247
       1.204     0.097
       1.505    -0.054
   fitted slope -0.500 (true b = -0.5), intercept 0.699 (true log10 a = 0.699)
```

Fitting a power law is therefore ordinary linear regression on the logarithms. `numpy.polyfit`
on `log10 x` and `log10 y` returns the exponent directly.

## Not everything that falls is a power law

```
     log10 x  power law  exponential
       0.000      0.699        0.602
       0.301      0.548        0.505
       0.602      0.398        0.311
       0.903      0.247       -0.076
       1.204      0.097       -0.852
       1.505     -0.054       -2.402
   the power-law column drops by a constant per row; the exponential accelerates.
   'straight on log-log' is a real test, and scaling-law papers pass it.
```

An exponential curves on log-log axes; a power law does not. "Straight on log-log" is a real,
falsifiable test, and it is the one scaling-law papers apply. It is also easy to pass by eye and
fail on the residuals — chapter 06 shows a case where a constant you forgot to subtract turns a
slope of −0.34 into −0.24.

## Reading a slope

```
   slope  -0.05: 10x more x -> y multiplied by 0.891  (  11% reduction)
   slope   -0.1: 10x more x -> y multiplied by 0.794  (  21% reduction)
   slope   -0.3: 10x more x -> y multiplied by 0.501  (  50% reduction)
   slope   -0.5: 10x more x -> y multiplied by 0.316  (  68% reduction)
   language-model losses have slopes near -0.05 to -0.1 in compute: a 10x costs
   buys ~10-20%. small per step, but there have been many 10x steps.
```

Language-model loss has an exponent near −0.05 to −0.1 in compute. Each 10× buys 10–20%. That
sounds meagre until you count how many 10× steps the field has taken.

## Extrapolation

```
   fit on x in [1, 100], predict x=1e+03: 0.1575   true 0.1581
   fit on x in [1, 100], predict x=1e+04: 0.0496   true 0.0500
   two orders of magnitude beyond the data, within a percent. that is why labs
   trust ladders of small runs -- and why a floor (irreducible loss) must be
   subtracted first, or the line bends.
```

Two orders of magnitude past the data, within a percent — *if* the law holds and *if* every floor
was subtracted first. That "if" is the entire risk in a $100M training run, and it is why the
ladder of small runs is fit carefully rather than eyeballed.

## Run it

```bash
python3 demo.py
```

## Terms

| Term | Meaning |
| --- | --- |
| **power law** | `y = a · xᵇ`. Every doubling of `x` multiplies `y` by `2ᵇ`. |
| **exponent** `b` | The slope on log-log axes. Negative for loss. |
| **log-log plot** | Both axes logarithmic. Power laws appear as straight lines. |
| **scale-free** | Looks the same at every magnitude — the defining property of a power law. |
| **exponential** | `y = a · cˣ`. Curves on log-log; straight on semi-log. Not a power law. |
| **residuals** | Data minus fit. The honest test of straightness. |
| **extrapolation** | Reading the fitted line beyond the data. Powerful when the law holds. |
| **floor / offset** | A constant added to a power law (like irreducible loss). Bends the line unless subtracted. |
