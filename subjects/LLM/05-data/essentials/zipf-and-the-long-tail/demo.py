#!/usr/bin/env python3
"""Zipf's law measured on real text, and what it means for rare tokens.
Run: python3 demo.py"""
import collections, re, math, os

path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "twelve-ideas-behind-modern-ai.md")
text = open(path, encoding="utf-8").read().lower()
words = re.findall(r"[a-z]+", text)
freq = collections.Counter(words).most_common()
N = len(words); Vd = len(freq)

print(f"=== word frequencies in a real 67KB document ({N:,} words, {Vd:,} distinct) ===")
print(f"   {'rank':>5}{'word':>12}{'count':>7}{'rank x count':>14}{'share of text':>15}")
for r in (1, 2, 3, 4, 5, 10, 20, 50, 100, 500):
    if r <= Vd:
        w, c = freq[r-1]
        print(f"   {r:>5}{w:>12}{c:>7}{r*c:>14}{c/N*100:>14.1f}%")
print("   rank x count hovers around a constant: that is Zipf's law. the 2nd word is")
print("   about half as common as the 1st, the 10th about a tenth, and so on.")

print("\n=== the head is tiny and the tail is enormous ===")
cum = 0
for k in (10, 100, 500):
    cum_k = sum(c for _, c in freq[:k])
    print(f"   top {k:>4} words cover {cum_k/N*100:5.1f}% of all text")
once = sum(1 for _, c in freq if c == 1)
lt5  = sum(1 for _, c in freq if c < 5)
print(f"   words seen exactly once: {once:,} of {Vd:,} distinct ({once/Vd*100:.0f}%)")
print(f"   words seen fewer than 5 times: {lt5:,} ({lt5/Vd*100:.0f}%)")

print("\n=== on log-log axes it is a straight line ===")
print(f"   {'log10 rank':>12}{'log10 count':>13}")
for r in (1, 10, 100, 1000):
    if r <= Vd:
        print(f"   {math.log10(r):>12.2f}{math.log10(freq[r-1][1]):>13.2f}")
print("   each 10x in rank costs roughly one unit of log10 count: slope about -1.")
print("   (chapter 06 owns the general power-law maths; this is the linguistic instance.)")

print("\n=== why this matters for training ===")
print("   a token's embedding is updated once per occurrence. the token at rank 1 got")
print(f"   {freq[0][1]:,} updates from this document; a rank-1000 token got {freq[min(999, Vd-1)][1]}.")
print("   half the vocabulary is essentially untrained on any given corpus. subword")
print("   tokenization (chapter 01) exists partly to pool that signal.")
