#!/usr/bin/env python3
"""A pretraining data pipeline on a corpus small enough to read, plus a measurement of
what the pipeline buys: the same bigram model trained on raw vs cleaned data, scored on
clean held-out text.

Run: python3 data_pipeline.py
"""
import hashlib, math, random, collections, re
random.seed(0)

# ------------------------------------------------------------------ a tiny "crawl"
GOOD = [
 "the river runs through the valley and the farmers water their fields from it",
 "she opened the letter and read it twice before she understood what it meant",
 "a good map shows the roads and the rivers but not every stone along the way",
 "the baker rises before dawn and the bread is warm when the shop opens",
 "we walked along the shore and watched the boats come back with the tide",
 "the old clock in the hall has kept time for a hundred years without fail",
 "every autumn the leaves turn and the hills look like they are on fire",
 "he fixed the fence and then sat on the porch until the light was gone",
]
BOILER  = "click here to subscribe accept cookies privacy policy terms of service login"
SPAM    = "buy now buy now best price best price free free free click click click"
CODEISH = "def f(x): return x*x  #  TODO fix  {{ }} ;; == != <> [] [] []"
FOREIGN = "el río corre por el valle y los granjeros riegan sus campos con su agua"
BENCH   = "the baker rises before dawn and the bread is warm when the shop opens"   # a 'test set' item

raw = []
raw += [("web", d) for d in GOOD]
raw += [("web", BOILER)] * 6                      # boilerplate, repeated across pages
raw += [("web", SPAM)] * 3
raw += [("web", GOOD[0])] * 4                     # exact duplicates of a good doc
raw += [("web", GOOD[1].replace("twice", "three times"))]   # a near-duplicate
raw += [("web", FOREIGN)]
raw += [("code", CODEISH)] * 2
raw += [("books", "in the beginning the house was quiet and the garden was full of birds")]
raw += [("books", "the road bent twice and then ran straight toward the distant hills")]
random.shuffle(raw)

def toks(d): return d.split()
def n_tokens(docs): return sum(len(toks(d)) for _, d in docs)
STOP = set("the a and of to in is it that was for on with as he she we they".split())

def show(stage, docs, removed):
    print(f"   {stage:<28} {len(docs):>3} docs {n_tokens(docs):>5} tokens   removed: {removed}")

# ------------------------------------------------------------------ 1. language id
def is_english(d):
    """Non-ASCII letters -> another language. (Real pipelines use a trained classifier
    over character n-grams; the principle is the same: does this look like English?)"""
    return all(ord(c) < 128 for c in d)
# ------------------------------------------------------------------ 2. quality classifier
# Real pipelines train a classifier: 'reference text we trust' vs 'random crawl'. This is
# the smallest honest version -- the reference sets are NOT in the crawl.
REF_GOOD = ["the children ran across the field while their mother called them home for supper",
            "he closed the book and looked out of the window at the rain on the street",
            "the town sits where two rivers meet and the market is held there every week",
            "when the storm passed the roof was gone but the family was safe in the cellar"]
REF_BAD  = ["subscribe to our newsletter accept all cookies manage preferences",
            "limited time offer buy now free shipping best price guaranteed",
            "sign up login register forgot password terms conditions privacy",
            "click here read more click here learn more click here"]
GOOD_V = {w for d in REF_GOOD for w in d.split()} - STOP
BAD_V  = {w for d in REF_BAD for w in d.split()} - STOP
def quality(d):
    """Prose has dense function words and little repetition; junk has a distinctive
    vocabulary (learned from REF_BAD) and repeats itself. Positive = looks like prose."""
    w = toks(d)
    stop = sum(t in STOP for t in w) / len(w)
    bad = sum(t in BAD_V for t in w) / len(w)
    repeat = 1 - len(set(w)) / len(w)
    return stop - 2*bad - repeat
# ------------------------------------------------------------------ 3. dedup
def exact_key(d): return hashlib.sha1(d.encode()).hexdigest()
def shingles(d, k=3):
    w = toks(d); return {" ".join(w[i:i+k]) for i in range(len(w)-k+1)}
def jaccard(a, b): return len(a & b) / len(a | b) if a | b else 0.0
def minhash(sh, n=64):
    return [min(int(hashlib.md5(f"{i}:{s}".encode()).hexdigest(), 16) for s in sh) for i in range(n)]
def minhash_sim(h1, h2): return sum(a == b for a, b in zip(h1, h2)) / len(h1)

def run_pipeline(docs):
    """Returns a list of (stage name, surviving docs, what was removed)."""
    stages = [("raw crawl", docs[:], "-")]
    code = [(s, d) for s, d in docs if s == "code"]          # code gets its own filters; skip these
    text = [(s, d) for s, d in docs if s != "code"]
    kept = [(s, d) for s, d in text if is_english(d)]
    stages.append(("language filter", kept + code, f"{len(text)-len(kept)} non-English")); text = kept
    kept = [(s, d) for s, d in text if quality(d) > 0.0]
    stages.append(("quality classifier", kept + code, f"{len(text)-len(kept)} scored as junk")); docs = kept + code
    seen = set(); kept = []
    for s, d in docs:
        k = exact_key(d)
        if k not in seen: seen.add(k); kept.append((s, d))
    stages.append(("exact dedup (hash)", kept, f"{len(docs)-len(kept)} identical copies")); docs = kept
    kept, sigs = [], []
    for s, d in docs:
        h = minhash(shingles(d))
        if any(minhash_sim(h, h2) >= 0.5 for h2 in sigs): continue      # threshold is a knob
        sigs.append(h); kept.append((s, d))
    stages.append(("near-dedup (MinHash)", kept, f"{len(docs)-len(kept)} near-duplicate"))
    return stages

def decontaminate(docs, bench, k=8):
    bsh = shingles(bench, k)
    hits = [(s, d) for s, d in docs if shingles(d, k) & bsh]
    return [x for x in docs if x not in hits], hits

def bigram_loss(train_docs, test_docs, alpha=0.1):
    cnt = collections.defaultdict(collections.Counter); vocab = set()
    for _, d in train_docs:
        w = ["<s>"] + toks(d); vocab.update(w)
        for p_, n_ in zip(w, w[1:]): cnt[p_][n_] += 1
    for d in test_docs: vocab.update(toks(d))
    V = len(vocab); tot = 0; n = 0
    for d in test_docs:
        w = ["<s>"] + toks(d)
        for p_, n_ in zip(w, w[1:]):
            row = cnt.get(p_, {}); tot += -math.log((row.get(n_, 0) + alpha) / (sum(row.values()) + alpha*V)); n += 1
    return tot / n

HELDOUT = ["the farmer walked along the river and watched the water run toward the hills",
           "she read the letter by the old clock and the house was quiet"]

if __name__ == "__main__":
    print("=== the pipeline: raw crawl -> training set ===")
    stages = run_pipeline(raw)
    for name, docs, removed in stages: show(name, docs, removed)
    clean = stages[-1][1]

    print("\n=== 2. the quality classifier: trusted-text words minus junk words ===")
    for label, d in (("good prose", GOOD[2]), ("good prose", GOOD[5]), ("boilerplate", BOILER), ("spam", SPAM)):
        print(f"   {label:<12} score {quality(d):+.3f}   '{d[:48]}...'")
    print("   the reference sets never saw these documents, yet the sign separates them.")
    print("   real pipelines do exactly this with a FastText classifier trained on")
    print("   Wikipedia-like text vs random crawl -- and every such filter is a bias chosen.")

    print("\n=== 3. near-duplicates: exact Jaccard vs the MinHash estimate ===")
    a, b = shingles(GOOD[1]), shingles(GOOD[1].replace("twice", "three times"))
    c = shingles(GOOD[3])
    ha, hb, hc = minhash(a), minhash(b), minhash(c)
    print(f"   near-dup pair   Jaccard {jaccard(a,b):.3f}   MinHash estimate {minhash_sim(ha,hb):.3f}")
    print(f"   unrelated pair  Jaccard {jaccard(a,c):.3f}   MinHash estimate {minhash_sim(ha,hc):.3f}")
    print("   64 hashes stand in for the whole shingle set; comparing docs becomes comparing")
    print("   64-number signatures. that is what makes dedup at trillions of tokens possible.")

    print("\n=== 4. mixture weights: how much of each source? ===")
    by_src = collections.Counter(s for s, _ in clean)
    tok_src = collections.Counter(); 
    for s, d in clean: tok_src[s] += len(toks(d))
    total = sum(tok_src.values())
    print(f"   {'source':<8}{'docs':>6}{'tokens':>8}{'natural share':>15}{'chosen weight':>15}{'tokens sampled':>16}")
    weights = {"web": 0.6, "books": 0.3, "code": 0.1}
    budget = 200
    for s in ("web", "books", "code"):
        nat = tok_src[s] / total
        print(f"   {s:<8}{by_src[s]:>6}{tok_src[s]:>8}{nat:>15.2f}{weights.get(s,0):>15.2f}{weights.get(s,0)*budget:>16.0f}")
    for s in ("books", "code"):
        if tok_src[s]:
            print(f"   {s}: sampling {weights[s]*budget:.0f} tokens from {tok_src[s]} available = {weights[s]*budget/tok_src[s]:.1f} epochs (up-sampled)")
    print("   'weight' is a decision, not a measurement. it overrides the crawl's natural mix.")

    print("\n=== 5. contamination: is the benchmark in the training set? ===")
    clean, hits = decontaminate(clean, BENCH)
    print(f"   benchmark item: '{BENCH[:50]}...'")
    print(f"   8-gram overlap with {len(hits)} training doc(s) -> {'CONTAMINATED: remove it' if hits else 'clean'}")
    print(f"   after decontamination: {len(clean)} docs")

    print("\n=== 6. what the pipeline buys: same model, raw vs clean, scored on clean held-out ===")
    lr, lc = bigram_loss(raw, HELDOUT), bigram_loss(clean, HELDOUT)
    print(f"   trained on raw crawl   ({n_tokens(raw):>4} tokens): held-out loss {lr:.3f} nats")
    print(f"   trained on clean set   ({n_tokens(clean):>4} tokens): held-out loss {lc:.3f} nats")
    verdict = "lower" if lc < lr else "HIGHER"
    print(f"   -> {n_tokens(raw)/n_tokens(clean):.1f}x fewer tokens, {abs(1-lc/lr)*100:.0f}% {verdict} loss.")
    if lc < lr:
        print("      the duplicates and boilerplate were not just useless -- they skewed the")
        print("      counts toward junk. less data, better model.")

    print("\n=== 7. the long tail ===")
    print("   see essentials/zipf-and-the-long-tail -- measured on a 10,000-word document,")
    print("   because 155 tokens is too few to show the shape. the punchline: about half")
    print("   of all distinct words appear exactly once, so most tokens are barely trained.")
