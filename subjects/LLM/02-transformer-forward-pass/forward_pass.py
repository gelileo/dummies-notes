#!/usr/bin/env python3
"""Generates forward-pass.md: one token traced through one Transformer block,
with every real intermediate value. Run: python3 forward_pass.py"""
import io, math
from tiny_transformer import (VOCAB, encode, D_MODEL, N_HEADS, D_HEAD, D_MLP, SEQ,
                              EMBED, W_Q, W_K, W_LM, forward, rmsnorm,
                              NORM1_GAIN, matmul, transpose)

o = io.StringIO(); W = o.write
TOK = VOCAB[:]
tr = {}
IDS = encode(TOK)
_, logits, probs = forward(IDS, tr, use_rope=False)
w = max(len(t) for t in TOK)

def mat(rows, labels=None, cols=None, fmt="{:>7.2f}", note=""):
    L = []
    if cols: L.append(" "*(w+3) + "".join(f"{c:>7}" for c in cols))
    for i, r in enumerate(rows):
        lab = f"  {labels[i]:<{w}} " if labels else "  "
        L.append(lab + "[" + " ".join(fmt.format(v) if not isinstance(v,str) else f"{v:>6}"
                                      for v in r) + "]")
    W("```\n" + "\n".join(L) + ("\n" + note if note else "") + "\n```\n\n")

W(f"""# One forward pass, traced

Every number in this article is produced by `tiny_transformer.py` — a complete Transformer block
in pure Python, no dependencies. Run `python3 forward_pass.py` to regenerate it.

The model is deliberately tiny so that every vector fits on a line:

| | |
| --- | --- |
| vocabulary | {len(VOCAB)} words: `{"`, `".join(VOCAB)}` |
| `d_model` | {D_MODEL} — the width of the residual stream |
| heads | {N_HEADS}, each `d_head` = {D_HEAD} |
| MLP hidden | {D_MLP} |
| sequence | {SEQ} tokens: *{" ".join(TOK)}* |

The weights are **hand-set, not trained**, so the behaviour is legible. A real model learns
weights that do this kind of thing for its own reasons; here we install two recognisable
behaviours and watch the machinery carry them out.

Positional encoding is **switched off** for sections 1–11, so you can see attention's own
behaviour first. Section 12 turns it on and shows exactly what it changes.

---

## 0. The shape that matters

One tensor flows through the whole model: the **residual stream**, shaped `[tokens, d_model]` —
here `[{SEQ}, {D_MODEL}]`. (Real models carry a batch dimension too: `[batch, seq, d_model]`.)

Every sublayer does the same three things: *read* the stream, *compute a correction*, *add it
back*. Nothing ever replaces the stream. Hold that picture and the rest is detail.

```
  x  --> [ norm -> attention ] --+--> [ norm -> MLP ] --+--> ...
  |                              |   |                  |
  +------------- add ------------+   +------- add ------+
```

Each of the {D_MODEL} dimensions was given a meaning so the vectors stay readable:

```
  dim   0      1        2      3   |   4      5      6     7
        the    trophy   did    not |   SINK   fit    it    always-on
        <------- head 0 -------->  |   <------- head 1 -------->
```

---

## 1. Token ids become vectors

A lookup, nothing more: id *i* selects row *i* of the embedding table.

""")
mat([EMBED[t] for t in TOK], TOK, [f"d{i}" for i in range(D_MODEL)], "{:>7.1f}")
W(f"""Note `'it'` is **only itself** — dimension 6. It carries no trophy-ness at all. That matters in
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

""")
xn = [rmsnorm(EMBED[t], NORM1_GAIN) for t in TOK]
mat(xn, TOK, [f"d{i}" for i in range(D_MODEL)])
W(f"""---

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

""")
Q = matmul(xn, W_Q); K = matmul(xn, W_K)
i_it = TOK.index("it")
mat([xn[i_it], K[i_it], Q[i_it]], ["embedding", "key", "query"],
    [f"d{i}" for i in range(D_MODEL)],
    note="  the key says 'I am it' (dim 6). The query says 'I want trophy' (dim 1).")
W("""If a single matrix produced both, a token could only ever look for things like itself. Two
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

""")
def head_scores(h, mask):
    lo, hi = h*D_HEAD, (h+1)*D_HEAD
    out = []
    for i in range(SEQ):
        row = []
        for j in range(SEQ):
            if mask and j > i: row.append("-inf")
            else: row.append(sum(Q[i][d]*K[j][d] for d in range(lo,hi))/math.sqrt(D_HEAD))
        out.append(row)
    return out
mat(head_scores(0, False), TOK, TOK)
W(f"""Row `it` is the interesting one: **{head_scores(0,False)[i_it][1]:.2f} against `trophy`**, and 0.00
against everything else including itself. The query found its referent.

---

## 5. The causal mask

A token may only attend to itself and to earlier tokens. Positions to the right are set to
negative infinity *before* softmax, so they receive exactly zero weight:

""")
mat(head_scores(0, True), TOK, TOK)
W("""This one triangle is what makes the model autoregressive. It is also why a whole document can be
trained on in a single forward pass — every position predicts its own next token without seeing
it — and why the KV cache works at inference, since a past key can never change.

---

## 6. Softmax turns scores into weights

`exp` each score, divide by the sum. Every row now sums to 1, and `exp(-inf) = 0` removes the
masked positions for free.

""")
for h in range(N_HEADS):
    W(f"**Head {h}** ({'dims 0-3' if h==0 else 'dims 4-7'}) attention weights:\n\n")
    mat([[tr["weights"][h][i][j] if j <= i else "-" for j in range(SEQ)] for i in range(SEQ)],
        TOK, TOK, "{:>7.3f}")
W(f"""The two heads learned — or here, were given — completely different jobs, which is exactly what
interpretability research finds in real models:

- **Head 0 matches content.** `'it'` puts **{tr['weights'][0][i_it][1]:.1%}** of its attention on
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

""")
mat(tr["concat"], TOK, [f"d{i}" for i in range(D_MODEL)],
    note="  concat: head 0 output in dims 0-3, head 1 output in dims 4-7")
mat(tr["attn_out"], TOK, [f"d{i}" for i in range(D_MODEL)],
    note="  after W_O: the correction attention wants to add to the residual stream")
W("""---

## 8. Add it back

""")
mat(tr["after_attn"], TOK, [f"d{i}" for i in range(D_MODEL)],
    note="  x = x + attention_output")
W(f"""Look at row `it`: it started as pure dimension 6 and now carries **{tr['after_attn'][i_it][1]:.2f}
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
hidden = silu(x @ W_gate) * (x @ W_up)     # [T, {D_MLP}]
out    = hidden @ W_down                    # [T, {D_MODEL}]
```

This is where most parameters — and most of a model's stored knowledge — live.

""")
mat(tr["mlp_out"], TOK, [f"d{i}" for i in range(D_MODEL)], note="  the MLP's correction")
mat(tr["after_mlp"], TOK, [f"d{i}" for i in range(D_MODEL)], note="  x = x + mlp_output")
W(f"""That is one complete block. A real model repeats it 32–100+ times; the stream gets progressively
richer, and nothing about the shape changes.

---

## 10. Final norm and the LM head

After the last block, one more normalisation, then a `[d_model, vocab]` matrix turns each token's
vector into one raw score per vocabulary entry. Those scores are the **logits**.

Here `W_LM` is the embedding table transposed — **weight tying**, where one matrix does double
duty: id → vector on the way in, vector → score per id on the way out.

""")
mat(logits, TOK, VOCAB, "{:>7.2f}", note="  logits: [T, vocab]")
W("""Softmax over each row gives a probability distribution over the next token:

""")
mat(probs, TOK, VOCAB, "{:>7.3f}")
W(f"""Only the last row is used when generating. Every other row is a prediction the model makes for
free, and during training all of them contribute to the loss — see
[chapter 03](../03-training-objective/).

The model produces a distribution and **stops**. No loop, no sampling, no learning — picking a
token from this row is [chapter 10](../10-inference-and-decoding/)'s job.

---

## 11. Attention is order-blind

Everything above ran with positional encoding off. Here is why that matters — the same six words,
`'trophy'` moved from position 1 to position 3:

""")
A = TOK[:]; B = ["the","did","not","trophy","fit","it"]
rows = []
for use_rope in (False, True):
    for name, toks in (("A", A), ("B", B)):
        t2 = {}; forward(encode(toks), t2, use_rope=use_rope)
        ii, jj = toks.index("it"), toks.index("trophy")
        rows.append((("ON " if use_rope else "OFF"), name, " ".join(toks), jj,
                     t2["weights"][0][ii][jj]))
W("```\n  RoPE  sentence                             trophy at  'it'->'trophy'\n")
for r, name, sent, jj, val in rows:
    W(f"  {r}   {sent:<36} pos {jj}      {val:.3f}\n")
W("```\n\n")
W(f"""**With RoPE off the weight is identical — {rows[0][4]:.3f} both times.** Attention computed the
same answer no matter where the word sat. It is a set operation: it sees *what* is there, never
*where*. "dog bites man" and "man bites dog" would produce identical query, key and value vectors.

Position has to be injected deliberately. **RoPE** (rotary position embedding) rotates each
query and key by an angle proportional to its position, so that the dot product between two
tokens comes to depend on the *distance* between them. Turn it on and the weight moves.

**Be careful reading the RoPE numbers in this toy.** They look destructive because `d_head` = {D_HEAD}:

""")
for d, label in [(D_HEAD, f"this toy (d_head={D_HEAD})"), (128, "Llama-3 (d_head=128)")]:
    th = [1/(10000**(i/d)) for i in range(0, d, 2)]
    W(f"```\n  {label}\n     dimension pairs: {len(th)}\n"
      f"     rotation per position: fastest {th[0]:.4f} rad, slowest {th[-1]:.6f} rad\n```\n\n")
W(f"""With only {D_HEAD//2} dimension pairs, *every* pair spins fast and content matching is wrecked. A real
head has 64 pairs whose speeds span four orders of magnitude: the fast ones encode local position,
while the slow ones barely rotate at all and carry content across long distances intact. The
mechanism is the same; the toy just cannot show the separation.

---

## 12. Counting the parameters

Everything in this article is one of a handful of matrices. Counting them for this toy:

""")
def count(d_model, vocab, layers, n_heads, n_kv, d_head, ffn, tied):
    emb = vocab*d_model
    q = d_model*(n_heads*d_head); k = d_model*(n_kv*d_head); v = k; oo = (n_heads*d_head)*d_model
    mlp = 3*d_model*ffn
    per = q+k+v+oo+mlp+2*d_model
    return emb, per, layers*per, d_model, (0 if tied else vocab*d_model), \
           emb + layers*per + d_model + (0 if tied else vocab*d_model)
e,per,allL,fn,lm,tot = count(D_MODEL, len(VOCAB), 1, N_HEADS, N_HEADS, D_HEAD, D_MLP, True)
W(f"""```
  embedding table   {len(VOCAB):>6} x {D_MODEL:<5} = {e:>14,}
  one block                          = {per:>14,}
  final norm                         = {fn:>14,}
  LM head (tied to embedding)        = {lm:>14,}
                                       {'-'*14}
  total                                {tot:>14,}
```

Now the same arithmetic for a real model — Llama-3-8B: `d_model` 4096, 32 layers, 32 query heads
and 8 key/value heads (grouped-query attention), `d_head` 128, MLP hidden 14336, vocabulary
128256, untied LM head:

""")
e,per,allL,fn,lm,tot = count(4096, 128256, 32, 32, 8, 128, 14336, False)
W(f"""```
  embedding table   128256 x 4096     = {e:>14,}
  one block                           = {per:>14,}
  x 32 layers                         = {allL:>14,}
  final norm                          = {fn:>14,}
  LM head (untied)                    = {lm:>14,}
                                        {'-'*14}
  total                                 {tot:>14,}   = {tot/1e9:.2f}B
```

That lands on the advertised 8B, which is a good check that nothing is missing. Two things worth
reading off it:

- **The MLP dominates.** Of each block's {per:,} parameters, {3*4096*14336:,} ({3*4096*14336/per:.0%})
  are the three MLP matrices and only {per-3*4096*14336-2*4096:,} are attention. "Where does a
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
""")
open('forward-pass.md','w').write(o.getvalue())
print("wrote forward-pass.md", len(o.getvalue()), "chars")
