# Essential · Hashing, Jaccard similarity and MinHash

**Needed for:** *"exact and near-duplicate removal"* in [chapter 05](../../README.md) — how you
find duplicates among billions of documents without comparing every pair.

## A hash is a fingerprint

```
   'the cat sat on the mat'     -> ec53ce85c730038e...
   'the cat sat on the mat.'    -> 67de230e2bb3e6cb...
   'the cat sat on the mat'     -> ec53ce85c730038e...
   identical text -> identical hash. one changed character -> unrelated hash.
   exact dedup: hash every document, keep one per hash. O(n), one pass.
```

Any input, a fixed-size output, and the slightest change gives an unrelated result. Exact
deduplication is one pass: hash every document, keep the first with each hash. Billions of
documents, linear time.

## Near-duplicates defeat it

```
   hash(a) = fd41c9cc7359bcf4...   hash(b) = 4f4ecda7bf8cab8e...   equal? False
   one word differs and the hashes share nothing. you need a SIMILARITY, not equality.
```

Web text is full of documents that differ by a date, a footer, one paragraph. Their hashes share
nothing. You need a *similarity*, not equality.

## Jaccard similarity of shingle sets

Cut each document into overlapping windows of *k* words — **shingles** — and treat the document
as the *set* of them. The Jaccard similarity of two sets is *shared ÷ total distinct*:

```
   shingles (3-word windows) of a: 10, of b: 10, shared: 9
   Jaccard = shared / total distinct = 9 / 11 = 0.818
   a vs an unrelated sentence: Jaccard = 0.000
   1.0 = identical sets, 0.0 = nothing shared. a near-dup scores high.
```

Identical documents score 1.0; unrelated ones 0.0; a near-duplicate lands high. This is the
right measure. The trouble is the cost.

## Every pair of a billion documents

```
            1,000 docs ->                  499,500 pairs
        1,000,000 docs ->          499,999,500,000 pairs
    1,000,000,000 docs ->  499,999,999,500,000,000 pairs
   and each comparison needs both full shingle sets. impossible.
```

## MinHash: a short signature whose match rate *is* the Jaccard

```
   for each of n hash functions, keep only the SMALLEST hash over the set.
   the chance two sets share a minimum equals their Jaccard similarity.
    signature size  estimate  true Jaccard
                 8     0.750         0.818
                32     0.844         0.818
               128     0.859         0.818
               512     0.842         0.818
   128 numbers per document instead of the whole text, compared with a zip().
   with locality-sensitive bucketing on top, near-duplicates find each other
   without comparing every pair. this is how FineWeb dedups 15T tokens.
```

The trick: for each of *n* different hash functions, hash every shingle and keep only the
**smallest**. Two sets share a minimum with probability exactly equal to their Jaccard
similarity — so the fraction of matching positions in two signatures *estimates* it, and the
estimate tightens as *n* grows. Each document is now 128 integers instead of thousands of
shingles, and comparing two is a `zip`.

Combined with locality-sensitive bucketing — group documents whose signature *bands* match, so
candidates find each other without an all-pairs scan — this is how a 15-trillion-token corpus
gets near-deduplicated at all.

## Run it

```bash
python3 demo.py
```

## Terms

| Term | Meaning |
| --- | --- |
| **hash function** | Maps any input to a fixed-size fingerprint; tiny input change → unrelated output. |
| **exact deduplication** | Keep one document per hash. One pass. |
| **shingle** | A window of *k* consecutive words. A document becomes the set of its shingles. |
| **Jaccard similarity** | `|A ∩ B| / |A ∪ B|`: shared elements over total distinct. 0 to 1. |
| **near-duplicate** | Jaccard above a chosen threshold. The threshold is a knob. |
| **MinHash** | Per hash function, keep the minimum hash over a set. Match rate of two signatures ≈ Jaccard. |
| **signature** | A document's list of MinHash values — a compact stand-in for its shingle set. |
| **locality-sensitive hashing (LSH)** | Bucketing signatures so similar documents collide, avoiding all-pairs comparison. |
