#!/usr/bin/env python3
"""Finding the closest vectors without checking them all: brute force vs random-hyperplane LSH.
Run: python3 demo.py"""
import numpy as np
rng = np.random.default_rng(0)

print("=== brute force: compare the query with every vector ===")
for n, d in ((1_000, 128), (1_000_000, 1024), (1_000_000_000, 1024)):
    print(f"   {n:>14,} vectors x {d:>5} dims: {n*d:>16,} multiply-adds per query, {n*d*2/1e9:>9.1f} GB of vectors to read")
print("   a billion vectors: hundreds of gigabytes streamed per query. impossible at interactive speed.")

print("\n=== the trick: a hash where SIMILAR vectors collide ===")
print("   pick a random direction. every vector is either on its + side or - side: one bit.")
print("   two vectors get the same bit with probability 1 - angle/pi.")
d = 64; a = rng.normal(size=d); a /= np.linalg.norm(a)
print(f"   {'angle between vectors':>23}{'P(same bit), formula':>22}{'measured (10k planes)':>23}")
for deg in (10, 30, 60, 90, 150):
    th = np.radians(deg); v = np.zeros(d); v[0] = 1; u = np.array([np.cos(th), np.sin(th)] + [0]*(d-2))
    planes = rng.normal(size=(10000, d))
    same = np.mean(np.sign(planes @ v) == np.sign(planes @ u))
    print(f"   {deg:>21}°{1 - th/np.pi:>22.3f}{same:>23.3f}")
print("   16 random planes -> a 16-bit signature. near vectors share most bits; far ones do not.")

print("\n=== does bucketing find the true neighbours? (data WITH neighbourhoods, like real embeddings) ===")
n, d, K = 20000, 64, 12
centres = rng.normal(size=(200, d))                                   # 200 topics
X = centres[rng.integers(0, 200, n)] + 0.12 * rng.normal(size=(n, d))  # 100 near-duplicates per topic (cosine ~0.9, like real embeddings of related text)
X /= np.linalg.norm(X, axis=1, keepdims=True)
planes = rng.normal(size=(K, d))
sig = (X @ planes.T > 0).astype(np.uint8)
codes = sig @ (1 << np.arange(K))
buckets = {}
for i, c in enumerate(codes): buckets.setdefault(int(c), []).append(i)
q = X[0] + 0.15 * rng.normal(size=d); q /= np.linalg.norm(q)
true = np.argsort(-(X @ q))[:10]
print(f"   the query's true 10 nearest neighbours sit at cosine {(X[true] @ q).min():.2f}..{(X[true] @ q).max():.2f}; a random vector is at ~{np.median(X @ q):.2f}")
qc = int((planes @ q > 0).astype(np.uint8) @ (1 << np.arange(K)))
print(f"   {n:,} vectors, {K}-bit signatures -> ~{2**K:,} buckets, ~{n/2**K:.1f} vectors each")
best = None
for probes, label in ((0, "exact bucket only"), (1, "+ buckets 1 bit away"), (2, "+ buckets 2 bits away"), (3, "+ buckets 3 bits away")):
    cand = set()
    for c in buckets:
        if bin(c ^ qc).count("1") <= probes: cand.update(buckets[c])
    recall = len(set(true) & cand) / 10
    print(f"   {label:<24} scanned {len(cand):>6,} of {n:,} ({len(cand)/n:>5.1%})   recall of true top-10: {recall:.1f}")
    if recall >= 0.7 and best is None: best = (len(cand)/n, recall)
if best:
    print(f"   scanning {best[0]:.1%} of the index recovered {best[1]:.0%} of the true neighbours. that trade --")
else:
    print("   recall stays low here: the signature is too coarse for these clusters. widen the probe or")
    print("   add planes. either way the shape is the same: scan a fraction, recover most. that trade --")
print("   recall for speed -- is every approximate index (LSH, IVF, HNSW). HNSW does it with a")
print("   navigable graph instead of hash buckets and is what most vector databases run.")
print("   (on structureless random vectors this fails outright -- nothing is near anything. ANN")
print("    works BECAUSE real embeddings cluster.)")
