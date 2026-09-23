#!/usr/bin/env python3
"""A real byte-level BPE, ~60 lines, no dependencies.

Trains on a small corpus and prints the vocabulary as what it actually is:
a lookup table from integer id to byte string. Run it: python3 minibpe_demo.py
"""
import re, collections

CORPUS = """
A tokenizer turns text into tokens. Tokenizing is the first step, and the
tokenization is fixed before training starts. The tokenizer's vocabulary is a
table. Token ids index that table. Tokens are not words, and a token is not a
character. The tokenizer tokenizes; the model reads the tokens.
""" * 6

SPLIT = re.compile(r" ?[A-Za-z]+|[^A-Za-z]")       # GPT-2-ish: keep the leading space
N_MERGES = 30

# ---- train ---------------------------------------------------------------
words = [tuple(bytes([b]) for b in w.encode()) for w in SPLIT.findall(CORPUS)]
vocab = {i: bytes([i]) for i in range(256)}         # ids 0..255 are the raw bytes
merges = {}                                         # (a, b) -> new id

for step in range(N_MERGES):
    pairs = collections.Counter()
    for w in words:
        for a, b in zip(w, w[1:]):
            pairs[(a, b)] += 1
    if not pairs:
        break
    (a, b), count = pairs.most_common(1)[0]
    new_id = 256 + step
    vocab[new_id] = a + b                           # the merged BYTE STRING
    merges[(a, b)] = new_id
    out = []                                        # apply the merge everywhere
    for w in words:
        i, nw = 0, []
        while i < len(w):
            if i + 1 < len(w) and (w[i], w[i + 1]) == (a, b):
                nw.append(a + b); i += 2
            else:
                nw.append(w[i]); i += 1
        out.append(tuple(nw))
    words = out
    print(f"merge {step:>2}: {a!r} + {b!r}  ->  id {new_id}  = {a+b!r}   ({count} occurrences)")

# ---- the vocabulary IS this table ----------------------------------------
def show(i):
    s = vocab[i].decode('utf-8', 'replace')
    return f"{i:>5} | {vocab[i]!r:<18} | {s!r}"

print(f"\nvocabulary: {len(vocab)} entries  (256 bytes + {len(merges)} merges)")
print("\n   id | byte string        | as text")
print("  ----+--------------------+---------")
for i in [32, 65, 97, 122, 255]:
    print(show(i), "   <- a raw byte, always present")
for i in range(256, 256 + len(merges)):
    print(show(i))

# ---- encode / decode using only that table -------------------------------
def encode(text):
    ids = []
    for w in SPLIT.findall(text):
        parts = [bytes([b]) for b in w.encode()]
        while True:
            cand = [(merges[p], i) for i, p in enumerate(zip(parts, parts[1:])) if p in merges]
            if not cand:
                break
            _, i = min(cand)                        # lowest id = earliest merge = apply first
            parts[i:i+2] = [parts[i] + parts[i+1]]
        ids += [next(k for k, v in vocab.items() if v == p) for p in parts]
    return ids

def decode(ids):
    return b"".join(vocab[i] for i in ids).decode('utf-8', 'replace')

for s in ["The tokenizer", "A tokenizing quokka", "retokenization"]:
    ids = encode(s)
    print(f"\n{s!r}")
    print("  ids   :", ids)
    print("  pieces:", [vocab[i].decode('utf-8', 'replace') for i in ids])
    print("  decode:", repr(decode(ids)), "roundtrip OK" if decode(ids) == s else "MISMATCH")
