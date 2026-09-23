import re, collections
CORPUS = ("the tokenizer tokenizes text into tokens and the token is not a word\n"
          "a tokenizer is a table and the tokens index that table\n") * 8

def train(chunks, n):
    words=[tuple(bytes([b]) for b in w.encode()) for w in chunks]
    vocab={i:bytes([i]) for i in range(256)}; merges={}
    for step in range(n):
        p=collections.Counter()
        for w in words:
            for a,b in zip(w,w[1:]): p[(a,b)]+=1
        if not p: break
        (a,b),_=p.most_common(1)[0]; nid=256+step; vocab[nid]=a+b; merges[(a,b)]=nid
        out=[]
        for w in words:
            i,nw=0,[]
            while i<len(w):
                if i+1<len(w) and (w[i],w[i+1])==(a,b): nw.append(a+b); i+=2
                else: nw.append(w[i]); i+=1
            out.append(tuple(nw))
        words=out
    return vocab, merges

GPT2ish = re.compile(r" ?[a-zA-Z]+|[^a-zA-Z]")
for label, chunks in [
        ("WITH pre-splitting  (regex ' ?[a-zA-Z]+|[^a-zA-Z]')", GPT2ish.findall(CORPUS)),
        ("WITHOUT pre-splitting (whole lines as one chunk)   ", CORPUS.split('\n'))]:
    vocab, _ = train(chunks, 40)
    multi = [v for k,v in vocab.items() if k>=256 and b' ' in v.strip(b' ')]
    print(f"\n{label}")
    print(f"  merge entries containing an INTERNAL space: {len(multi)}")
    for v in multi[:8]: print(f"     {v!r}")
    longest = sorted((v for k,v in vocab.items() if k>=256), key=len)[-3:]
    print(f"  longest merged entries: {[repr(x) for x in longest]}")

print("\n--- whitespace runs DO merge (code indentation) ---")
code = ("def f():\n    if x:\n        return 1\n    return 0\n")*20
chunks = re.compile(r" ?[a-zA-Z]+|\s+|[^\sa-zA-Z]").findall(code)
vocab,_ = train(chunks, 25)
ws = [v for k,v in vocab.items() if k>=256 and v.strip()==b'']
print(f"  pure-whitespace tokens learned: {[repr(x) for x in ws]}")
