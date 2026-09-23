# Essential · Softmax and probability distributions

**Needed for:** attention weights, the causal mask, the model's output — three separate places in
[chapter 02](../../README.md) where raw scores become something that sums to 1.

## The problem it solves

You have a list of scores. They can be any size, positive or negative:

```
[2.0, 1.0, 0.1]        [-3.0, -1.0, -8.0]        [5.0, 1.0, 0.1]
```

You want to turn them into **weights**: all positive, adding up to 1, with bigger scores getting
more. A **probability distribution** is exactly that — a list of non-negative numbers summing to
1, saying how much of the total belongs to each option.

## Softmax, in two steps

```python
def softmax(scores):
    e = [exp(s) for s in scores]      # 1. make everything positive
    return [x / sum(e) for x in e]    # 2. divide by the total
```

```
[2.0, 1.0, 0.1]          -> ['0.659', '0.242', '0.099']   sums to 1.000
   [5.0, 1.0, 0.1]          -> ['0.975', '0.018', '0.007']   sums to 1.000
   [1.0, 1.0, 1.0]          -> ['0.333', '0.333', '0.333']   sums to 1.000
   [-3.0, -1.0, -8.0]       -> ['0.119', '0.880', '0.001']   sums to 1.000
```

**Why `exp`?** Two reasons, both load-bearing:

```
score   exp(score)
         -2        0.135
         -1        0.368
          0        1.000
          1        2.718
          2        7.389
          3       20.086
   Negative scores survive as small positive numbers - nothing is thrown away.
```

It turns *any* number into a positive one, so negative scores survive as small weights rather than
being clipped to zero — nothing is discarded. And it grows fast, so a score that is 2 higher gets
`e²≈7.4×` more weight. Gaps get amplified, which makes the result decisive without being brutal.

## Only differences matter

```
[1.0, 2.0, 3.0]          -> ['0.090', '0.245', '0.665']
   [101.0, 102.0, 103.0]    -> ['0.090', '0.245', '0.665']
   [-9.0, -8.0, -7.0]       -> ['0.090', '0.245', '0.665']
   Adding a constant to every score changes nothing. That is why subtracting
   the max is safe, and it is what stops exp() overflowing.
```

Adding the same constant to every score changes nothing. That is why real implementations subtract
the largest score first: it cannot change the answer, and it stops `exp` overflowing on large
inputs.

## Negative infinity gives you exactly zero

```
: this is how the causal mask works
```

`exp(-inf)` is `0`, so a masked position gets **exactly** zero weight and drops out of the sum.
This is how the causal mask works in chapter 02 — set the future to `-inf` *before* softmax and it
vanishes for free, with no special-casing anywhere.

## Dividing first: temperature

```
T=0.5   -> ['0.867', '0.117', '0.016']
   T=1.0   -> ['0.665', '0.245', '0.090']
   T=2.0   -> ['0.506', '0.307', '0.186']
   T=10.0  -> ['0.367', '0.332', '0.301']
   small T -> sharper (closer to picking the top one); large T -> flatter.
```

Dividing every score by `T` before softmax controls how decisive the result is. This is the
`temperature` knob on every model API — [chapter 10](../../../10-inference-and-decoding/) — and the
same mechanism explains why attention divides by `√d_head`, covered in
[averages and normalization](../averages-and-normalization/).

## The three places chapter 02 uses it

1. **Attention weights** — scores for each earlier token become a set of weights summing to 1, so
   each row of the attention matrix is "how I divide my attention".
2. **The causal mask** — `-inf` plus softmax equals exactly zero, no branching required.
3. **The model's output** — softmax over the logits gives the next-token distribution. That is
   literally what the model returns.

## Run it

```bash
python3 demo.py
```

## Terms

| Term | Meaning |
| --- | --- |
| **probability distribution** | Non-negative numbers summing to 1, splitting a whole into shares. |
| **softmax** | Exponentiate each score, divide by the total. Scores → distribution. |
| **`exp(x)` / `e^x`** | The exponential function. Always positive; grows fast; `exp(0)=1`, `exp(-inf)=0`. |
| **logit** | A raw score before softmax. Any size, any sign. |
| **temperature** | Divide scores by `T` before softmax. Small `T` sharpens, large `T` flattens. |
| **saturated** | A distribution where one entry has nearly all the weight and the rest are ~0. |
