#!/usr/bin/env python3
"""Context and knowledge, measured on real text: the curriculum's own 67KB field guide is the
corpus. Chunk it, index it two ways (BM25 keyword and TF-IDF cosine), ask real questions, and
watch what comes back; then the arithmetic of long context vs retrieval, and why RoPE can be
stretched. numpy.  Run: python3 retrieval.py
"""
import numpy as np, re, math, os, collections
rng = np.random.default_rng(0)

DOC = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "twelve-ideas-behind-modern-ai.md"), encoding="utf-8").read()
STOP = set("the a an and of to in is it that was for on with as by this are be or from at which".split())
def stem(w):
    """A crude stemmer: strip common suffixes so 'dividing', 'divides', 'divided' -> 'divid'."""
    for suf in ("ing", "ers", "ies", "es", "ed", "ly", "s"):
        if len(w) > len(suf) + 3 and w.endswith(suf): return w[:-len(suf)]
    return w
def tokens(s): return [stem(w) for w in re.findall(r"[a-z0-9√]+", s.lower()) if w not in STOP]

# ------------------------------------------------------------------ chunking
def chunk(text, size=120, overlap=30):
    words = text.split(); out = []; i = 0
    while i < len(words):
        out.append(" ".join(words[i:i+size])); i += size - overlap
    return out

# ------------------------------------------------------------------ two indexes
class BM25:
    def __init__(self, chunks, k1=1.5, b=0.75):
        self.docs = [tokens(c) for c in chunks]; self.N = len(chunks)
        self.avgdl = np.mean([len(d) for d in self.docs]); self.k1, self.b = k1, b
        df = collections.Counter(t for d in self.docs for t in set(d))
        self.idf = {t: math.log(1 + (self.N - n + 0.5) / (n + 0.5)) for t, n in df.items()}
    def score(self, q):
        qt = tokens(q); s = np.zeros(self.N)
        for i, d in enumerate(self.docs):
            tf = collections.Counter(d); dl = len(d)
            for t in qt:
                if t in tf:
                    s[i] += self.idf[t] * tf[t] * (self.k1 + 1) / (tf[t] + self.k1 * (1 - self.b + self.b * dl / self.avgdl))
        return s

class TFIDFCosine:
    """A bag-of-words 'embedding': each chunk is a vector over the vocabulary, weighted by tf-idf.
    A stand-in for a learned embedding model -- same geometry (cosine), no training."""
    def __init__(self, chunks):
        self.vocab = sorted({t for c in chunks for t in tokens(c)}); self.ix = {t: i for i, t in enumerate(self.vocab)}
        df = collections.Counter(t for c in chunks for t in set(tokens(c))); N = len(chunks)
        self.idf = np.array([math.log(N / df[t]) + 1 for t in self.vocab])
        self.M = np.stack([self.embed(c) for c in chunks])
    def embed(self, text):
        v = np.zeros(len(self.vocab))
        for t in tokens(text):
            if t in self.ix: v[self.ix[t]] += 1
        v = v * self.idf; n = np.linalg.norm(v); return v / n if n else v
    def score(self, q): return self.M @ self.embed(q)

def top(scores, k=3): return np.argsort(-scores)[:k]

if __name__ == "__main__":
    chunks = chunk(DOC)
    print(f"corpus: the field guide, {len(DOC.split()):,} words -> {len(chunks)} chunks of ~120 words (30 overlap)\n")
    bm, tf = BM25(chunks), TFIDFCosine(chunks)

    print("=== 1. ask real questions; where does the right chunk rank? ===")
    # (question, a string that marks the chunk(s) that actually answer it)
    QS = [("why divide attention scores by the square root of the dimension", "√d"),
          ("how many tokens per parameter did Chinchilla recommend", "20 tokens"),
          ("what does the KV cache store and why is GQA used", "KV cache")]
    def rank_of(scores, marker):
        order = np.argsort(-scores)
        return next((r+1 for r, i in enumerate(order) if marker in chunks[i]), None)
    print(f"   {'question':<62}{'BM25 rank':>10}{'TF-IDF rank':>12}")
    for q, marker in QS:
        print(f"   {q:<62}{rank_of(bm.score(q), marker):>10}{rank_of(tf.score(q), marker):>12}")
    q, marker = QS[0]; i = top(bm.score(q), 1)[0]
    print(f"\n   BM25's top hit for the first question (chunk {i}): {chunks[i][:100]}...")
    print("   rank 1 = the answering chunk is the top hit. the retrieved chunks go into the prompt and")
    print("   the model answers from them -- that is retrieval-augmented generation, in full. note that")
    print("   ranks above 3 mean a top-3 retriever MISSES: retrieval failures are silent.")

    print("\n=== 2. keyword vs meaning: where bag-of-words retrieval strains ===")
    q = "making the model cheaper to run on a graphics card"
    print(f"   Q: {q}")
    print(f"   the answering section (hardware co-design) says 'efficiency', 'quantization', 'GPU' -- none of the query's words.")
    for name, idx in (("BM25 ", bm), ("TFIDF", tf)):
        i = top(idx.score(q), 1)[0]
        print(f"   {name} top hit (chunk {i:>3}): {chunks[i][:100]}...")
    print(f"   rank of the hardware section under BM25: {rank_of(bm.score(q), 'co-design')}   under TF-IDF: {rank_of(tf.score(q), 'co-design')}")
    print("   the top hit is wrong for both, and the answering section survives only at rank 2 on")
    print("   incidental word overlap. a top-1 retriever misses; top-3 catches it by luck. this is the")
    print("   gap a LEARNED embedding model closes: trained so that 'cheaper to run' lands near")
    print("   'efficiency' and 'quantization' (chapter 02's geometry, with training). production systems")
    print("   run both keyword and embedding retrieval (hybrid) and rerank the union with a cross-encoder.")

    print("\n=== 3. chunk size is a real knob ===")
    q, _ = QS[0]
    print(f"   Q: {q}")
    print(f"   {'chunk words':>12}{'chunks':>8}{'answering chunk rank':>32}{'words retrieved (top-3)':>26}")
    for size in (40, 120, 400):
        ch = chunk(DOC, size, size//4); idx = BM25(ch); sc = idx.score(q); order = np.argsort(-sc)
        rk = next((r+1 for r, i in enumerate(order) if "√d" in ch[i]), None)
        print(f"   {size:>12}{len(ch):>8}{str(rk):>32}{sum(len(ch[i].split()) for i in order[:3]):>26}")
    print("   small chunks: precise hits, little context around them. big chunks: the answer is in")
    print("   there somewhere, with a lot of padding the model must read past. 100-300 words with")
    print("   overlap is the usual compromise; structure-aware splitting (by heading) does better.")

    print("\n=== 4. long context vs retrieval: the arithmetic ===")
    doc_tokens = int(len(DOC.split()) * 1.3)          # ~1.3 tokens per word
    for calls in (1, 100, 10_000):
        print(f"   {calls:>6} question(s): stuff the whole guide ({doc_tokens:,} tok) = {doc_tokens*calls:>12,} input tokens;"
              f"  retrieve 3 chunks (~{3*120*1.3:.0f} tok) = {int(3*120*1.3)*calls:>10,}")
    print("   at one question, stuffing is simpler and cannot miss. at ten thousand, retrieval is")
    print("   ~30x cheaper. prefix caching narrows the gap when the stuffed document is shared.")
    print("   and a 500-page manual does not fit in any window: retrieval is the only option there.")

    print("\n=== 5. why long context is hard (chapter 02/10 recap, with numbers) ===")
    for T in (8_192, 128_000, 1_000_000):
        kv = 2*32*8*128*2*T
        print(f"   T={T:>9,}: attention scores per layer {T*T:>16,} -- KV cache (Llama-3-8B) {kv/1e9:>7.1f} GB per sequence")
    print("   quadratic attention (tiled away by FlashAttention) and linear cache (not away-able).")

    print("\n=== 6. RoPE can be stretched: position is an angle ===")
    d = 128; theta = 1.0 / (10000 ** (np.arange(0, d, 2) / d))
    def dot_at_distance(dist, scale=1.0):
        # unit query and key with identical content; rotate by positions 0 and dist (scaled); average cosine
        ang = theta * dist / scale
        return np.mean(np.cos(ang))
    print(f"   {'distance':>9}{'trained (scale 1)':>19}{'stretched 4x':>14}")
    for dist in (1, 100, 1000, 8000, 32000):
        print(f"   {dist:>9,}{dot_at_distance(dist):>19.3f}{dot_at_distance(dist, 4.0):>14.3f}")
    print("   a model trained to 8k has only seen angles up to theta*8000. at 32k the fast pairs")
    print("   have spun into territory it never saw. divide all positions by 4 (position interpolation)")
    print("   and 32k looks like 8k did -- then a short fine-tune on long documents settles it.")
    print("   NTK-aware scaling and YaRN stretch the slow and fast frequencies differently.")

    print("\n=== 7. brute-force vs approximate nearest neighbour ===")
    for n in (1_000, 1_000_000, 1_000_000_000):
        print(f"   {n:>14,} vectors x 1024 dims: one query = {n*1024:>16,} multiply-adds brute force")
    print("   a billion-vector index cannot be scanned per query. HNSW/IVF visit ~0.1% of it and")
    print("   return near-exact neighbours -- see essentials/nearest-neighbour-search.")
