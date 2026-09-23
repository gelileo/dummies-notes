# The objective, traced

Every number here is produced by `bigram_lm.py`. Run `python3 objective.py` to regenerate.

The model is a **bigram counter**: it predicts the next word from the previous word by counting
how often each pair occurred. No matrices, no gradients — those arrive in
[chapter 04](../04-optimization-loop/). Using the simplest possible model isolates the one thing
this chapter is about: **the number that says how wrong a prediction was**, and what lowering it
buys.

The corpus is 8 lines and 17 distinct tokens, small enough to read in full:

```
the capital of france is paris
the capital of italy is rome
the capital of spain is madrid
the capital of france is paris
paris is the capital of france
rome is the capital of italy
the cat sat on the mat
the dog sat on the rug
```

The held-out sentence — not used for counting, only for measuring — is *the capital of france is paris*.

---

## 1. One sentence is many training examples

Hide the last word of any prefix and you have a labelled example. A 6-word sentence
gives 6 of them, and one forward pass computes all of them at once (the causal mask
in chapter 02 is what makes that legal):

```
  given <s>                                    predict 'the'
  given <s> the                                predict 'capital'
  given <s> the capital                        predict 'of'
  given <s> the capital of                     predict 'france'
  given <s> the capital of france              predict 'is'
  given <s> the capital of france is           predict 'paris'
```

Nobody labelled anything. The text is its own supervision — that is what **self-supervised**
means, and it is why there is effectively unlimited training data.

---

## 2. The model is a table of counts

```
  after '<s>'     : the 6/8, paris 1/8, rome 1/8
  after 'the'     : capital 6/10, cat 1/10, mat 1/10, dog 1/10, rug 1/10
  after 'capital' : of 6/6
  after 'of'      : france 3/6, italy 2/6, spain 1/6
  after 'is'      : paris 2/6, the 2/6, rome 1/6, madrid 1/6
```

`p(next | prev)` is just `count(prev, next) / count(prev)`, with a little smoothing so a pair the
corpus never showed is improbable rather than impossible. A real model replaces this table with
the network from chapter 02, but *what it outputs is the same object*: a probability for every
possible next token.

---

## 3. The loss, term by term

For each position, look up the probability the model gave to the token that **actually** came
next, and take `-log` of it:

```
  position 1: p('the'     | '<s>'    ) =  0.394   -log p =  0.932
  position 2: p('capital' | 'the'    ) =  0.351   -log p =  1.046
  position 3: p('of'      | 'capital') =  0.448   -log p =  0.802
  position 4: p('france'  | 'of'     ) =  0.241   -log p =  1.421
  position 5: p('is'      | 'france' ) =  0.238   -log p =  1.435
  position 6: p('paris'   | 'is'     ) =  0.172   -log p =  1.758

  mean over 6 positions = 1.232 nats      <- the loss
```

That average is the **cross-entropy loss**. It is one scalar for the whole sentence, and it is
the only thing training ever looks at.

Why `-log`? Two reasons that both matter (→ [essentials](essentials/)):

- Probabilities *multiply* along a sequence; logs turn that into a *sum*, which does not
  underflow to zero and can be averaged.
- `-log p` is **surprise**: 0 when the model was certain and right, growing without bound as it
  assigns less and less to the truth. Confident wrongness is punished hardest:

```
  p = 0.9    on the true token  ->  loss  0.105
  p = 0.5    on the true token  ->  loss  0.693
  p = 0.1    on the true token  ->  loss  2.303
  p = 0.01   on the true token  ->  loss  4.605
  p = 0.001  on the true token  ->  loss  6.908
```

---

## 4. The same number in three units

```
  loss           1.232 nats            natural log; what papers report
  bits per token 1.778               divide by ln 2; what compressors count
  perplexity     3.43                 exp(loss); "as if choosing among 3.4 equally likely tokens"
```

**Perplexity** is the most intuitive: a perplexity of 3.4 means the model is, on average, as
uncertain as if it were picking uniformly among 3.4 options. Lower is better; 1 is omniscience.

**Bits** is the most profound. A model with loss *L* bits per token could drive a compressor that
stores text at *L* bits per token — total here, **10.7 bits for the whole sentence**.
Predicting well and compressing well are the same skill. Many researchers take that literally:
*build a good compressor of the internet* and *build an intelligence* become one engineering
problem.

---

## 5. What does knowing nothing cost?

```
  uniform guess over 17 tokens   loss = ln(17) = 2.833 nats   perplexity 17
  bigram counts                   loss = 1.232 nats   perplexity 3.43
                                  -> 57% of the surprise removed by counting pairs
```

The uniform baseline is the ceiling. At real scale it is `ln(50,257) = 10.82` nats for GPT-2's
vocabulary or `ln(128,256) = 11.76` for Llama-3's. A trained model lands far below: GPT-2's
published perplexity of about 37.5 on WikiText-103 corresponds to `ln(37.5) ≈ 3.6` nats *(a
reported figure, not measured here)*, and frontier models on web text are lower still.

---

## 6. Lowering the loss means using context

A bigram model predicting after `is` cannot see `france`. Here is the last-token loss as the
model is allowed to see one, two, then three words back:

```
  sentence                              1-gram    2-gram    3-gram
  the capital of france is paris         2.914     1.758     1.435
  the capital of france is rome          3.250     2.269     3.045
  the capital of italy is rome           3.250     2.269     1.846
  the capital of italy is paris          2.914     1.758     2.944
```

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
