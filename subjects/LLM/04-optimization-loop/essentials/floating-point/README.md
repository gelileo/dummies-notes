# Essential · Floating-point numbers, and why training uses bf16

**Needed for:** *"bf16 mixed precision with fp32 master weights"* in [chapter 04](../../README.md)
and the quantization discussion in [chapter 11](../../../11-efficiency/).

## A float is three bit-fields

A computer stores a decimal as **sign × mantissa × 2^exponent**, with a fixed budget of bits
split between the exponent and the mantissa:

```
   format    total  exponent  mantissa   largest value   gap at 1.0
   fp32         32         8        23         3.4e+38     1.19e-07
   fp16         16         5        10           65504     9.77e-04
   bf16         16         8         7         3.4e+38     7.81e-03
   exponent bits buy RANGE (how big/small). mantissa bits buy PRECISION (how fine).
```

The trade is exact: exponent bits buy **range** (how large and how small you can go), mantissa
bits buy **precision** (how finely you can distinguish nearby numbers). Sixteen bits are not
enough for both, so the two 16-bit formats make opposite choices.

## Precision

```
   1.0100     fp32 1.010000     fp16 1.009766     bf16 1.007812    
   1.0010     fp32 1.001000     fp16 1.000977     bf16 1.000000    
   1.0001     fp32 1.000100     fp16 1.000000     bf16 1.000000    
   bf16 cannot see 1.001: it rounds to 1.0. fp16 can. fp16 has more precision.
```

`bf16` cannot represent `1.001` — it rounds to `1.0`. `fp16` can. If you care about the third
decimal place, `fp16` is the better format.

## Range

```
   60000      fp16 60000        bf16 59904       
   65504      fp16 65504        bf16 65280       
   70000      fp16 inf          bf16 69632       
   1e+10      fp16 inf          bf16 9.99922e+09 
   3e+38      fp16 inf          bf16 2.99076e+38 
   fp16 dies at 65504 -> inf. bf16 reaches 3e38 like fp32. bf16 has more range.
```

`fp16` cannot represent anything above 65,504 — it overflows to `inf`, and one `inf` in a
gradient poisons everything downstream. `bf16` reaches 3×10³⁸, the same as `fp32`.

## Decimals are not exact, and errors accumulate

```
   0.1 + 0.2 == 0.3 ?  False    (0.1 + 0.2 = 0.30000000000000004441)
   add 0.1 ten thousand times: fp16 256.0   fp32 999.903   exact 1000
   errors accumulate. this is why the optimizer keeps a fp32 'master' copy of
   the weights and only uses 16-bit for the big matrix multiplies.
```

Adding `0.1` ten thousand times in `fp16` drifts to 999.5 — wrong in the units place. This is why
the optimizer keeps an **fp32 master copy** of every weight and applies updates to that; the
16-bit copies are used only for the big matrix multiplies, where speed matters and small rounding
is harmless.

## Why bf16 won

```
   gradients range across many orders of magnitude within one model.
   losing precision in the 3rd decimal is harmless; overflowing to inf is fatal.
   fp16 needs 'loss scaling' (multiply the loss by ~1000 so tiny gradients
   stay above fp16's floor, then divide back). bf16 does not.
```

Gradients in one model span many orders of magnitude at once. Losing precision in the third
decimal is survivable; overflowing to `inf` is not. So training chose range. `fp16` can be made
to work with **loss scaling** — multiply the loss by a large constant so tiny gradients stay above
its floor, then divide back — but `bf16` simply does not need it.

## Run it

```bash
python3 demo.py
```

## Terms

| Term | Meaning |
| --- | --- |
| **floating point** | Storing a number as sign × mantissa × 2^exponent with fixed bit budgets. |
| **mantissa / significand** | The bits holding the digits. More = finer precision. |
| **exponent** | The bits holding the scale. More = wider range. |
| **fp32** | 32-bit float: 8 exponent, 23 mantissa. The default; the "master" weights. |
| **fp16** | 16-bit: 5 exponent, 10 mantissa. Fine precision, tiny range (max 65,504). |
| **bf16** | 16-bit: 8 exponent, 7 mantissa. fp32's range, coarse precision. What training uses. |
| **overflow** | A value too large for the format → `inf`. Fatal in a gradient. |
| **mixed precision** | 16-bit for the heavy matrix multiplies, fp32 for the weights being updated. |
| **loss scaling** | Multiplying the loss so small gradients stay representable in fp16. Not needed with bf16. |
