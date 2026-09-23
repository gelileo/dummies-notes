# One forward pass, traced

Every number in this article is produced by `tiny_transformer.py` — a complete Transformer block
in pure Python, no dependencies. Run `python3 forward_pass.py` to regenerate it.

The model is deliberately tiny so that every vector fits on a line:

| | |
| --- | --- |
| vocabulary | 6 words: `the`, `trophy`, `did`, `not`, `fit`, `it` |
| `d_model` | 8 — the width of the residual stream |
| heads | 2, each `d_head` = 4 |
| MLP hidden | 16 |
| sequence | 6 tokens: *the trophy did not fit it* |

The weights are **hand-set, not trained**, so the behaviour is legible. A real model learns
weights that do this kind of thing for its own reasons; here we install two recognisable
behaviours and watch the machinery carry them out.

Positional encoding is **switched off** for sections 1–11, so you can see attention's own
behaviour first. Section 12 turns it on and shows exactly what it changes.

---

## 0. The shape that matters

One tensor flows through the whole model: the **residual stream**, shaped `[tokens, d_model]` —
here `[6, 8]`. (Real models carry a batch dimension too: `[batch, seq, d_model]`.)

Every sublayer does the same three things: *read* the stream, *compute a correction*, *add it
back*. Nothing ever replaces the stream. Hold that picture and the rest is detail.

```
  x  --> [ norm -> attention ] --+--> [ norm -> MLP ] --+--> ...
  |                              |   |                  |
  +------------- add ------------+   +------- add ------+
```

Each of the 8 dimensions was given a meaning so the vectors stay readable:

```
  dim   0      1        2      3   |   4      5      6     7
        the    trophy   did    not |   SINK   fit    it    always-on
        <------- head 0 -------->  |   <------- head 1 -------->
```

---

## 1. Token ids become vectors

A lookup, nothing more: id *i* selects row *i* of the embedding table.

```
              d0     d1     d2     d3     d4     d5     d6     d7
  the    [    1.0     0.0     0.0     0.0     2.0     0.0     0.0     1.0]
  trophy [    0.0     1.0     0.0     0.0     0.0     0.0     0.0     1.0]
  did    [    0.0     0.0     1.0     0.0     0.0     0.0     0.0     1.0]
  not    [    0.0     0.0     0.0     1.0     0.0     0.0     0.0     1.0]
  fit    [    0.0     0.0     0.0     0.0     0.0     1.0     0.0     1.0]
  it     [    0.0     0.0     0.0     0.0     0.0     0.0     1.0     1.0]
```

Note `'it'` is **only itself** — dimension 6. It carries no trophy-ness at all. That matters in
section 3.

Every token also has `1.0` in dimension 7. That is an always-on feature, the vector equivalent of
a bias term; section 6 shows what it is for.

---

## 2. RMSNorm

Before each sublayer the vector is rescaled to a fixed size, then multiplied by a learned
per-dimension gain. Root-mean-square normalisation divides by the root mean square of the
entries:

```python
rms = sqrt(mean(x**2) + eps)
out = x / rms * gain
```

It keeps activations in a stable range no matter how many layers have added to the stream. With
all gains set to 1.0 here:

```
              d0     d1     d2     d3     d4     d5     d6     d7
  the    [   1.15    0.00    0.00    0.00    2.31    0.00    0.00    1.15]
  trophy [   0.00    2.00    0.00    0.00    0.00    0.00    0.00    2.00]
  did    [   0.00    0.00    2.00    0.00    0.00    0.00    0.00    2.00]
  not    [   0.00    0.00    0.00    2.00    0.00    0.00    0.00    2.00]
  fit    [   0.00    0.00    0.00    0.00    0.00    2.00    0.00    2.00]
  it     [   0.00    0.00    0.00    0.00    0.00    0.00    2.00    2.00]
```

---

## 3. Q, K and V — three projections of the same vector

Each token produces three vectors from its (normalised) embedding, each by a different learned
matrix:

| | question it answers | matrix |
| --- | --- | --- |
| **query** | what am I looking for? | `W_Q` |
| **key** | what do I contain? | `W_K` |
| **value** | what do I hand over if selected? | `W_V` |

**Why are query and key two different matrices?** This is the usual sticking point, and this toy
answers it directly. `W_K` is the identity — a token's key is simply what it contains. `W_Q` is
the identity *except* for one edit:

```python
W_Q[6][6] = 0.0    # 'it' stops querying its own direction...
W_Q[6][1] = 1.0    # ...and asks for 'trophy' instead
```

So for the token `'it'`:

```
              d0     d1     d2     d3     d4     d5     d6     d7
  embedding [   0.00    0.00    0.00    0.00    0.00    0.00    2.00    2.00]
  key    [   0.00    0.00    0.00    0.00    0.00    0.00    2.00    2.00]
  query  [   0.00    2.00    0.00    0.00    2.00    0.00    0.00    0.00]
  the key says 'I am it' (dim 6). The query says 'I want trophy' (dim 1).
```

If a single matrix produced both, a token could only ever look for things like itself. Two
matrices let *what I am* and *what I want* point in completely different directions — which is
what makes a pronoun able to find its referent.

---

## 4. Scores

Every query is compared against every key by dot product, then divided by `sqrt(d_head)`:

```
scores[i][j] = dot(q_i, k_j) / sqrt(d_head)
```

The dot product is large when two vectors point the same way, so a score measures *how well what
token i wants matches what token j has*. The `sqrt(d_head)` keeps scores from growing with
dimension until softmax saturates into a hard pick.

Head 0 (dimensions 0–3), raw scores before masking:

```
             the trophy    did    not    fit     it
  the    [   0.67    0.00    0.00    0.00    0.00    0.00]
  trophy [   0.00    2.00    0.00    0.00    0.00    0.00]
  did    [   0.00    0.00    2.00    0.00    0.00    0.00]
  not    [   0.00    0.00    0.00    2.00    0.00    0.00]
  fit    [   0.00    0.00    0.00    0.00    0.00    0.00]
  it     [   0.00    2.00    0.00    0.00    0.00    0.00]
```

Row `it` is the interesting one: **2.00 against `trophy`**, and 0.00
against everything else including itself. The query found its referent.

---

## 5. The causal mask

A token may only attend to itself and to earlier tokens. Positions to the right are set to
negative infinity *before* softmax, so they receive exactly zero weight:

```
             the trophy    did    not    fit     it
  the    [   0.67   -inf   -inf   -inf   -inf   -inf]
  trophy [   0.00    2.00   -inf   -inf   -inf   -inf]
  did    [   0.00    0.00    2.00   -inf   -inf   -inf]
  not    [   0.00    0.00    0.00    2.00   -inf   -inf]
  fit    [   0.00    0.00    0.00    0.00    0.00   -inf]
  it     [   0.00    2.00    0.00    0.00    0.00    0.00]
```

This one triangle is what makes the model autoregressive. It is also why a whole document can be
trained on in a single forward pass — every position predicts its own next token without seeing
it — and why the KV cache works at inference, since a past key can never change.

---

## 6. Softmax turns scores into weights

`exp` each score, divide by the sum. Every row now sums to 1, and `exp(-inf) = 0` removes the
masked positions for free.

**Head 0** (dims 0-3) attention weights:

```
             the trophy    did    not    fit     it
  the    [  1.000      -      -      -      -      -]
  trophy [  0.119   0.881      -      -      -      -]
  did    [  0.107   0.107   0.787      -      -      -]
  not    [  0.096   0.096   0.096   0.711      -      -]
  fit    [  0.200   0.200   0.200   0.200   0.200      -]
  it     [  0.081   0.596   0.081   0.081   0.081   0.081]
```

**Head 1** (dims 4-7) attention weights:

```
             the trophy    did    not    fit     it
  the    [  1.000      -      -      -      -      -]
  trophy [  0.910   0.090      -      -      -      -]
  did    [  0.834   0.083   0.083      -      -      -]
  not    [  0.770   0.077   0.077   0.077      -      -]
  fit    [  0.492   0.049   0.049   0.049   0.361      -]
  it     [  0.668   0.066   0.066   0.066   0.066   0.066]
```

The two heads learned — or here, were given — completely different jobs, which is exactly what
interpretability research finds in real models:

- **Head 0 matches content.** `'it'` puts **59.6%** of its attention on
  `'trophy'` and about 8% on each of the rest.
- **Head 1 is an attention sink.** Every token dumps most of its weight on the first token
  (`'the'` holds dimension 4 and `W_Q[7][4] = 1.0` makes the always-on feature query it). Real
  models do this constantly — a head with nothing useful to do parks its attention on position 0
  rather than disturbing the residual stream.
- **A head with no signal goes uniform.** Look at row `fit` in head 0: `0.200` five times. Its
  query is all zeros in those dimensions, so every score ties and softmax spreads evenly. That
  row is just averaging.

---

## 7. Values, concatenate, project

Each head's output is the weighted sum of the value vectors — the weights above applied to `V`.
The heads are then concatenated back to `d_model` and passed through `W_O`:

```
              d0     d1     d2     d3     d4     d5     d6     d7
  the    [   1.15    0.00    0.00    0.00    2.31    0.00    0.00    1.15]
  trophy [   0.14    1.76    0.00    0.00    2.10    0.00    0.00    1.23]
  did    [   0.12    0.21    1.57    0.00    1.93    0.00    0.00    1.29]
  not    [   0.11    0.19    0.19    1.42    1.78    0.00    0.00    1.35]
  fit    [   0.23    0.40    0.40    0.40    1.14    0.72    0.00    1.58]
  it     [   0.09    1.19    0.16    0.16    1.54    0.13    0.13    1.44]
  concat: head 0 output in dims 0-3, head 1 output in dims 4-7
```

```
              d0     d1     d2     d3     d4     d5     d6     d7
  the    [   1.15    0.00    0.00    0.00    2.31    0.00    0.00    1.15]
  trophy [   0.14    1.76    0.00    0.00    2.10    0.00    0.00    1.23]
  did    [   0.12    0.21    1.57    0.00    1.93    0.00    0.00    1.29]
  not    [   0.11    0.19    0.19    1.42    1.78    0.00    0.00    1.35]
  fit    [   0.23    0.40    0.40    0.40    1.14    0.72    0.00    1.58]
  it     [   0.09    1.19    0.16    0.16    1.54    0.13    0.13    1.44]
  after W_O: the correction attention wants to add to the residual stream
```

---

## 8. Add it back

```
              d0     d1     d2     d3     d4     d5     d6     d7
  the    [   2.15    0.00    0.00    0.00    4.31    0.00    0.00    2.15]
  trophy [   0.14    2.76    0.00    0.00    2.10    0.00    0.00    2.23]
  did    [   0.12    0.21    2.57    0.00    1.93    0.00    0.00    2.29]
  not    [   0.11    0.19    0.19    2.42    1.78    0.00    0.00    2.35]
  fit    [   0.23    0.40    0.40    0.40    1.14    1.72    0.00    2.58]
  it     [   0.09    1.19    0.16    0.16    1.54    0.13    1.13    2.44]
  x = x + attention_output
```

Look at row `it`: it started as pure dimension 6 and now carries **1.19
in dimension 1** — trophy-ness that attention copied in from four positions back. That copy is
the entire point of the mechanism.

Because this is an addition rather than a replacement, the original `'it'` information is still
there. A later layer can use both.

---

## 9. The MLP

Attention moves information *between* tokens. The MLP processes each token *on its own* — no
mixing. Modern models use SwiGLU: two projections up, one gated by the other through SiLU, then
one projection back down.

```python
hidden = silu(x @ W_gate) * (x @ W_up)     # [T, 16]
out    = hidden @ W_down                    # [T, 8]
```

This is where most parameters — and most of a model's stored knowledge — live.

```
              d0     d1     d2     d3     d4     d5     d6     d7
  the    [   0.11    0.00    0.00    0.00    0.51    0.00    0.00    0.11]
  trophy [   0.00    0.32    0.00    0.00    0.17    0.00    0.00    0.20]
  did    [   0.00    0.00    0.30    0.00    0.16    0.00    0.00    0.23]
  not    [   0.00    0.00    0.00    0.28    0.14    0.00    0.00    0.27]
  fit    [   0.00    0.01    0.01    0.01    0.07    0.17    0.00    0.43]
  it     [   0.00    0.08    0.00    0.00    0.14    0.00    0.07    0.39]
  the MLP's correction
```

```
              d0     d1     d2     d3     d4     d5     d6     d7
  the    [   2.26    0.00    0.00    0.00    4.82    0.00    0.00    2.26]
  trophy [   0.14    3.08    0.00    0.00    2.27    0.00    0.00    2.43]
  did    [   0.12    0.21    2.88    0.00    2.08    0.00    0.00    2.53]
  not    [   0.11    0.19    0.19    2.71    1.92    0.00    0.00    2.61]
  fit    [   0.23    0.41    0.41    0.41    1.21    1.90    0.00    3.02]
  it     [   0.09    1.27    0.16    0.16    1.68    0.13    1.20    2.83]
  x = x + mlp_output
```

That is one complete block. A real model repeats it 32–100+ times; the stream gets progressively
richer, and nothing about the shape changes.

---

## 10. Final norm and the LM head

After the last block, one more normalisation, then a `[d_model, vocab]` matrix turns each token's
vector into one raw score per vocabulary entry. Those scores are the **logits**.

Here `W_LM` is the embedding table transposed — **weight tying**, where one matrix does double
duty: id → vector on the way in, vector → score per id on the way out.

```
             the trophy    did    not    fit     it
  the    [   6.93    1.11    1.11    1.11    1.11    1.11]
  trophy [   4.43    3.44    1.51    1.51    1.51    1.51]
  did    [   4.42    1.78    3.50    1.64    1.64    1.64]
  not    [   4.39    1.87    1.87    3.55    1.75    1.75]
  fit    [   4.18    2.53    2.53    2.53    3.62    2.23]
  it     [   4.76    3.10    2.26    2.26    2.24    3.05]
  logits: [T, vocab]
```

Softmax over each row gives a probability distribution over the next token:

```
             the trophy    did    not    fit     it
  the    [  0.985   0.003   0.003   0.003   0.003   0.003]
  trophy [  0.631   0.232   0.034   0.034   0.034   0.034]
  did    [  0.603   0.043   0.241   0.037   0.037   0.037]
  not    [  0.575   0.047   0.047   0.250   0.041   0.041]
  fit    [  0.436   0.084   0.084   0.084   0.251   0.062]
  it     [  0.618   0.118   0.051   0.051   0.050   0.112]
```

Only the last row is used when generating. Every other row is a prediction the model makes for
free, and during training all of them contribute to the loss — see
[chapter 03](../03-training-objective/).

The model produces a distribution and **stops**. No loop, no sampling, no learning — picking a
token from this row is [chapter 10](../10-inference-and-decoding/)'s job.

---

## 11. Attention is order-blind

Everything above ran with positional encoding off. Here is why that matters — the same six words,
`'trophy'` moved from position 1 to position 3:

```
  RoPE  sentence                             trophy at  'it'->'trophy'
  OFF   the trophy did not fit it            pos 1      0.596
  OFF   the did not trophy fit it            pos 3      0.596
  ON    the trophy did not fit it            pos 1      0.037
  ON    the did not trophy fit it            pos 3      0.058
```

**With RoPE off the weight is identical — 0.596 both times.** Attention computed the
same answer no matter where the word sat. It is a set operation: it sees *what* is there, never
*where*. "dog bites man" and "man bites dog" would produce identical query, key and value vectors.

Position has to be injected deliberately. **RoPE** (rotary position embedding) rotates each
query and key by an angle proportional to its position, so that the dot product between two
tokens comes to depend on the *distance* between them. Turn it on and the weight moves.

**Be careful reading the RoPE numbers in this toy.** They look destructive because `d_head` = 4:

```
  this toy (d_head=4)
     dimension pairs: 2
     rotation per position: fastest 1.0000 rad, slowest 0.010000 rad
```

```
  Llama-3 (d_head=128)
     dimension pairs: 64
     rotation per position: fastest 1.0000 rad, slowest 0.000115 rad
```

With only 2 dimension pairs, *every* pair spins fast and content matching is wrecked. A real
head has 64 pairs whose speeds span four orders of magnitude: the fast ones encode local position,
while the slow ones barely rotate at all and carry content across long distances intact. The
mechanism is the same; the toy just cannot show the separation.

---

## 12. Counting the parameters

Everything in this article is one of a handful of matrices. Counting them for this toy:

```
  embedding table        6 x 8     =             48
  one block                          =            656
  final norm                         =              8
  LM head (tied to embedding)        =              0
                                       --------------
  total                                           712
```

Now the same arithmetic for a real model — Llama-3-8B: `d_model` 4096, 32 layers, 32 query heads
and 8 key/value heads (grouped-query attention), `d_head` 128, MLP hidden 14336, vocabulary
128256, untied LM head:

```
  embedding table   128256 x 4096     =    525,336,576
  one block                           =    218,112,000
  x 32 layers                         =  6,979,584,000
  final norm                          =          4,096
  LM head (untied)                    =    525,336,576
                                        --------------
  total                                  8,030,261,248   = 8.03B
```

That lands on the advertised 8B, which is a good check that nothing is missing. Two things worth
reading off it:

- **The MLP dominates.** Of each block's 218,112,000 parameters, 176,160,768 (81%)
  are the three MLP matrices and only 41,943,040 are attention. "Where does a
  model store what it knows?" — mostly there.
- **Grouped-query attention is an inference decision made here.** `W_K` and `W_V` project to 8
  heads instead of 32, cutting those matrices to a quarter. The saving that matters is not the
  parameters but the KV cache at serving time — [chapter 11](../11-efficiency/).

---

## 13. The invariants

1. **One tensor flows through everything**, shaped `[batch, seq, d_model]`. Every sublayer reads
   it, computes a correction, and adds the correction back.
2. **Attention is the only place tokens see each other.** The MLP, the norms and the LM head all
   act on one token at a time.
3. **Query and key are different projections**, which is what lets a token look for something
   unlike itself.
4. **The causal mask is one triangle of `-inf`**, and it is the reason the model is
   autoregressive, trainable in one pass, and cacheable at inference.
5. **Attention alone is order-blind.** Position is injected separately, by RoPE.
6. **The block is shape-preserving**, so stacking it changes nothing structural — which is why
   the same design works from 100M to 1T parameters.
7. **The output is a distribution, and that is where the forward pass ends.**
