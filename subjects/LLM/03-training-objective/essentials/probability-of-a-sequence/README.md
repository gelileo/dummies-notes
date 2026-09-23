# Essential · The probability of a sequence

**Needed for:** *"predict the next token given everything before it"* in
[chapter 03](../../README.md) — why the model works one token at a time, and why the loss is
a sum.

## Conditional probability

`p(B | A)` reads *"the probability of B, given that A happened"*. The same event can have very
different probabilities under different conditions:

```
   p(cat | the) = 0.5      p(cat | a) = 0.3
   Same word, different probability, because the context differs.
```

That vertical bar is the whole of language modelling. Every prediction is *given the context*.

## The chain rule

Any sequence's probability can be written as a product of one-step conditionals, each
conditioned on **everything** before it:

```
   p(the cat sat)
     = p(the) * p(cat | the) * p(sat | the cat)
     = 0.6 * 0.5 * 0.8
     = 0.240
   Every step conditions on EVERYTHING before it. Nothing is assumed independent.
```

This is exact — not an approximation. And it is why a language model only ever needs to answer
one question: *what comes next?* Answer it at every position and you have the probability of the
whole text.

## This is what the model computes

```
   forward pass at position t returns p(token_t | tokens_<t) -- one factor.
   the loss adds up -log of each factor (see logarithms-and-bits):
   p(the)             = 0.6    -> -log = 0.511
   p(cat|the)         = 0.5    -> -log = 0.693
   p(sat|the cat)     = 0.8    -> -log = 0.223
   sum = 1.427 = -log p(sequence) = -log(0.240) = 1.427  (same thing)
```

The forward pass at position *t* returns one factor of the chain rule. The loss is the sum of
`-log` of each factor — which, by the [log rule](../logarithms-and-bits/), is `-log` of the
entire sequence's probability. Minimising the loss *is* maximising the probability the model
assigns to the real text.

## A language model is a distribution over all texts

```
   sum over all 8 possible three-word sequences = 1.000
   Because every conditional sums to 1, the product does too. A language
   model is a probability distribution over ALL possible texts.
```

Because every conditional sums to 1, every product does too. The model does not just score the
text it saw — it implicitly assigns a probability to *every* possible string. Sampling from it
([chapter 10](../../../10-inference-and-decoding/)) is walking down one branch of that tree.

## Independence — the case that does not hold

```
   if p(cat | the) == p(cat | a) == p(cat), the words are independent and
   the chain rule collapses to p(w1)*p(w2)*p(w3) -- a 'bag of words'.
   Real language is nothing like that, which is the whole point of context.
```

If context made no difference the whole apparatus would be pointless. Language is the opposite
extreme, which is why the context window matters so much.

## Run it

```bash
python3 demo.py
```

## Terms

| Term | Meaning |
| --- | --- |
| **conditional probability** `p(B \| A)` | Probability of B given that A is known to have happened. |
| **joint probability** | Probability of several things all happening: `p(A, B, C)`. |
| **chain rule (probability)** | `p(A,B,C) = p(A) · p(B\|A) · p(C\|A,B)`. Exact for any sequence. |
| **factor** | One term in that product. The forward pass computes one factor. |
| **autoregressive** | Generating a sequence by repeatedly computing the next factor. |
| **independent** | `p(B\|A) = p(B)`: context does not matter. Language is not like this. |
| **likelihood** | The probability a model assigns to the observed data. Training maximises it. |
