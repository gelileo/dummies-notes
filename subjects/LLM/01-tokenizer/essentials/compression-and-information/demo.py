#!/usr/bin/env python3
"""Frequent things get short codes: Huffman coding, and why BPE is the same idea applied to
strings. Measured on the curriculum's own field guide. Standard library. Run: python3 demo.py"""
import heapq, collections, math, os, re

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "twelve-ideas-behind-modern-ai.md")
text = open(path, encoding="utf-8").read()
data = text.encode("utf-8"); N = len(data)
print(f"corpus: the field guide, {N:,} bytes\n")

print("=== 1. a fixed-width code: every byte costs 8 bits ===")
print(f"   {N:,} bytes x 8 = {N*8:,} bits.  8.000 bits per byte. this is the baseline.")

print("\n=== 2. the floor: the entropy of the byte distribution (chapter 03) ===")
cnt = collections.Counter(data)
H = -sum(c/N * math.log2(c/N) for c in cnt.values())
print(f"   {len(cnt)} distinct byte values. entropy = {H:.3f} bits per byte.")
print("   no code that assigns one codeword per byte can average fewer bits than this.")

print("\n=== 3. Huffman: give frequent bytes short codes ===")
heap = [[c, [b, ""]] for b, c in cnt.items()]; heapq.heapify(heap)
while len(heap) > 1:
    lo = heapq.heappop(heap); hi = heapq.heappop(heap)
    for pair in lo[1:]: pair[1] = "0" + pair[1]
    for pair in hi[1:]: pair[1] = "1" + pair[1]
    heapq.heappush(heap, [lo[0] + hi[0]] + lo[1:] + hi[1:])
code = {b: c for b, c in heap[0][1:]}
bits = sum(cnt[b] * len(code[b]) for b in cnt)
print(f"   {'byte':>6}{'count':>8}{'code length':>13}   code")
for b, c in cnt.most_common(4) + cnt.most_common()[-2:]:
    print(f"   {repr(chr(b)):>6}{c:>8}{len(code[b]):>13}   {code[b]}")
print(f"   total {bits:,} bits = {bits/N:.3f} bits per byte   (entropy floor {H:.3f}; fixed width 8.000)")
print("   the most common byte gets a 3-bit code; the rarest get 15+. that is the whole idea.")

print("\n=== 4. BPE is the same idea, one level up: frequent STRINGS get single tokens ===")
SPLIT = re.compile(r" ?[A-Za-z]+|[^A-Za-z]")
def train_bpe(chunks, n):
    words = [tuple(bytes([b]) for b in w.encode()) for w in chunks]; merges = 0
    for _ in range(n):
        pairs = collections.Counter()
        for w in words:
            for a, b in zip(w, w[1:]): pairs[(a, b)] += 1
        if not pairs: break
        (a, b), _ = pairs.most_common(1)[0]; merges += 1
        out = []
        for w in words:
            i, nw = 0, []
            while i < len(w):
                if i + 1 < len(w) and (w[i], w[i+1]) == (a, b): nw.append(a + b); i += 2
                else: nw.append(w[i]); i += 1
            out.append(tuple(nw))
        words = out
    return sum(len(w) for w in words), 256 + merges
chunks = SPLIT.findall(text)
print(f"   {'merges':>7}{'tokens':>9}{'vocab':>7}{'bits/token':>11}{'total bits':>13}{'bits per byte':>15}")
for n in (0, 24, 100, 300):
    toks, V = train_bpe(chunks, n)
    bpt = math.log2(V); total = toks * bpt
    print(f"   {n:>7}{toks:>9,}{V:>7}{bpt:>11.2f}{total:>13,.0f}{total/N:>15.3f}")
print("   more merges: fewer tokens, each costing a little more to name. the product falls below")
print("   Huffman's per-byte code because a token captures a whole frequent string at once.")
print("   (this uses a fixed log2(vocab) bits per token; a real compressor would Huffman-code the")
print("    tokens too and do better still.)")

print("\n=== 5. the through-line to the training loss ===")
print("   chapter 03 measures a model in bits per token. a model that predicts well IS a good code:")
print("   assign -log2 p bits to each token and the total is the compressed size. tokenizer, Huffman,")
print("   language model -- three rungs of one ladder: frequent things should be cheap to write down.")
