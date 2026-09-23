# Essential · Nearest-neighbour search

**Needed for:** *"vector database"*, *"HNSW"*, *"approximate nearest neighbour"* in
[chapter 12](../../README.md).

## Brute force does not scale

```
            1,000 vectors x   128 dims:          128,000 multiply-adds per query,       0.0 GB of vectors to read
        1,000,000 vectors x  1024 dims:    1,024,000,000 multiply-adds per query,       2.0 GB of vectors to read
    1,000,000,000 vectors x  1024 dims: 1,024,000,000,000 multiply-adds per query,    2048.0 GB of vectors to read
   a billion vectors: hundreds of gigabytes streamed per query. impossible at interactive speed.
```

Retrieval means finding the vectors closest to a query. Comparing against every stored vector is
exact and, at a billion vectors, means streaming hundreds of gigabytes per query.

## A hash where similar things collide

```
   pick a random direction. every vector is either on its + side or - side: one bit.
   two vectors get the same bit with probability 1 - angle/pi.
     angle between vectors  P(same bit), formula  measured (10k planes)
                      10°                 0.944                  0.949
                      30°                 0.833                  0.829
                      60°                 0.667                  0.671
                      90°                 0.500                  0.504
                     150°                 0.167                  0.169
   16 random planes -> a 16-bit signature. near vectors share most bits; far ones do not.
```

Ordinary hashes scatter similar inputs. **Locality-sensitive hashing** does the opposite: pick a
random direction, and every vector gets one bit — which side it falls on. Two vectors at a small
angle almost always land on the same side. Sixteen random directions give a 16-bit signature;
near vectors share most bits.

## Bucketing finds the neighbours by scanning a fraction

```
   the query's true 10 nearest neighbours sit at cosine 0.65..0.67; a random vector is at ~0.01
   20,000 vectors, 12-bit signatures -> ~4,096 buckets, ~4.9 vectors each
   exact bucket only        scanned      3 of 20,000 ( 0.0%)   recall of true top-10: 0.0
   + buckets 1 bit away     scanned    294 of 20,000 ( 1.5%)   recall of true top-10: 0.1
   + buckets 2 bits away    scanned    931 of 20,000 ( 4.7%)   recall of true top-10: 0.5
   + buckets 3 bits away    scanned  2,515 of 20,000 (12.6%)   recall of true top-10: 1.0
   scanning 12.6% of the index recovered 100% of the true neighbours. that trade --
   recall for speed -- is every approximate index (LSH, IVF, HNSW). HNSW does it with a
   navigable graph instead of hash buckets and is what most vector databases run.
   (on structureless random vectors this fails outright -- nothing is near anything. ANN
    works BECAUSE real embeddings cluster.)
```

Group vectors by signature. To answer a query, look only in its bucket and the buckets a few bits
away. A fraction of the index is scanned and the true neighbours come back — here 12.6% of it for
all ten, 4.7% for half. Widen the probe for recall, narrow it for speed. **That trade is what every
approximate index makes.**

The parenthetical matters: on structureless random vectors this fails, because nothing is near
anything. ANN works *because* real embeddings cluster — documents about the same thing point the
same way.

## What production uses

HNSW builds a **navigable graph**: each vector links to a handful of neighbours across several
layers, and a query walks greedily from a coarse layer down to the fine one. IVF partitions
vectors around cluster centroids and searches the nearest few partitions, often with the vectors
compressed (product quantization). All share the shape above: touch a fraction, return nearly
the right answer, tune the fraction.

## Run it

```bash
python3 demo.py
```

## Terms

| Term | Meaning |
| --- | --- |
| **nearest-neighbour search** | Find the stored vectors most similar to a query. |
| **brute force / exact** | Compare against everything. Correct; linear in index size. |
| **approximate (ANN)** | Return nearly the closest, much faster. |
| **recall** | Fraction of the true nearest neighbours the approximate search returned. |
| **locality-sensitive hashing (LSH)** | Hashes designed so similar inputs collide. Random hyperplanes → bit signatures. |
| **signature** | The short bit-string standing in for a vector. |
| **HNSW** | Hierarchical navigable small-world graph. The dominant ANN index in vector databases. |
| **IVF** | Inverted file index: partition by centroid, search the nearest partitions. |
| **product quantization** | Compressing vectors into short codes so the index fits in memory. |
