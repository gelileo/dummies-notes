# Essential · Geometric series and expected tries

**Needed for:** *"tokens per big-model pass"* in [chapter 10](../../README.md)'s speculative
decoding, and *"samples until one passes"* in [chapter 09](../../../09-reasoning-training/).

## The series

```
   q=0.5: partial sums [1.    1.5   1.75  1.969 1.999 2.   ]   limit 1/(1-q) = 2.000
   q=0.9: partial sums [1.    1.9   2.71  4.686 6.862 9.954]   limit 1/(1-q) = 10.000
   each term is the last times q. the sum of the first n+1 terms is (1 - q^(n+1)) / (1 - q),
   and it converges to 1/(1-q) when q < 1.
```

Each term is the previous one times `q`. The first `n+1` terms sum to `(1 − qⁿ⁺¹)/(1 − q)`, and if
`q < 1` the infinite sum is `1/(1 − q)`.

## Speculative decoding's payoff

```
   a draft model proposes k tokens; the big model checks them in order and accepts each
   with probability q, stopping at the first rejection (and supplying its own token there).
   accepted count = 1 + q + q^2 + ... + q^k in expectation  -- a geometric series.
        q     k=1     k=2     k=4     k=8    k=16
     0.50    1.50    1.75    1.94    2.00    2.00
     0.70    1.70    2.19    2.77    3.20    3.33
     0.90    1.90    2.71    4.10    6.13    8.33
     0.95    1.95    2.85    4.52    7.40   11.64
   tokens per expensive pass. at q=0.9 drafting 8 gives 6.5 -- but drafting 16 gives only
   8.1, and the draft itself costs something: diminishing returns set the best k.
```

A cheap draft model proposes `k` tokens; the expensive model checks them in one pass, accepting
each with probability `q` and stopping at the first rejection (where it supplies its own token).
The expected number of tokens produced per expensive pass is a geometric sum. At `q = 0.9`,
drafting 8 yields 6.5 tokens per pass — but 16 yields only 8.1, and the draft costs something too.
Diminishing returns set the best `k`.

## Checked by simulation

```
   q=0.9, k=5: simulated mean 4.700   formula 4.686
```

## Expected tries until a success

```
   success probability 0.5  : expected tries 1/p =    2.0   simulated    2.0
   success probability 0.1  : expected tries 1/p =   10.0   simulated    9.9
   success probability 0.01 : expected tries 1/p =  100.0   simulated  100.1
   'how many samples until one passes the verifier' is this number (chapter 09).
```

The same series in disguise: with success probability `p` per try, you expect `1/p` tries. "How
many samples until the verifier accepts one" is this number, and it is why best-of-n works at all
for tasks the model rarely gets right.

## Run it

```bash
python3 demo.py
```

## Terms

| Term | Meaning |
| --- | --- |
| **geometric series** | `1 + q + q² + …`. Each term is the last times `q`. |
| **partial sum** | `(1 − qⁿ⁺¹)/(1 − q)`: the first `n+1` terms. |
| **limit** | `1/(1 − q)` for `q < 1`. |
| **acceptance rate** `q` | Probability the big model agrees with one drafted token. |
| **speculative decoding** | Draft `k` tokens cheaply, verify in one expensive pass. Same output distribution, fewer passes. |
| **expected tries** | `1/p` for success probability `p`. |
