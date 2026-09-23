# Essential · Logarithms, and why a loss is in bits

**Needed for:** every `-log p` in [chapter 03](../../README.md) — the loss, perplexity, and the
sentence *"loss is the number of bits the model needs to encode the text"*.

## A log asks "what power?"

```
   log2(    1) =    0    because 2^0 = 1
   log2(    2) =    1    because 2^1 = 2
   log2(    4) =    2    because 2^2 = 4
   log2(    8) =    3    because 2^3 = 8
   log2( 1024) =   10    because 2^10 = 1024
   ln(e)  = 1,   ln(1) = 0,   log2(1) = 0
```

`log2(8) = 3` because `2³ = 8`. That is the entire definition. `ln` is the same question with
base *e* ≈ 2.718 instead of 2, and it is the one papers use.

## The one rule everything hinges on

```
   log(0.3*0.02) = -5.1160
   log(0.3) + log(0.02) = -5.1160
   multiplication becomes addition. That is the only reason logs appear.
```

**Multiplication becomes addition.** Every appearance of a log in this curriculum comes from
wanting to add things that would otherwise have to be multiplied.

## Why you cannot avoid it

A sequence's probability is a *product* of per-token probabilities
([probability of a sequence](../probability-of-a-sequence/)). Products of small numbers vanish:

```
    10 tokens at p=0.05:  product = 9.766e-14    sum of logs =     -30.0
    50 tokens at p=0.05:  product = 8.882e-66    sum of logs =    -149.8
   100 tokens at p=0.05:  product = 7.889e-131    sum of logs =    -299.6
   200 tokens at p=0.05:  product = 6.223e-261    sum of logs =    -599.1
   300 tokens at p=0.05:  product = 0.000e+00    sum of logs =    -898.7
   400 tokens at p=0.05:  product = 0.000e+00    sum of logs =   -1198.3
   By 300 tokens the product has underflowed to exactly 0.0 and the
   information is gone. The sum of logs is a perfectly ordinary number.
```

By 300 tokens the product is exactly `0.0` in floating point and the information is gone. The
sum of logs is a perfectly ordinary number you can average, compare and take gradients of. That
is not a convenience — it is the only way the computation can be done at all.

## `-log p` is surprise

```
   p = 1.0     -ln p = -0.000 nats   -log2 p = -0.000 bits
   p = 0.5     -ln p =  0.693 nats   -log2 p =  1.000 bits
   p = 0.25    -ln p =  1.386 nats   -log2 p =  2.000 bits
   p = 0.1     -ln p =  2.303 nats   -log2 p =  3.322 bits
   p = 0.01    -ln p =  4.605 nats   -log2 p =  6.644 bits
   p = 0.001   -ln p =  6.908 nats   -log2 p =  9.966 bits
   A certain event (p=1) costs 0. Halving p adds exactly 1 bit, every time.
```

A certain event costs nothing. Every halving of `p` adds exactly one bit. An event at
`p = 0.001` is worth about 10 bits — ten yes/no questions' worth of surprise.

## Bits are yes/no questions

```
   one of    2 equally likely options -> log2(2) =    1 questions to pin it down
   one of    4 equally likely options -> log2(4) =    2 questions to pin it down
   one of    8 equally likely options -> log2(8) =    3 questions to pin it down
   one of   16 equally likely options -> log2(16) =    4 questions to pin it down
   one of 1024 equally likely options -> log2(1024) =   10 questions to pin it down
```

Which is why a model with a loss of 1.78 bits per token *is* a compressor that stores text at
1.78 bits per token: each token needs, on average, 1.78 binary decisions to pin down given the
model's prediction. Predicting and compressing are the same act.

## Nats versus bits

```
   1.232 nats = 1.777 bits     (divide by ln 2 = 0.6931)
   1.232 nats -> perplexity exp(1.232) = 3.43
   Papers quote loss in nats (natural log), compression people in bits.
```

Divide nats by `ln 2 ≈ 0.693` to get bits. `exp(nats)` gives perplexity. All three describe one
quantity.

## Run it

```bash
python3 demo.py
```

## Terms

| Term | Meaning |
| --- | --- |
| **logarithm** | The inverse of exponentiation: `log_b(x)` is the power you raise *b* to, to get *x*. |
| **`ln`** | Natural log, base *e* ≈ 2.718. The default in ML papers. |
| **`log2`** | Log base 2. Counts bits. |
| **nat** | The unit of `-ln p`. |
| **bit** | The unit of `-log2 p`; one yes/no question. `1 nat ≈ 1.443 bits`. |
| **surprise** | `-log p`: zero for certainty, unbounded as `p → 0`. |
| **underflow** | A number too small for floating point, rounded to exactly 0. Products of probabilities do this. |
