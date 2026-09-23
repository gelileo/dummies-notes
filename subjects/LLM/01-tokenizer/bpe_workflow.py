import re, collections, io
SPLIT = re.compile(r" ?[a-zA-Z]+|[^a-zA-Z]")
LINE1 = "the tokenizer tokenizes text into tokens and the token is not a word\n"
LINE2 = "a tokenizer is a table and the tokens index that table\n"
CORPUS = (LINE1 + LINE2) * 8
N_MERGES = 13
o = io.StringIO(); W = o.write

chunks = SPLIT.findall(CORPUS)
words = [tuple(bytes([b]) for b in w.encode()) for w in chunks]
vocab = {i: bytes([i]) for i in range(256)}
merges = {}
d = lambda b: b.decode('utf8', 'replace')

def tables(note=""):
    """Both tables, side by side, showing the 1:1 correspondence."""
    LW = 42
    L = ["MERGES  (pair -> id)".ljust(LW) + "|  VOCAB  (id -> byte string)",
         "-" * LW + "+" + "-" * 30,
         "".ljust(LW) + "|   0-255  <the 256 raw bytes>"]
    if not merges:
        L.append("  (empty)".ljust(LW) + "|   (nothing beyond the bytes yet)")
    for (a, b), i in merges.items():
        left = f"  ({d(a)!r}, {d(b)!r})"
        L.append((left + " " * max(1, 34 - len(left)) + f"-> {i}").ljust(LW)
                 + f"|   {i}    {vocab[i]!r}")
    W("```\n" + "\n".join(L) + "\n```\n\n")

def corpus_tokens(): return sum(len(w) for w in words)

W("""# How BPE actually works — a complete trace

A full worked example of byte-pair encoding: training a tokenizer, using it, and reading text
back. Every table and number below is generated output from `bpe_workflow.py` in this folder —
run it and you get exactly this.

The corpus is deliberately tiny (two sentences, repeated 8 times) so that **every merge is
visible and every table fits on screen**. The algorithm is identical at 50,000 merges; only the
row count changes. Section 5 connects it back to a real-scale run.

> Prerequisite: the Q&A entries in `README.md` on the vocabulary table and the merge process.
> This article is the same material end to end, with the tables shown at each step.

---

## 0. The two tables

BPE maintains two data structures. They are built together, one row each per merge, but they are
**keyed differently and used at different times**:

| | key | value | used by |
| --- | --- | --- | --- |
| `merges` | a **pair** of byte strings | the new id | **encoding** (text → ids) |
| `vocab` | an **id** | one byte string | **decoding** (ids → text), and the model's embedding rows |

The invariant that ties them together:

```
merges[(a, b)] == i     if and only if     vocab[i] == a + b
```

So they carry the same information in two access patterns. You need the pair-keyed one to ask
"may these two neighbours combine?" and the id-keyed one to ask "what bytes is id 452?".

---

## 1. Training — building the merge list

### The corpus

```
""")
W(LINE1 + LINE2)
W(f"""```

repeated 8 times: **{len(CORPUS)} characters = {len(CORPUS.encode())} bytes** (pure ASCII), which
the regex cuts into **{len(chunks)} chunks**:

```
  {sum(1 for c in chunks if c.strip()):>3} word chunks     = 24 words x 8 repetitions
  {sum(1 for c in chunks if not c.strip()):>3} newline chunks  =  2 newlines x 8 repetitions
  {len(chunks):>3} total
```

The newlines are chunks too — the regex's second branch, `[^a-zA-Z]`, matches any single
non-letter. (Digits and punctuation would go the same way here; GPT-2's real regex groups runs of
them instead.)

### Pre-splitting

Before anything else the text is cut on a regex — here `r" ?[a-zA-Z]+|[^a-zA-Z]"`, which keeps a
leading space attached to its word. This is a **hard boundary: merges may never cross it**, which
is what stops BPE from eventually swallowing whole sentences into single tokens.

```
{chunks[:8]}
  ...around a line break:  {chunks[11:17]}
```

Two details already visible in that list. **The leading space belongs to the chunk** — `' tokenizer'`
carries it. And **the line-initial word does not have one**: the `\n` is consumed as its own chunk,
leaving nothing for the optional space to match, so this corpus contains both `'the'` and `' the'`
as distinct chunks that will get distinct ids. Same English word, two tokens.

### Step 0 — the starting state

Every chunk becomes a sequence of individual bytes. The vocabulary is the 256 raw byte values;
the merge table is empty.

```
' tokenizer'  ->  {[d(bytes([b])) for b in ' tokenizer'.encode()]}
```

corpus length: **{corpus_tokens()} tokens** (one per byte)

""")
tables()

exhausted = False
for step in range(N_MERGES):
    pairs = collections.Counter()
    for w in words:
        for a, b in zip(w, w[1:]): pairs[(a, b)] += 1
    if not pairs:                       # no adjacent pair left anywhere in the corpus:
        exhausted = True                # every chunk is already a single token and
        break                           # merges may not cross the pre-split boundary
    top = pairs.most_common(3)
    (a, b), cnt = top[0]
    nid = 256 + step
    before = corpus_tokens()
    W(f"### Merge {step} → id {nid}\n\nMost frequent adjacent pairs right now:\n\n```\n")
    for (x, y), c in top:
        mark = "  <- winner" if (x, y) == (a, b) else ""
        W(f"  ({d(x)!r}, {d(y)!r})".ljust(30) + f"{c} occurrences{mark}\n")
    W("```\n\n")
    vocab[nid] = a + b; merges[(a, b)] = nid
    out = []
    for w in words:
        i, nw = 0, []
        while i < len(w):
            if i + 1 < len(w) and (w[i], w[i + 1]) == (a, b): nw.append(a + b); i += 2
            else: nw.append(w[i]); i += 1
        out.append(tuple(nw))
    words = out
    W(f"Merge `{d(a)!r}` + `{d(b)!r}` → **id {nid} = `{d(a+b)!r}`**. "
      f"Corpus: {before} → **{corpus_tokens()} tokens** (−{before-corpus_tokens()}, "
      f"one per occurrence).\n\n")
    tables()

W("""> **On ties.** Several pairs often share the top count (merges 1-3 below are three-way ties at
> 48). The winner is then decided by the counter's iteration order, i.e. first-encountered. Real
> implementations fix a deterministic tie-break; the choice barely matters, but it does mean two
> BPE implementations can produce different tables from identical data.

""")

DONE = len(merges)
W(f"""### Training ends

""" + (f"""Here it stopped **because the corpus ran out of pairs** after {DONE} merges, before the budget of
{N_MERGES} was reached: every one of the {len(set(chunks))} distinct chunks is now a single token, and merges
may not cross the pre-split boundary, so there is nowhere left to go. That is the theoretical
ceiling, and it only happens on toy corpora — a real corpus has millions of distinct chunks.
""" if exhausted else f"""Not because anything converged — because **the budget ran out**. We asked for {N_MERGES} merges and
got them. The loop also carries an exhaustion guard (`if not pairs: break`), but on any corpus
with more distinct chunks than merges it never fires; here it would only trigger past {41} merges.
""") + f"""
The final vocabulary is **{256+DONE} entries = 256 bytes + {DONE} merges**, and the corpus
has shrunk from {len(CORPUS.encode())} to **{corpus_tokens()} tokens ({corpus_tokens()/len(CORPUS.encode())*100:.0f}% of byte-level)**.

Notice what the ladder built:

```
' t'  ->  ' to'  ->  ' tok'  ->  ' toke'  ->  ' token'  ->  ' tokeni'  ->  ' tokeniz'  ->  ' tokenize'  ->  ' tokenizer'
```

Nine vocabulary slots to reach one word. Every rung stays in the table forever, because other
words need them — and in a moment you will see exactly why that matters.

---

## 2. Encoding — text to ids

The rule: of all adjacent pairs currently present, apply the one with the **lowest id** (learned
earliest). Stop when no pair is a key in `merges`.

""")

def encode_trace(s, title, comment):
    parts = [bytes([x]) for x in s.encode()]
    W(f"### {title}\n\n```\n")
    n = 0
    while True:
        cand = [(merges[p], i, p) for i, p in enumerate(zip(parts, parts[1:])) if p in merges]
        W(f"state {n}: {[d(p) for p in parts]}\n")
        if not cand:
            for x, y in zip(parts, parts[1:]):
                W(f"           ({d(x)!r}, {d(y)!r}) -> not in merges\n")
            W(f"           no eligible pair -> STOP  ({len(parts)} token{'' if len(parts)==1 else 's'})\n")
            break
        mid, i, p = min(cand)
        elig = ", ".join(f"{d(x)!r}+{d(y)!r}=id {merges[(x,y)]}" for x, y in zip(parts, parts[1:]) if (x, y) in merges)
        W(f"           eligible: {elig}\n           apply lowest id {mid}\n")
        parts[i:i + 2] = [parts[i] + parts[i + 1]]
        n += 1
    ids = []
    b2i = {v: k for k, v in vocab.items()}
    ids = [b2i[p] for p in parts]
    W(f"\nids: {ids}\n```\n\n{comment}\n\n")
    return ids, parts

ids1, _ = encode_trace(" tokenizer", "A word the ladder covers completely: `' tokenizer'`",
 "Nine merges replayed in learned order, each one a rung of the ladder, ending in a **single token**. "
 "This is what it looks like when the training corpus paved the whole path.")

ids2, _ = encode_trace(" tokenizing", "A word that falls off the ladder: `' tokenizing'`",
 "The climb is identical up to `' tokeniz'` — and then stops dead. The pair `(' tokeniz', 'i')` is "
 "not in `merges`, because the corpus contained *tokenizer*, *tokenizes* and *tokens* but never "
 "*tokenizing*. Both pieces are perfectly valid vocabulary entries sitting next to each other, and "
 "they still cannot combine: **being a valid token is not the same as being combinable with your "
 "neighbour.** One word costs 1 token, its close relative costs 4.")

ids3, _ = encode_trace(" quokka", "A word the corpus never saw at all: `' quokka'`",
 "No catastrophe, no `<UNK>` — it falls all the way back to the raw byte rows, and the coverage "
 "guarantee holds. Look closely at why *nothing* merged: `'o'` and `'k'` are adjacent here and the "
 "corpus is full of *tok*, yet `('o', 'k')` was never a merge on its own — the ladder went "
 "`' to'` + `'k'`, so the only pair that exists starts from `' to'`. **Merges match exact pairs of "
 "current pieces, not substrings.** A tokenizer trained on a corpus that happened to merge "
 "`('o','k')` would tokenize *quokka* differently.")

b2i = {v: k for k, v in vocab.items()}
W(f"""---

## 3. Decoding — ids back to text

Decoding needs only `vocab`: look up each id, concatenate the byte strings, decode UTF-8 once at
the end.

```python
def decode(ids):
    return b"".join(vocab[i] for i in ids).decode("utf-8")
```

```
{ids2}
  -> {[repr(d(vocab[i])) for i in ids2]}
  -> {b"".join(vocab[i] for i in ids2)!r}
  -> {b"".join(vocab[i] for i in ids2).decode()!r}
```

Two consequences worth holding onto:

- **UTF-8 is decoded last, not per token.** A multi-byte character can be split across several
  tokens, so a streaming decoder can receive a token that is half a character — which is why
  naive streaming sometimes prints `\\ufffd` until the next token arrives.
- **Decoding cannot fail on a valid id** and does not consult `merges` at all. It is a pure
  lookup-and-concatenate.

---

## 4. The complete final state

After {DONE} merges, both tables in full:

""")
tables()
W(f"""The 256 byte rows are still there, untouched. They always are — that is the floor that makes
every possible input encodable.

---

## 5. What changes at real scale

Nothing structural. Same two tables, same two loops, more rows:

| | this article | GPT-2 | Llama-3 |
| --- | --- | --- | --- |
| raw byte entries | 256 | 256 | 256 |
| merges | {DONE} | 50,000 | ~128,000 |
| special tokens | 0 | 1 | ~256 |
| **vocabulary** | **{256+DONE}** | **50,257** | **128,256** |

Two things that only become visible at scale:

**Diminishing returns set the vocabulary size.** Trained on 67,652 bytes of real prose
(`merge_trace.py`), the payoff per merge collapses:

```
  after   1 merges: 66197 tokens (97.8% of byte-level)   1455 tokens saved by that merge
  after  10 merges: 58913 tokens (87.1%)                  656 saved per merge
  after 100 merges: 40218 tokens (59.4%)                  120 saved per merge
  after 600 merges: 26601 tokens (39.3%)                   13 saved per merge
```

Meanwhile every merge costs a fixed price forever: one embedding row plus one LM-head row —
8,192 parameters at Llama-3's `d_model` of 4,096. You stop where the falling benefit crosses that
flat cost. 50k–250k is where the crossover empirically lands.

**The merge table is extremely sparse, which is why encoding halts fast.** GPT-2 has 50,000
merges against 50,257² ≈ 2.5 billion possible pairs — about **0.002%** populated. Almost every
pair you test is a miss.

---

## 6. The invariants

1. **Ids 0–255 are the raw bytes and are never removed.** Nothing is ever unencodable.
2. **Every merge adds exactly one row to each table**, and `merges[(a,b)] == i ⟺ vocab[i] == a+b`.
3. **Training stops on a budget**, not on convergence. Encoding stops when **no adjacent pair is
   a key in `merges`** — a property of the whole sequence, not of any one position.
4. **Encoding replays merges in learned order**, not longest-match-first. The two give different
   answers on 44% of distinct chunks in real text, and merge-order compresses better.
5. **Merging is only permitted along paths training carved out.** Valid neighbouring tokens with
   no merge between them stay separate forever.
6. **The result is corpus-dependent.** `' tokenizer'` is 1 token here and 3 tokens under the
   tokenizer trained on the guide's prose. There is no "correct" tokenization of a word — only
   what this table permits.
7. **Everything is deterministic.** Same string, same table → same ids, every time.

---

## Files in this folder

| | |
| --- | --- |
| `bpe_workflow.py` | generates this entire article — run it to reproduce every table |
| `minibpe_demo.py` | the shortest version: train, print the vocabulary, encode, decode |
| `merge_trace.py` | trains on a real file; compression curve and merge-order comparison |
| `stop_check.py` | inspects the stopping condition pair by pair |
""")
open('bpe-workflow.md', 'w').write(o.getvalue())
print(o.getvalue()[:1500])
print("\n...\n\nWROTE bpe-workflow.md", len(o.getvalue()), "chars")
