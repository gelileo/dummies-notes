import re, collections, sys
SPLIT = re.compile(r" ?[A-Za-z]+|[^A-Za-z]")
text = open(sys.argv[1]).read()
toks = SPLIT.findall(text)
print(f"corpus: {len(text)} chars, {len(toks)} pre-split chunks, {len(text.encode())} bytes")

words = [tuple(bytes([b]) for b in w.encode()) for w in toks]
vocab = {i: bytes([i]) for i in range(256)}
merges = {}
N = 600
curve = {}
trace_word = b' tokenizer'
trace = []

for step in range(N):
    pairs = collections.Counter()
    for w in words:
        for a, b in zip(w, w[1:]): pairs[(a,b)] += 1
    if not pairs:
        print(f"\n!! ran out of pairs at merge {step}"); break
    (a,b), cnt = pairs.most_common(1)[0]
    total_before = sum(len(w) for w in words)
    if step in (0,1,2,5,10,20,50,100,200,300,400,500) : curve[step] = total_before
    nid = 256+step; vocab[nid] = a+b; merges[(a,b)] = nid
    out=[]
    for w in words:
        i,nw = 0,[]
        while i < len(w):
            if i+1 < len(w) and (w[i],w[i+1])==(a,b): nw.append(a+b); i+=2
            else: nw.append(w[i]); i+=1
        out.append(tuple(nw))
    words = out
    if a+b in trace_word or trace_word.startswith(a+b):
        trace.append((step, nid, a, b, cnt))
curve[N] = sum(len(w) for w in words)

print(f"\n=== compression curve (total tokens for the whole corpus) ===")
base = curve[0]
prev=None
for k in sorted(curve):
    v=curve[k]; 
    marg = f"{(prev-v)/max(1,(k-pk)):8.1f}" if prev else "       -"
    print(f"  after {k:>4} merges: {v:>7} tokens   ({v/base*100:5.1f}% of byte-level)   avg tokens saved per merge since last row: {marg}")
    prev, pk = v, k

print(f"\n=== merges that built b' tokenizer' ===")
for step,nid,a,b,cnt in trace: print(f"  merge {step:>3} -> id {nid:>4}: {a!r} + {b!r} = {(a+b)!r}  ({cnt} occurrences)")

# --- encoding: replay merges in learned order ---
def encode_trace(word):
    parts=[bytes([x]) for x in word.encode()]
    print(f"\n=== encoding {word!r} — replaying the merge list in order ===")
    print(f"  start: {[p.decode('utf8','replace') for p in parts]}")
    while True:
        cand=[(merges[p],i) for i,p in enumerate(zip(parts,parts[1:])) if p in merges]
        if not cand: break
        mid,i = min(cand)
        pair=(parts[i],parts[i+1]); parts[i:i+2]=[parts[i]+parts[i+1]]
        print(f"  apply merge id {mid:>4} ({pair[0]!r}+{pair[1]!r}): {[p.decode('utf8','replace') for p in parts]}")
    print(f"  done: no pair left in the merge table -> {len(parts)} tokens")
    return parts
encode_trace(" tokenizer")
encode_trace(" retokenizing")

# --- does greedy longest-match differ from merge-order replay? ---
def longest_first(word):
    parts=[bytes([x]) for x in word.encode()]
    while True:
        best=None
        for i,p in enumerate(zip(parts,parts[1:])):
            if p in merges:
                L=len(p[0])+len(p[1])
                if best is None or L>best[0]: best=(L,i)
        if not best: break
        i=best[1]; parts[i:i+2]=[parts[i]+parts[i+1]]
    return parts
def ordered(word):
    parts=[bytes([x]) for x in word.encode()]
    while True:
        cand=[(merges[p],i) for i,p in enumerate(zip(parts,parts[1:])) if p in merges]
        if not cand: break
        _,i=min(cand); parts[i:i+2]=[parts[i]+parts[i+1]]
    return parts
print("\n=== does merge-order matter? searching for disagreements ===")
seen=set(); diffs=0
for w in toks:
    if w in seen: continue
    seen.add(w)
    a,b = ordered(w), longest_first(w)
    if a!=b:
        diffs+=1
        if diffs<=4:
            print(f"  {w!r}")
            print(f"     merge-order : {[x.decode('utf8','replace') for x in a]}  ({len(a)} tokens)")
            print(f"     longest-first: {[x.decode('utf8','replace') for x in b]}  ({len(b)} tokens)")
print(f"  total distinct chunks differing: {diffs} / {len(seen)}")
