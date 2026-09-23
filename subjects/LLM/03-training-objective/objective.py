#!/usr/bin/env python3
"""Generates objective.md: the training objective traced on a readable corpus.
Run: python3 objective.py"""
import io, math, collections
from bigram_lm import CORPUS, HELDOUT, BOS, tokenize, vocab_of, train_counts, prob, sequence_loss

o = io.StringIO(); W = o.write
train = tokenize(CORPUS); vocab = vocab_of(train); V = len(vocab)
counts = train_counts(train)
held = [BOS] + HELDOUT.split()
mean_loss, losses = sequence_loss(counts, vocab, held)

W(f"""# The objective, traced

Every number here is produced by `bigram_lm.py`. Run `python3 objective.py` to regenerate.

The model is a **bigram counter**: it predicts the next word from the previous word by counting
how often each pair occurred. No matrices, no gradients — those arrive in
[chapter 04](../04-optimization-loop/). Using the simplest possible model isolates the one thing
this chapter is about: **the number that says how wrong a prediction was**, and what lowering it
buys.

The corpus is {len(train)} lines and {V} distinct tokens, small enough to read in full:

```
{CORPUS}
```

The held-out sentence — not used for counting, only for measuring — is *{HELDOUT}*.

---

## 1. One sentence is many training examples

Hide the last word of any prefix and you have a labelled example. A {len(held)-1}-word sentence
gives {len(held)-1} of them, and one forward pass computes all of them at once (the causal mask
in chapter 02 is what makes that legal):

```
""")
for i in range(1, len(held)):
    W(f"  given {' '.join(held[:i]):<38} predict {held[i]!r}\n")
W(f"""```

Nobody labelled anything. The text is its own supervision — that is what **self-supervised**
means, and it is why there is effectively unlimited training data.

---

## 2. The model is a table of counts

```
""")
for prev in ("<s>", "the", "capital", "of", "is"):
    row = counts[(prev,)]; tot = sum(row.values())
    W(f"  after {prev!r:<10}: " + ", ".join(f"{k} {v}/{tot}" for k, v in row.most_common(5)) + "\n")
W(f"""```

`p(next | prev)` is just `count(prev, next) / count(prev)`, with a little smoothing so a pair the
corpus never showed is improbable rather than impossible. A real model replaces this table with
the network from chapter 02, but *what it outputs is the same object*: a probability for every
possible next token.

---

## 3. The loss, term by term

For each position, look up the probability the model gave to the token that **actually** came
next, and take `-log` of it:

```
""")
sequence_loss(counts, vocab, held, verbose=False)
for i in range(1, len(held)):
    p = prob(counts, vocab, (held[i-1],), held[i])
    W(f"  position {i}: p({held[i]!r:<9} | {held[i-1]!r:<9}) = {p:6.3f}   -log p = {-math.log(p):6.3f}\n")
W(f"""
  mean over {len(losses)} positions = {mean_loss:.3f} nats      <- the loss
```

That average is the **cross-entropy loss**. It is one scalar for the whole sentence, and it is
the only thing training ever looks at.

Why `-log`? Two reasons that both matter (→ [essentials](essentials/)):

- Probabilities *multiply* along a sequence; logs turn that into a *sum*, which does not
  underflow to zero and can be averaged.
- `-log p` is **surprise**: 0 when the model was certain and right, growing without bound as it
  assigns less and less to the truth. Confident wrongness is punished hardest:

```
""")
for p in (0.9, 0.5, 0.1, 0.01, 0.001):
    W(f"  p = {p:<6} on the true token  ->  loss {-math.log(p):6.3f}\n")
W(f"""```

---

## 4. The same number in three units

```
  loss           {mean_loss:.3f} nats            natural log; what papers report
  bits per token {mean_loss/math.log(2):.3f}               divide by ln 2; what compressors count
  perplexity     {math.exp(mean_loss):.2f}                 exp(loss); "as if choosing among {math.exp(mean_loss):.1f} equally likely tokens"
```

**Perplexity** is the most intuitive: a perplexity of {math.exp(mean_loss):.1f} means the model is, on average, as
uncertain as if it were picking uniformly among {math.exp(mean_loss):.1f} options. Lower is better; 1 is omniscience.

**Bits** is the most profound. A model with loss *L* bits per token could drive a compressor that
stores text at *L* bits per token — total here, **{sum(losses)/math.log(2):.1f} bits for the whole sentence**.
Predicting well and compressing well are the same skill. Many researchers take that literally:
*build a good compressor of the internet* and *build an intelligence* become one engineering
problem.

---

## 5. What does knowing nothing cost?

```
  uniform guess over {V} tokens   loss = ln({V}) = {math.log(V):.3f} nats   perplexity {V}
  bigram counts                   loss = {mean_loss:.3f} nats   perplexity {math.exp(mean_loss):.2f}
                                  -> {(1-mean_loss/math.log(V))*100:.0f}% of the surprise removed by counting pairs
```

The uniform baseline is the ceiling. At real scale it is `ln(50,257) = {math.log(50257):.2f}` nats for GPT-2's
vocabulary or `ln(128,256) = {math.log(128256):.2f}` for Llama-3's. A trained model lands far below: GPT-2's
published perplexity of about 37.5 on WikiText-103 corresponds to `ln(37.5) ≈ {math.log(37.5):.1f}` nats *(a
reported figure, not measured here)*, and frontier models on web text are lower still.

---

## 6. Lowering the loss means using context

A bigram model predicting after `is` cannot see `france`. Here is the last-token loss as the
model is allowed to see one, two, then three words back:

```
  sentence                              1-gram    2-gram    3-gram
""")
tests = ("the capital of france is paris", "the capital of france is rome",
         "the capital of italy is rome",  "the capital of italy is paris")
flat = collections.Counter(t for s_ in train for t in s_); tot = sum(flat.values())
c2, c3 = train_counts(train, 2), train_counts(train, 3)
for sent in tests:
    seq = [BOS] + sent.split()
    l1 = -math.log((flat[seq[-1]] + 0.5) / (tot + 0.5*V))
    _, ls2 = sequence_loss(c2, vocab, seq, n=2); _, ls3 = sequence_loss(c3, vocab, seq, n=3)
    W(f"  {sent:<36}{l1:>8.3f}{ls2[-1]:>10.3f}{ls3[-1]:>10.3f}\n")
W(f"""```

Read the two `france is` rows. With one word of context the model cannot distinguish them — same
loss for `paris` and `rome`. With two words it can: **the right answer gets cheaper and the wrong
one gets dearer.** That is the objective doing its job.

Nothing here was told to learn geography. Lower loss on `france is ___` simply *requires* knowing
that France goes with Paris. Facts, grammar, style, arithmetic — each is just a way of being less
surprised on some slice of text. And the objective rewards whichever architecture can carry more
context, which is why chapter 02's attention matters: it can look back thousands of tokens, not
two.

---

## 7. What the objective does not do

It rewards predicting **what people wrote** — including their mistakes, their biases, and the
distribution of the internet. It does not reward being helpful, brief, or correct in any sense
beyond "likely to appear next". That gap is why post-training exists
([07](../07-supervised-fine-tuning/)–[09](../09-reasoning-training/)).

It also assumes the truth is one token. The target is a **one-hot** — all probability on the word
that actually came next — so the cross-entropy collapses to `-log p(true token)`. Other
objectives exist: masked language modelling (BERT) hides words in the middle rather than the end,
and contrastive objectives compare pairs ([13](../13-multimodality/)).

---

## 8. Invariants

1. **Self-supervised**: the label is the next token. No annotation, unlimited data.
2. **One forward pass, T−1 losses**, thanks to the causal mask.
3. **Loss = mean of −log p(true token)**. Cross-entropy, negative log-likelihood, −log p: one thing.
4. **Perplexity = exp(loss)**; **bits = loss / ln 2**. Same number, three units.
5. **The uniform baseline is ln(vocab)**; the floor is the entropy of language itself.
6. **Lowering it requires using context** — which the architecture must be able to carry.
""")
open('objective.md', 'w').write(o.getvalue())
print("wrote objective.md", len(o.getvalue()), "chars")
