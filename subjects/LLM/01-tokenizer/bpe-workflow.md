# How BPE actually works — a complete trace

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
the tokenizer tokenizes text into tokens and the token is not a word
a tokenizer is a table and the tokens index that table
```

repeated 8 times: **992 characters = 992 bytes** (pure ASCII), which
the regex cuts into **208 chunks**:

```
  192 word chunks     = 24 words x 8 repetitions
   16 newline chunks  =  2 newlines x 8 repetitions
  208 total
```

The newlines are chunks too — the regex's second branch, `[^a-zA-Z]`, matches any single
non-letter. (Digits and punctuation would go the same way here; GPT-2's real regex groups runs of
them instead.)

### Pre-splitting

Before anything else the text is cut on a regex — here `r" ?[a-zA-Z]+|[^a-zA-Z]"`, which keeps a
leading space attached to its word. This is a **hard boundary: merges may never cross it**, which
is what stops BPE from eventually swallowing whole sentences into single tokens.

```
['the', ' tokenizer', ' tokenizes', ' text', ' into', ' tokens', ' and', ' the']
  ...around a line break:  [' a', ' word', '\n', 'a', ' tokenizer', ' is']
```

Two details already visible in that list. **The leading space belongs to the chunk** — `' tokenizer'`
carries it. And **the line-initial word does not have one**: the `
` is consumed as its own chunk,
leaving nothing for the optional space to match, so this corpus contains both `'the'` and `' the'`
as distinct chunks that will get distinct ids. Same English word, two tokens.

### Step 0 — the starting state

Every chunk becomes a sequence of individual bytes. The vocabulary is the 256 raw byte values;
the merge table is empty.

```
' tokenizer'  ->  [' ', 't', 'o', 'k', 'e', 'n', 'i', 'z', 'e', 'r']
```

corpus length: **992 tokens** (one per byte)

```
MERGES  (pair -> id)                      |  VOCAB  (id -> byte string)
------------------------------------------+------------------------------
                                          |   0-255  <the 256 raw bytes>
  (empty)                                 |   (nothing beyond the bytes yet)
```

### Merge 0 → id 256

Most frequent adjacent pairs right now:

```
  (' ', 't')                  96 occurrences  <- winner
  ('t', 'o')                  56 occurrences
  ('o', 'k')                  48 occurrences
```

Merge `' '` + `'t'` → **id 256 = `' t'`**. Corpus: 992 → **896 tokens** (−96, one per occurrence).

```
MERGES  (pair -> id)                      |  VOCAB  (id -> byte string)
------------------------------------------+------------------------------
                                          |   0-255  <the 256 raw bytes>
  (' ', 't')                      -> 256  |   256    b' t'
```

### Merge 1 → id 257

Most frequent adjacent pairs right now:

```
  (' t', 'o')                 48 occurrences  <- winner
  ('o', 'k')                  48 occurrences
  ('k', 'e')                  48 occurrences
```

Merge `' t'` + `'o'` → **id 257 = `' to'`**. Corpus: 896 → **848 tokens** (−48, one per occurrence).

```
MERGES  (pair -> id)                      |  VOCAB  (id -> byte string)
------------------------------------------+------------------------------
                                          |   0-255  <the 256 raw bytes>
  (' ', 't')                      -> 256  |   256    b' t'
  (' t', 'o')                     -> 257  |   257    b' to'
```

### Merge 2 → id 258

Most frequent adjacent pairs right now:

```
  (' to', 'k')                48 occurrences  <- winner
  ('k', 'e')                  48 occurrences
  ('e', 'n')                  48 occurrences
```

Merge `' to'` + `'k'` → **id 258 = `' tok'`**. Corpus: 848 → **800 tokens** (−48, one per occurrence).

```
MERGES  (pair -> id)                      |  VOCAB  (id -> byte string)
------------------------------------------+------------------------------
                                          |   0-255  <the 256 raw bytes>
  (' ', 't')                      -> 256  |   256    b' t'
  (' t', 'o')                     -> 257  |   257    b' to'
  (' to', 'k')                    -> 258  |   258    b' tok'
```

### Merge 3 → id 259

Most frequent adjacent pairs right now:

```
  (' tok', 'e')               48 occurrences  <- winner
  ('e', 'n')                  48 occurrences
  (' ', 'i')                  32 occurrences
```

Merge `' tok'` + `'e'` → **id 259 = `' toke'`**. Corpus: 800 → **752 tokens** (−48, one per occurrence).

```
MERGES  (pair -> id)                      |  VOCAB  (id -> byte string)
------------------------------------------+------------------------------
                                          |   0-255  <the 256 raw bytes>
  (' ', 't')                      -> 256  |   256    b' t'
  (' t', 'o')                     -> 257  |   257    b' to'
  (' to', 'k')                    -> 258  |   258    b' tok'
  (' tok', 'e')                   -> 259  |   259    b' toke'
```

### Merge 4 → id 260

Most frequent adjacent pairs right now:

```
  (' toke', 'n')              48 occurrences  <- winner
  (' ', 'i')                  32 occurrences
  (' ', 'a')                  32 occurrences
```

Merge `' toke'` + `'n'` → **id 260 = `' token'`**. Corpus: 752 → **704 tokens** (−48, one per occurrence).

```
MERGES  (pair -> id)                      |  VOCAB  (id -> byte string)
------------------------------------------+------------------------------
                                          |   0-255  <the 256 raw bytes>
  (' ', 't')                      -> 256  |   256    b' t'
  (' t', 'o')                     -> 257  |   257    b' to'
  (' to', 'k')                    -> 258  |   258    b' tok'
  (' tok', 'e')                   -> 259  |   259    b' toke'
  (' toke', 'n')                  -> 260  |   260    b' token'
```

### Merge 5 → id 261

Most frequent adjacent pairs right now:

```
  (' ', 'i')                  32 occurrences  <- winner
  (' ', 'a')                  32 occurrences
  ('h', 'e')                  24 occurrences
```

Merge `' '` + `'i'` → **id 261 = `' i'`**. Corpus: 704 → **672 tokens** (−32, one per occurrence).

```
MERGES  (pair -> id)                      |  VOCAB  (id -> byte string)
------------------------------------------+------------------------------
                                          |   0-255  <the 256 raw bytes>
  (' ', 't')                      -> 256  |   256    b' t'
  (' t', 'o')                     -> 257  |   257    b' to'
  (' to', 'k')                    -> 258  |   258    b' tok'
  (' tok', 'e')                   -> 259  |   259    b' toke'
  (' toke', 'n')                  -> 260  |   260    b' token'
  (' ', 'i')                      -> 261  |   261    b' i'
```

### Merge 6 → id 262

Most frequent adjacent pairs right now:

```
  (' ', 'a')                  32 occurrences  <- winner
  ('h', 'e')                  24 occurrences
  (' token', 'i')             24 occurrences
```

Merge `' '` + `'a'` → **id 262 = `' a'`**. Corpus: 672 → **640 tokens** (−32, one per occurrence).

```
MERGES  (pair -> id)                      |  VOCAB  (id -> byte string)
------------------------------------------+------------------------------
                                          |   0-255  <the 256 raw bytes>
  (' ', 't')                      -> 256  |   256    b' t'
  (' t', 'o')                     -> 257  |   257    b' to'
  (' to', 'k')                    -> 258  |   258    b' tok'
  (' tok', 'e')                   -> 259  |   259    b' toke'
  (' toke', 'n')                  -> 260  |   260    b' token'
  (' ', 'i')                      -> 261  |   261    b' i'
  (' ', 'a')                      -> 262  |   262    b' a'
```

### Merge 7 → id 263

Most frequent adjacent pairs right now:

```
  ('h', 'e')                  24 occurrences  <- winner
  (' token', 'i')             24 occurrences
  ('i', 'z')                  24 occurrences
```

Merge `'h'` + `'e'` → **id 263 = `'he'`**. Corpus: 640 → **616 tokens** (−24, one per occurrence).

```
MERGES  (pair -> id)                      |  VOCAB  (id -> byte string)
------------------------------------------+------------------------------
                                          |   0-255  <the 256 raw bytes>
  (' ', 't')                      -> 256  |   256    b' t'
  (' t', 'o')                     -> 257  |   257    b' to'
  (' to', 'k')                    -> 258  |   258    b' tok'
  (' tok', 'e')                   -> 259  |   259    b' toke'
  (' toke', 'n')                  -> 260  |   260    b' token'
  (' ', 'i')                      -> 261  |   261    b' i'
  (' ', 'a')                      -> 262  |   262    b' a'
  ('h', 'e')                      -> 263  |   263    b'he'
```

### Merge 8 → id 264

Most frequent adjacent pairs right now:

```
  (' token', 'i')             24 occurrences  <- winner
  ('i', 'z')                  24 occurrences
  ('z', 'e')                  24 occurrences
```

Merge `' token'` + `'i'` → **id 264 = `' tokeni'`**. Corpus: 616 → **592 tokens** (−24, one per occurrence).

```
MERGES  (pair -> id)                      |  VOCAB  (id -> byte string)
------------------------------------------+------------------------------
                                          |   0-255  <the 256 raw bytes>
  (' ', 't')                      -> 256  |   256    b' t'
  (' t', 'o')                     -> 257  |   257    b' to'
  (' to', 'k')                    -> 258  |   258    b' tok'
  (' tok', 'e')                   -> 259  |   259    b' toke'
  (' toke', 'n')                  -> 260  |   260    b' token'
  (' ', 'i')                      -> 261  |   261    b' i'
  (' ', 'a')                      -> 262  |   262    b' a'
  ('h', 'e')                      -> 263  |   263    b'he'
  (' token', 'i')                 -> 264  |   264    b' tokeni'
```

### Merge 9 → id 265

Most frequent adjacent pairs right now:

```
  (' tokeni', 'z')            24 occurrences  <- winner
  ('z', 'e')                  24 occurrences
  ('n', 'd')                  24 occurrences
```

Merge `' tokeni'` + `'z'` → **id 265 = `' tokeniz'`**. Corpus: 592 → **568 tokens** (−24, one per occurrence).

```
MERGES  (pair -> id)                      |  VOCAB  (id -> byte string)
------------------------------------------+------------------------------
                                          |   0-255  <the 256 raw bytes>
  (' ', 't')                      -> 256  |   256    b' t'
  (' t', 'o')                     -> 257  |   257    b' to'
  (' to', 'k')                    -> 258  |   258    b' tok'
  (' tok', 'e')                   -> 259  |   259    b' toke'
  (' toke', 'n')                  -> 260  |   260    b' token'
  (' ', 'i')                      -> 261  |   261    b' i'
  (' ', 'a')                      -> 262  |   262    b' a'
  ('h', 'e')                      -> 263  |   263    b'he'
  (' token', 'i')                 -> 264  |   264    b' tokeni'
  (' tokeni', 'z')                -> 265  |   265    b' tokeniz'
```

### Merge 10 → id 266

Most frequent adjacent pairs right now:

```
  (' tokeniz', 'e')           24 occurrences  <- winner
  ('n', 'd')                  24 occurrences
  ('e', 'r')                  16 occurrences
```

Merge `' tokeniz'` + `'e'` → **id 266 = `' tokenize'`**. Corpus: 568 → **544 tokens** (−24, one per occurrence).

```
MERGES  (pair -> id)                      |  VOCAB  (id -> byte string)
------------------------------------------+------------------------------
                                          |   0-255  <the 256 raw bytes>
  (' ', 't')                      -> 256  |   256    b' t'
  (' t', 'o')                     -> 257  |   257    b' to'
  (' to', 'k')                    -> 258  |   258    b' tok'
  (' tok', 'e')                   -> 259  |   259    b' toke'
  (' toke', 'n')                  -> 260  |   260    b' token'
  (' ', 'i')                      -> 261  |   261    b' i'
  (' ', 'a')                      -> 262  |   262    b' a'
  ('h', 'e')                      -> 263  |   263    b'he'
  (' token', 'i')                 -> 264  |   264    b' tokeni'
  (' tokeni', 'z')                -> 265  |   265    b' tokeniz'
  (' tokeniz', 'e')               -> 266  |   266    b' tokenize'
```

### Merge 11 → id 267

Most frequent adjacent pairs right now:

```
  ('n', 'd')                  24 occurrences  <- winner
  (' tokenize', 'r')          16 occurrences
  ('e', 'x')                  16 occurrences
```

Merge `'n'` + `'d'` → **id 267 = `'nd'`**. Corpus: 544 → **520 tokens** (−24, one per occurrence).

```
MERGES  (pair -> id)                      |  VOCAB  (id -> byte string)
------------------------------------------+------------------------------
                                          |   0-255  <the 256 raw bytes>
  (' ', 't')                      -> 256  |   256    b' t'
  (' t', 'o')                     -> 257  |   257    b' to'
  (' to', 'k')                    -> 258  |   258    b' tok'
  (' tok', 'e')                   -> 259  |   259    b' toke'
  (' toke', 'n')                  -> 260  |   260    b' token'
  (' ', 'i')                      -> 261  |   261    b' i'
  (' ', 'a')                      -> 262  |   262    b' a'
  ('h', 'e')                      -> 263  |   263    b'he'
  (' token', 'i')                 -> 264  |   264    b' tokeni'
  (' tokeni', 'z')                -> 265  |   265    b' tokeniz'
  (' tokeniz', 'e')               -> 266  |   266    b' tokenize'
  ('n', 'd')                      -> 267  |   267    b'nd'
```

### Merge 12 → id 268

Most frequent adjacent pairs right now:

```
  (' tokenize', 'r')          16 occurrences  <- winner
  ('e', 'x')                  16 occurrences
  (' token', 's')             16 occurrences
```

Merge `' tokenize'` + `'r'` → **id 268 = `' tokenizer'`**. Corpus: 520 → **504 tokens** (−16, one per occurrence).

```
MERGES  (pair -> id)                      |  VOCAB  (id -> byte string)
------------------------------------------+------------------------------
                                          |   0-255  <the 256 raw bytes>
  (' ', 't')                      -> 256  |   256    b' t'
  (' t', 'o')                     -> 257  |   257    b' to'
  (' to', 'k')                    -> 258  |   258    b' tok'
  (' tok', 'e')                   -> 259  |   259    b' toke'
  (' toke', 'n')                  -> 260  |   260    b' token'
  (' ', 'i')                      -> 261  |   261    b' i'
  (' ', 'a')                      -> 262  |   262    b' a'
  ('h', 'e')                      -> 263  |   263    b'he'
  (' token', 'i')                 -> 264  |   264    b' tokeni'
  (' tokeni', 'z')                -> 265  |   265    b' tokeniz'
  (' tokeniz', 'e')               -> 266  |   266    b' tokenize'
  ('n', 'd')                      -> 267  |   267    b'nd'
  (' tokenize', 'r')              -> 268  |   268    b' tokenizer'
```

> **On ties.** Several pairs often share the top count (merges 1-3 below are three-way ties at
> 48). The winner is then decided by the counter's iteration order, i.e. first-encountered. Real
> implementations fix a deterministic tie-break; the choice barely matters, but it does mean two
> BPE implementations can produce different tables from identical data.

### Training ends

Not because anything converged — because **the budget ran out**. We asked for 13 merges and
got them. The loop also carries an exhaustion guard (`if not pairs: break`), but on any corpus
with more distinct chunks than merges it never fires; here it would only trigger past 41 merges.

The final vocabulary is **269 entries = 256 bytes + 13 merges**, and the corpus
has shrunk from 992 to **504 tokens (51% of byte-level)**.

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

### A word the ladder covers completely: `' tokenizer'`

```
state 0: [' ', 't', 'o', 'k', 'e', 'n', 'i', 'z', 'e', 'r']
           eligible: ' '+'t'=id 256
           apply lowest id 256
state 1: [' t', 'o', 'k', 'e', 'n', 'i', 'z', 'e', 'r']
           eligible: ' t'+'o'=id 257
           apply lowest id 257
state 2: [' to', 'k', 'e', 'n', 'i', 'z', 'e', 'r']
           eligible: ' to'+'k'=id 258
           apply lowest id 258
state 3: [' tok', 'e', 'n', 'i', 'z', 'e', 'r']
           eligible: ' tok'+'e'=id 259
           apply lowest id 259
state 4: [' toke', 'n', 'i', 'z', 'e', 'r']
           eligible: ' toke'+'n'=id 260
           apply lowest id 260
state 5: [' token', 'i', 'z', 'e', 'r']
           eligible: ' token'+'i'=id 264
           apply lowest id 264
state 6: [' tokeni', 'z', 'e', 'r']
           eligible: ' tokeni'+'z'=id 265
           apply lowest id 265
state 7: [' tokeniz', 'e', 'r']
           eligible: ' tokeniz'+'e'=id 266
           apply lowest id 266
state 8: [' tokenize', 'r']
           eligible: ' tokenize'+'r'=id 268
           apply lowest id 268
state 9: [' tokenizer']
           no eligible pair -> STOP  (1 token)

ids: [268]
```

Nine merges replayed in learned order, each one a rung of the ladder, ending in a **single token**. This is what it looks like when the training corpus paved the whole path.

### A word that falls off the ladder: `' tokenizing'`

```
state 0: [' ', 't', 'o', 'k', 'e', 'n', 'i', 'z', 'i', 'n', 'g']
           eligible: ' '+'t'=id 256
           apply lowest id 256
state 1: [' t', 'o', 'k', 'e', 'n', 'i', 'z', 'i', 'n', 'g']
           eligible: ' t'+'o'=id 257
           apply lowest id 257
state 2: [' to', 'k', 'e', 'n', 'i', 'z', 'i', 'n', 'g']
           eligible: ' to'+'k'=id 258
           apply lowest id 258
state 3: [' tok', 'e', 'n', 'i', 'z', 'i', 'n', 'g']
           eligible: ' tok'+'e'=id 259
           apply lowest id 259
state 4: [' toke', 'n', 'i', 'z', 'i', 'n', 'g']
           eligible: ' toke'+'n'=id 260
           apply lowest id 260
state 5: [' token', 'i', 'z', 'i', 'n', 'g']
           eligible: ' token'+'i'=id 264
           apply lowest id 264
state 6: [' tokeni', 'z', 'i', 'n', 'g']
           eligible: ' tokeni'+'z'=id 265
           apply lowest id 265
state 7: [' tokeniz', 'i', 'n', 'g']
           (' tokeniz', 'i') -> not in merges
           ('i', 'n') -> not in merges
           ('n', 'g') -> not in merges
           no eligible pair -> STOP  (4 tokens)

ids: [265, 105, 110, 103]
```

The climb is identical up to `' tokeniz'` — and then stops dead. The pair `(' tokeniz', 'i')` is not in `merges`, because the corpus contained *tokenizer*, *tokenizes* and *tokens* but never *tokenizing*. Both pieces are perfectly valid vocabulary entries sitting next to each other, and they still cannot combine: **being a valid token is not the same as being combinable with your neighbour.** One word costs 1 token, its close relative costs 4.

### A word the corpus never saw at all: `' quokka'`

```
state 0: [' ', 'q', 'u', 'o', 'k', 'k', 'a']
           (' ', 'q') -> not in merges
           ('q', 'u') -> not in merges
           ('u', 'o') -> not in merges
           ('o', 'k') -> not in merges
           ('k', 'k') -> not in merges
           ('k', 'a') -> not in merges
           no eligible pair -> STOP  (7 tokens)

ids: [32, 113, 117, 111, 107, 107, 97]
```

No catastrophe, no `<UNK>` — it falls all the way back to the raw byte rows, and the coverage guarantee holds. Look closely at why *nothing* merged: `'o'` and `'k'` are adjacent here and the corpus is full of *tok*, yet `('o', 'k')` was never a merge on its own — the ladder went `' to'` + `'k'`, so the only pair that exists starts from `' to'`. **Merges match exact pairs of current pieces, not substrings.** A tokenizer trained on a corpus that happened to merge `('o','k')` would tokenize *quokka* differently.

---

## 3. Decoding — ids back to text

Decoding needs only `vocab`: look up each id, concatenate the byte strings, decode UTF-8 once at
the end.

```python
def decode(ids):
    return b"".join(vocab[i] for i in ids).decode("utf-8")
```

```
[265, 105, 110, 103]
  -> ["' tokeniz'", "'i'", "'n'", "'g'"]
  -> b' tokenizing'
  -> ' tokenizing'
```

Two consequences worth holding onto:

- **UTF-8 is decoded last, not per token.** A multi-byte character can be split across several
  tokens, so a streaming decoder can receive a token that is half a character — which is why
  naive streaming sometimes prints `\ufffd` until the next token arrives.
- **Decoding cannot fail on a valid id** and does not consult `merges` at all. It is a pure
  lookup-and-concatenate.

---

## 4. The complete final state

After 13 merges, both tables in full:

```
MERGES  (pair -> id)                      |  VOCAB  (id -> byte string)
------------------------------------------+------------------------------
                                          |   0-255  <the 256 raw bytes>
  (' ', 't')                      -> 256  |   256    b' t'
  (' t', 'o')                     -> 257  |   257    b' to'
  (' to', 'k')                    -> 258  |   258    b' tok'
  (' tok', 'e')                   -> 259  |   259    b' toke'
  (' toke', 'n')                  -> 260  |   260    b' token'
  (' ', 'i')                      -> 261  |   261    b' i'
  (' ', 'a')                      -> 262  |   262    b' a'
  ('h', 'e')                      -> 263  |   263    b'he'
  (' token', 'i')                 -> 264  |   264    b' tokeni'
  (' tokeni', 'z')                -> 265  |   265    b' tokeniz'
  (' tokeniz', 'e')               -> 266  |   266    b' tokenize'
  ('n', 'd')                      -> 267  |   267    b'nd'
  (' tokenize', 'r')              -> 268  |   268    b' tokenizer'
```

The 256 byte rows are still there, untouched. They always are — that is the floor that makes
every possible input encodable.

---

## 5. What changes at real scale

Nothing structural. Same two tables, same two loops, more rows:

| | this article | GPT-2 | Llama-3 |
| --- | --- | --- | --- |
| raw byte entries | 256 | 256 | 256 |
| merges | 13 | 50,000 | ~128,000 |
| special tokens | 0 | 1 | ~256 |
| **vocabulary** | **269** | **50,257** | **128,256** |

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
