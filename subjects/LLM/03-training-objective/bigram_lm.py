#!/usr/bin/env python3
"""The training objective, isolated from the optimizer.

A bigram language model 'trained' by COUNTING -- no gradients, no matrices --
so that the loss itself is the only thing on the table. Everything chapter 03
claims about next-token prediction, cross-entropy, perplexity and bits can be
watched happening on a corpus small enough to read.

Run: python3 bigram_lm.py
"""
import math, collections

CORPUS = """the capital of france is paris
the capital of italy is rome
the capital of spain is madrid
the capital of france is paris
paris is the capital of france
rome is the capital of italy
the cat sat on the mat
the dog sat on the rug"""

HELDOUT = "the capital of france is paris"
BOS = "<s>"

def tokenize(text):           # words are tokens here; chapter 01 explains why real models don't
    return [[BOS] + line.split() for line in text.strip().splitlines()]

def vocab_of(seqs):
    return sorted({t for s in seqs for t in s})

# ---------------------------------------------------------------- "training"
def train_counts(seqs, n=2):
    """Count how often each token follows each (n-1)-token context.
    n=2 is a bigram model: the context is just the previous token."""
    counts = collections.defaultdict(collections.Counter)
    for s in seqs:
        s = [BOS] * (n - 2) + s                 # pad so early tokens have a full context
        for i in range(n - 1, len(s)):
            ctx = tuple(s[i - n + 1:i])
            counts[ctx][s[i]] += 1
    return counts

def prob(counts, vocab, ctx, nxt, alpha=0.5):
    """p(next | context), with add-alpha smoothing so unseen pairs are not impossible."""
    row = counts.get(tuple(ctx), {})
    total = sum(row.values())
    return (row.get(nxt, 0) + alpha) / (total + alpha * len(vocab))

# ---------------------------------------------------------------- the objective
def sequence_loss(counts, vocab, seq, n=2, verbose=False):
    """Average cross-entropy, in nats, over every next-token prediction in seq."""
    seq = [BOS] * (n - 2) + seq
    losses = []
    for i in range(n - 1, len(seq)):
        ctx, nxt = tuple(seq[i - n + 1:i]), seq[i]
        p = prob(counts, vocab, ctx, nxt)
        l = -math.log(p)
        losses.append(l)
        if verbose:
            shown = ' '.join(ctx) if n > 2 else ctx[0]
            print(f"   position {i-(n-2)}: p({nxt!r:<9} | {shown!r:<9}) = {p:6.3f}   -log p = {l:6.3f}")
    return sum(losses) / len(losses), losses

if __name__ == "__main__":
    train = tokenize(CORPUS)
    vocab = vocab_of(train)
    V = len(vocab)
    counts = train_counts(train)
    held = [BOS] + HELDOUT.split()

    print(f"corpus: {len(train)} lines, vocabulary {V} tokens\n")

    print("=== 1. one sentence is T-1 training examples (teacher forcing) ===")
    for i in range(1, len(held)):
        print(f"   given {' '.join(held[:i]):<40} predict {held[i]!r}")

    print("\n=== 2. the model is a table of counts: p(next | prev) ===")
    for prev in ("the", "capital", "is"):
        row = counts[(prev,)]
        tot = sum(row.values())
        print(f"   after {prev!r:<9}: " + ", ".join(f"{k} {v}/{tot}" for k, v in row.most_common(4)))

    print("\n=== 3. the loss on the held-out sentence, term by term ===")
    mean_loss, losses = sequence_loss(counts, vocab, held, verbose=True)
    print(f"   mean loss (cross-entropy) = {mean_loss:.3f} nats")

    print("\n=== 4. the same number in other units ===")
    print(f"   perplexity      = exp({mean_loss:.3f}) = {math.exp(mean_loss):.2f}"
          f"   <- 'as if choosing among {math.exp(mean_loss):.1f} equally likely tokens'")
    print(f"   bits per token  = {mean_loss/math.log(2):.3f}")
    print(f"   bits for the whole sentence = {sum(losses)/math.log(2):.1f}"
          f"   (a compressor using this model would need about this many)")

    print("\n=== 5. baselines: what does 'knowing nothing' cost? ===")
    uniform = math.log(V)
    print(f"   uniform guess over {V} tokens: loss = ln({V}) = {uniform:.3f} nats, perplexity {V}")
    print(f"   our bigram model:               loss = {mean_loss:.3f} nats, perplexity {math.exp(mean_loss):.2f}")
    print(f"   -> counting bigrams removed {(1-mean_loss/uniform)*100:.0f}% of the surprise")

    print("\n=== 6. the loss punishes confident wrongness hardest ===")
    for p in (0.9, 0.5, 0.1, 0.01, 0.001):
        print(f"   assigned p = {p:<6} to the true token -> loss {-math.log(p):6.3f}")

    print("\n=== 7. lowering the loss requires USING CONTEXT ===")
    print("   a bigram model predicting after 'is' cannot see 'france' at all.")
    print("   give the model a longer context and watch the last-token loss:\n")
    tests = ("the capital of france is paris", "the capital of france is rome",
             "the capital of italy is rome",  "the capital of italy is paris")
    print(f"   {'sentence':<32}" + "".join(f"{f'{n}-gram':>10}" for n in (1, 2, 3)))
    for sent in tests:
        seq = [BOS] + sent.split()
        row = []
        for n in (1, 2, 3):
            c = train_counts(train, n) if n > 1 else None
            if n == 1:
                # unigram: ignore context entirely, just token frequency
                flat = collections.Counter(t for s_ in train for t in s_)
                tot = sum(flat.values()); a = 0.5
                lp = -math.log((flat[seq[-1]] + a) / (tot + a * V))
            else:
                _, ls = sequence_loss(c, vocab, seq, n=n); lp = ls[-1]
            row.append(lp)
        print(f"   {sent:<32}" + "".join(f"{x:>10.3f}" for x in row))
    print("\n   1-gram sees nothing, 2-gram sees 'is', 3-gram sees 'france is'.")
    print("   Only the 3-gram can tell paris-after-france from rome-after-france:")
    print("   right answers get cheaper AND wrong ones get dearer. The objective")
    print("   rewards whatever architecture can carry more context -- chapter 02.")
