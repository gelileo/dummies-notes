# Essential · Quantization arithmetic

**Needed for:** *"int8"*, *"int4 with group size 32"*, *"outliers"* in [chapter 11](../../README.md).
Floating-point formats themselves are owned by
[chapter 04](../../../04-optimization-loop/essentials/floating-point/).

## The recipe

```
   weights      [ 0.31 -0.12  0.05 -0.44  0.2   0.02 -0.27  0.09]
   int4: levels -7..7, scale = max|w|/7 = 0.0629
   integers     [ 5 -2  1 -7  3  0 -4  1]
   dequantised  [ 0.314 -0.126  0.063 -0.44   0.189  0.    -0.251  0.063]
   error        [ 0.004 -0.006  0.013 -0.    -0.011 -0.02   0.019 -0.027]   (max possible: scale/2 = 0.0314)
   storage: 8 x 4 bits + one 16-bit scale = 48 bits, vs 8 x 16 = 128 bits. 2.7x smaller.
```

Pick a **scale** so the largest weight maps to the largest integer, divide every weight by it,
round, store the integers and the one scale. To use them, multiply back. Eight 4-bit integers and
one 16-bit scale replace eight 16-bit floats.

## Where the error comes from

```
   int8:  255 levels, step 0.0035, max error 0.0017  (1% of a typical weight)
   int4:   15 levels, step 0.0629, max error 0.0314  (17% of a typical weight)
   int3:    7 levels, step 0.1467, max error 0.0733  (39% of a typical weight)
   int2:    3 levels, step 0.4400, max error 0.2200  (117% of a typical weight)
```

Rounding costs at most half a step, and the step is the scale — which is set by the **largest**
value. Halve the bits and you double the step. `int2` has four levels; almost every weight rounds
to one of two values.

## One outlier ruins everyone

```
   no outlier           step 0.0629   small weights become [-0.126  0.063  0.   ]  (were [-0.12  0.05  0.02])
   one weight = -3.5    step 0.5000   small weights become [-0.  0.  0.]  (were [-0.12  0.05  0.02])
   the outlier forces a coarse step and the small weights round to zero. real weight
   matrices have such outliers, which is the whole problem quantization methods solve.
```

Real weight matrices have rare large values. One of them stretches the shared scale, and every
ordinary weight in that row is now quantised coarsely — many round to zero. This, not the bit
count, is the actual problem quantization methods solve.

## The fix: scales per small group

```
    group size  rel. weight error  extra bits per weight
           256             0.1337                   0.06
           128             0.1214                   0.12
            64             0.1101                   0.25
            32             0.0988                   0.50
            16             0.0860                   1.00
   smaller groups: an outlier only hurts its own block, at the cost of storing more scales.
   group 32 is the common compromise (0.5 extra bits/weight). GPTQ and AWQ go further by
   choosing the rounding to minimise output error, not weight error.
```

Give each block of 32 or 64 weights its own scale and an outlier hurts only its own block. The
price is storing more scales — half a bit per weight at group 32 — which is why quantized model
files quote sizes like "4.5 bits per weight". GPTQ and AWQ go further: one chooses the rounding
to minimise *output* error rather than weight error; the other rescales outlier channels before
quantising.

## Run it

```bash
python3 demo.py
```

## Terms

| Term | Meaning |
| --- | --- |
| **quantization** | Representing weights with a small number of integer levels plus a scale. |
| **scale** | The float that maps integer levels back to weight values. Set by the largest value in its group. |
| **levels** | `2^bits` distinct values. int8: 256; int4: 16; int2: 4. |
| **step** | The gap between adjacent representable values. Rounding error ≤ half a step. |
| **outlier** | A rare large weight that stretches the scale for its group. |
| **group size** | How many weights share a scale. Smaller = more robust, more overhead. |
| **bits per weight** | Effective storage including scales. Group 32 at int4 ≈ 4.5 bpw. |
| **GPTQ / AWQ** | Methods that pick rounding or pre-scaling to minimise output error rather than weight error. |
