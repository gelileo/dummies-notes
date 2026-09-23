#!/usr/bin/env python3
"""Term weighting: why 'the' counts for nothing and 'quantization' for a lot. Run: python3 demo.py"""
import math, collections

DOCS = ["the cat sat on the mat", "the dog sat on the rug", "quantization stores weights in fewer bits",
        "the weights of the model are stored in bf16", "a cat and a dog sat together"]
def toks(d): return d.split()
N = len(DOCS)

print("=== term frequency alone rewards the wrong words ===")
tf = collections.Counter(toks(DOCS[0]))
print(f"   doc 0: {DOCS[0]!r}")
print(f"   counts: {dict(tf)}   -> 'the' is the top term. useless.")

print("\n=== document frequency: how many documents contain the word? ===")
df = collections.Counter(t for d in DOCS for t in set(toks(d)))
for t in ("the", "sat", "cat", "quantization"):
    print(f"   {t:<14} appears in {df[t]}/{N} documents")

print("\n=== inverse document frequency: rare across documents = informative ===")
print("   idf(t) = log(N / df(t))     (+1 variants keep it positive)")
for t in ("the", "sat", "cat", "quantization"):
    print(f"   {t:<14} idf = log({N}/{df[t]}) = {math.log(N/df[t]):.3f}")
print("   'the' is in every document: idf 0, weight 0. 'quantization' is in one: highest weight.")

print("\n=== tf-idf: count in THIS document x rarity ACROSS documents ===")
for i in (0, 2):
    w = {t: c * math.log(N/df[t]) for t, c in collections.Counter(toks(DOCS[i])).items()}
    top = sorted(w.items(), key=lambda kv: -kv[1])[:3]
    print(f"   doc {i}: {DOCS[i]!r}")
    print(f"          top weights: " + ", ".join(f"{t} {v:.2f}" for t, v in top))
print("   a document becomes a vector over the vocabulary; cosine similarity between those")
print("   vectors is the classical 'embedding' -- chapter 02's geometry with counts instead of learning.")

print("\n=== BM25: two fixes to raw tf ===")
k1, b = 1.5, 0.75; avgdl = sum(len(toks(d)) for d in DOCS) / N
def bm25_tf(c, dl): return c * (k1 + 1) / (c + k1 * (1 - b + b * dl / avgdl))
print(f"   1. saturation: the 10th occurrence of a word matters less than the 1st.")
print(f"   {'count':>7}{'raw tf':>8}{'BM25 tf (dl=avg)':>18}")
for c in (1, 2, 5, 10, 50):
    print(f"   {c:>7}{c:>8}{bm25_tf(c, avgdl):>18.2f}")
print(f"   2. length normalisation: a match in a short document counts more than in a long one.")
for dl in (avgdl/2, avgdl, avgdl*3):
    print(f"      doc length {dl:>5.1f} words (avg {avgdl:.1f}):  tf=2 -> {bm25_tf(2, dl):.2f}")
print("   BM25 = sum over query terms of idf(t) x saturated, length-normalised tf. it has been")
print("   the keyword-search baseline since the 1990s and still beats embeddings on exact terms.")
