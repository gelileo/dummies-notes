# Essential · Sampling from a distribution

**Needed for:** *"pick a token"*, temperature, top-k and top-p in [chapter 10](../../README.md).

## How one token is actually drawn

The model hands you probabilities. Turning them into a single choice takes one random number:

```
   probabilities [0.5  0.3  0.15 0.05]
   cumulative    [0.5  0.8  0.95 1.  ]
   draw u uniformly in [0,1); the token is the first index whose cumulative sum exceeds u:
      u = 0.12 -> token 0
      u = 0.61 -> token 1
      u = 0.83 -> token 2
      u = 0.97 -> token 3
   100,000 draws: frequencies [0.501 0.301 0.148 0.05 ]   (match p)
   that is all 'sampling' is: one uniform random number and a lookup.
```

Cumulative sums turn the probabilities into consecutive intervals on `[0, 1)`; a uniform random
number lands in exactly one of them. That is the whole of "sampling". Every randomness in a
model's output traces back to that one `u`.

## Temperature

```
   logits [ 3.  2.  1.  0. -1.]
        T                               probabilities   p(top)
      0.2             [0.993 0.007 0.    0.    0.   ]    0.993
      0.5             [0.865 0.117 0.016 0.002 0.   ]    0.865
      1.0             [0.636 0.234 0.086 0.032 0.012]    0.636
      2.0             [0.429 0.26  0.158 0.096 0.058]    0.429
      5.0             [0.287 0.235 0.192 0.157 0.129]    0.287
   T -> 0 approaches argmax (greedy). T -> inf approaches uniform. it rescales the gaps
   between logits, so it changes confidence, not ranking.
```

Divide the logits by `T` *before* softmax
([softmax](../../../02-transformer-forward-pass/essentials/softmax-and-probability/)). Small `T`
widens the gaps and approaches greedy; large `T` flattens toward uniform. Ranking never changes —
only confidence.

## Top-k

```
   full      [0.636 0.234 0.086 0.032 0.012]
   top-2     [0.731 0.269 0.    0.    0.   ]   (three tokens can never be chosen)
```

Keep the `k` most probable tokens, zero the rest, renormalise. The tail can never be chosen.

## Top-p (nucleus)

```
   top-p=0.5   keeps 1 tokens -> [1. 0. 0. 0. 0.]
   top-p=0.9   keeps 3 tokens -> [0.665 0.245 0.09  0.    0.   ]
   top-p=0.99  keeps 5 tokens -> [0.636 0.234 0.086 0.032 0.012]
   top-k fixes the COUNT; top-p fixes the MASS. when the model is confident top-p keeps
   few tokens; when it is unsure it keeps many. that adaptivity is why top-p is the default.
```

Keep the smallest set of tokens whose probabilities add up to `p`. When the model is confident that
set is tiny; when it is unsure the set is large. Top-k fixes a *count*; top-p fixes a *mass* — and
that adaptivity is why top-p is usually the default.

## Order matters

```
   1. logits / T   2. softmax   3. truncate (top-k / top-p)   4. renormalise   5. draw
   temperature changes which tokens survive truncation; do it first.
```

## Run it

```bash
python3 demo.py
```

## Terms

| Term | Meaning |
| --- | --- |
| **sampling** | Drawing one outcome according to a distribution: one uniform number, one lookup. |
| **cumulative distribution** | Running sum of probabilities. Turns a distribution into intervals. |
| **greedy / argmax** | Always take the most probable token. `T → 0`. Deterministic, prone to loops. |
| **temperature** `T` | Divide logits by `T` before softmax. Reshapes confidence, not ranking. |
| **top-k** | Keep the `k` most probable tokens, renormalise. |
| **top-p / nucleus** | Keep the smallest set with total probability ≥ `p`, renormalise. |
| **min-p** | Keep tokens with probability at least `p × p(top)`. Another adaptive truncation. |
| **renormalise** | Rescale surviving probabilities to sum to 1. |
