# Essential · Entropy, cross-entropy, and why the loss has that name

**Needed for:** *"cross-entropy loss"* and *"the irreducible loss is the entropy of language"* in
[chapter 03](../../README.md).

## Entropy: the average surprise of a source

Take a distribution. For each outcome, its surprise is `-log2 p` ([logarithms](../logarithms-and-bits/)).
**Entropy** is the average surprise, weighted by how often each outcome occurs:

```
   fair coin            H = 1.000 bits
   biased coin 90/10    H = 0.469 bits
   certain              H = -0.000 bits
   fair 6-sided die     H = 2.585 bits
   loaded die           H = 2.161 bits
   Fair coin = 1 bit exactly. Certainty = 0. More spread = more bits.
   Entropy is the FLOOR: no predictor of this source can average below it.
```

A fair coin is exactly 1 bit. A certain outcome is 0. The more spread out the distribution, the
higher the entropy. And it is a **floor**: no predictor, however clever, can average less
surprise than the source itself contains. Language has real entropy — the next word is
genuinely uncertain sometimes — so there is a loss below which no model can go.

## Cross-entropy: believing q when the truth is p

Now you hold a *model* `q` of a source whose real distribution is `p`. Your average surprise is
the **cross-entropy** — you are surprised according to `q`, but events arrive according to `p`:

```
   truth p = [0.7, 0.2, 0.1]   entropy H(p) = 1.157 bits
   your model q                cross-entropy    gap (KL)
   [0.7, 0.2, 0.1]                     1.157       0.000
   [0.6, 0.3, 0.1]                     1.195       0.039
   [0.4, 0.4, 0.2]                     1.422       0.265
   [0.333, 0.333, 0.333]               1.585       0.428
   [0.1, 0.2, 0.7]                     2.841       1.684
   Minimum is exactly at q = p, where cross-entropy equals entropy and
   the gap is 0. Every other q pays extra. The gap is the KL divergence.
```

Two things to see in that table. The minimum is **exactly at `q = p`**, where cross-entropy
equals entropy. And every other `q` pays a penalty — the **KL divergence**, the gap between what
you paid and the floor. It is never negative: a wrong model always costs extra.

## The training loss is a cross-entropy with a one-hot truth

```
   model q = [0.71, 0.09, 0.06, 0.04, 0.1]
   truth   = [1, 0, 0, 0, 0]   (we KNOW what came next -- all mass on one token)
   cross-entropy = -1*log(q[0]) - 0 - 0 - 0 - 0 = -log(0.71) = 0.342 nats
   With a one-hot truth, cross-entropy collapses to -log(p of the true token).
   That IS the per-token loss. 'Cross-entropy loss' and '-log p' are one thing.
```

In training, the "true distribution" for one position is trivial: the next token is known, so
`p` is a **one-hot** — all mass on that token. The cross-entropy sum then has a single non-zero
term, `-log q(true token)`. **That is the per-token loss from chapter 03.** "Cross-entropy
loss", "negative log-likelihood" and "`-log p`" are three names for one number.

## So what does lowering the loss mean?

```
   average loss over a corpus = cross-entropy(true text distribution, model)
                              = entropy(language) + KL(language || model)
   The first term is fixed -- language is genuinely unpredictable to some
   degree. Training can only shrink the second. That fixed part is the
   'irreducible loss' that scaling-law curves flatten towards (chapter 06).
```

Average the loss over a corpus and you are measuring the cross-entropy between the true
distribution of text and the model — which splits into the entropy of language (fixed) plus the
KL divergence (what training can shrink). The fixed part is the **irreducible loss** that scaling
curves flatten towards in [chapter 06](../../../06-planning-a-run/).

## Run it

```bash
python3 demo.py
```

## Terms

| Term | Meaning |
| --- | --- |
| **entropy** `H(p)` | Average surprise of a source: `-Σ p log p`. The floor on any predictor's loss. |
| **cross-entropy** `H(p, q)` | Average surprise when you believe `q` but the truth is `p`: `-Σ p log q`. |
| **KL divergence** `KL(p‖q)` | `H(p,q) − H(p)`: the extra cost of believing `q`. Always ≥ 0, zero only at `q = p`. |
| **one-hot** | A distribution with all mass on one outcome. The training target at each position. |
| **negative log-likelihood (NLL)** | `-log q(observed)`. Identical to cross-entropy against a one-hot. |
| **irreducible loss** | The entropy of the data itself; the part of the loss no model can remove. |
