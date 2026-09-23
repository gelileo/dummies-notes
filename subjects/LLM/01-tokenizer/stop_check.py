import re, collections
SPLIT = re.compile(r" ?[A-Za-z]+|[^A-Za-z]")
text = open('../twelve-ideas-behind-modern-ai.md').read()
words = [tuple(bytes([b]) for b in w.encode()) for w in SPLIT.findall(text)]
vocab = {i: bytes([i]) for i in range(256)}; merges = {}
for step in range(600):
    pairs = collections.Counter()
    for w in words:
        for a,b in zip(w,w[1:]): pairs[(a,b)] += 1
    if not pairs: break
    (a,b),_ = pairs.most_common(1)[0]
    nid = 256+step; vocab[nid]=a+b; merges[(a,b)]=nid
    words = [tuple(x for x in _apply(w,a,b)) for w in words] if False else [
        tuple((lambda w: [ (w[i],) for i in range(0)] )(w)) for w in []] or words
    out=[]
    for w in words:
        i,nw=0,[]
        while i<len(w):
            if i+1<len(w) and (w[i],w[i+1])==(a,b): nw.append(a+b); i+=2
            else: nw.append(w[i]); i+=1
        out.append(tuple(nw))
    words=out

def enc(s):
    parts=[bytes([x]) for x in s.encode()]
    while True:
        c=[(merges[p],i) for i,p in enumerate(zip(parts,parts[1:])) if p in merges]
        if not c: break
        _,i=min(c); parts[i:i+2]=[parts[i]+parts[i+1]]
    return parts

byte_str_to_id = {v:k for k,v in vocab.items()}
V = len(vocab)
print(f"vocabulary entries (id -> byte string): {V}")
print(f"merge table entries (pair -> id)      : {len(merges)}")
print(f"possible adjacent pairs over V tokens : {V*V:,}")
print(f"fraction of pairs that ARE merges     : {len(merges)/(V*V)*100:.4f}%\n")

for s in [" tokenizer", " engineers", " the model"]:
    parts = enc(s)
    print(f"final state of {s!r}: {[p.decode() for p in parts]}")
    for i in range(len(parts)-1):
        a,b = parts[i], parts[i+1]
        print(f"   pair {i}: ({a.decode()!r:<10}, {b.decode()!r:<6})"
              f"  A in vocab? {'yes':>3} (id {byte_str_to_id[a]:>4})"
              f"   B in vocab? {'yes':>3} (id {byte_str_to_id[b]:>4})"
              f"   PAIR in merge table? {'YES id %d' % merges[(a,b)] if (a,b) in merges else 'no  -> cannot merge'}")
    print(f"   -> no pair is a merge key: STOP, {len(parts)} tokens\n")

# the same word under a tokenizer trained on a different corpus
print("same word, tokenizer trained on a tokenizer-heavy corpus (minibpe_demo.py, 30 merges):")
print("   ' tokenizer' -> [' tokenizer']  (1 token; the pair (' tokenize','r') WAS merged there)")
print("same word, this tokenizer (600 merges on the guide):")
print(f"   ' tokenizer' -> {[p.decode() for p in enc(' tokenizer')]}  (the pair (' token','iz') was never merged here)")
