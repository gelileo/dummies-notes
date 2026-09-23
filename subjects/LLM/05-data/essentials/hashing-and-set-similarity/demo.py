#!/usr/bin/env python3
"""Hashing, Jaccard similarity, and MinHash -- how deduplication works at scale.
Run: python3 demo.py"""
import hashlib, random
random.seed(0)

def h(s): return hashlib.sha1(s.encode()).hexdigest()
print("=== a hash: any input -> a fixed-size fingerprint ===")
for s in ("the cat sat on the mat", "the cat sat on the mat.", "the cat sat on the mat"):
    print(f"   {s!r:<28} -> {h(s)[:16]}...")
print("   identical text -> identical hash. one changed character -> unrelated hash.")
print("   exact dedup: hash every document, keep one per hash. O(n), one pass.")

print("\n=== but near-duplicates defeat exact hashing ===")
a = "the cat sat on the mat and looked out at the rain"
b = "the cat sat on the mat and looked out at the snow"
print(f"   hash(a) = {h(a)[:16]}...   hash(b) = {h(b)[:16]}...   equal? {h(a)==h(b)}")
print("   one word differs and the hashes share nothing. you need a SIMILARITY, not equality.")

def shingles(s, k=3):
    w = s.split(); return {" ".join(w[i:i+k]) for i in range(len(w)-k+1)}
def jaccard(x, y): return len(x & y) / len(x | y)
print("\n=== Jaccard similarity of shingle sets ===")
sa, sb = shingles(a), shingles(b)
print(f"   shingles (3-word windows) of a: {len(sa)}, of b: {len(sb)}, shared: {len(sa & sb)}")
print(f"   Jaccard = shared / total distinct = {len(sa&sb)} / {len(sa|sb)} = {jaccard(sa,sb):.3f}")
c = "a good map shows the roads and the rivers but not every stone"
print(f"   a vs an unrelated sentence: Jaccard = {jaccard(sa, shingles(c)):.3f}")
print("   1.0 = identical sets, 0.0 = nothing shared. a near-dup scores high.")

print("\n=== the problem: comparing every pair of a billion documents ===")
for n in (1_000, 1_000_000, 1_000_000_000):
    print(f"   {n:>14,} docs -> {n*(n-1)//2:>24,} pairs")
print("   and each comparison needs both full shingle sets. impossible.")

print("\n=== MinHash: a short signature whose match-rate IS the Jaccard ===")
def minhash(sh, n):
    return [min(int(hashlib.md5(f"{i}:{s}".encode()).hexdigest(), 16) for s in sh) for i in range(n)]
print("   for each of n hash functions, keep only the SMALLEST hash over the set.")
print("   the chance two sets share a minimum equals their Jaccard similarity.")
print(f"   {'signature size':>15}{'estimate':>10}{'true Jaccard':>14}")
for n in (8, 32, 128, 512):
    ha, hb = minhash(sa, n), minhash(sb, n)
    est = sum(x == y for x, y in zip(ha, hb)) / n
    print(f"   {n:>15}{est:>10.3f}{jaccard(sa,sb):>14.3f}")
print("   128 numbers per document instead of the whole text, compared with a zip().")
print("   with locality-sensitive bucketing on top, near-duplicates find each other")
print("   without comparing every pair. this is how FineWeb dedups 15T tokens.")
