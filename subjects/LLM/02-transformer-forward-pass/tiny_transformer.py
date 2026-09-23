#!/usr/bin/env python3
"""One Transformer block, forward pass only, in pure Python. No dependencies.

Everything is tiny and printable: d_model=8, 2 heads, 6 tokens. The weights are
hand-set rather than trained, so the attention pattern is legible -- 'it' is given
an embedding that points mostly at 'trophy', and you can watch attention find it.

Run:  python3 tiny_transformer.py
"""
import math

# ---------------------------------------------------------------- config
VOCAB   = ["the", "trophy", "did", "not", "fit", "it"]
D_MODEL = 8
N_HEADS = 2
D_HEAD  = D_MODEL // N_HEADS      # 4
D_MLP   = 16                       # real models use ~4x d_model
SEQ     = len(VOCAB)

# ------------------------------------------------------- tiny linear algebra
def zeros(r, c):        return [[0.0]*c for _ in range(r)]
def matmul(A, B):
    """[n x k] @ [k x m] -> [n x m].  The nested loop IS the lesson."""
    n, k, m = len(A), len(B), len(B[0])
    out = zeros(n, m)
    for i in range(n):
        for j in range(m):
            s = 0.0
            for p in range(k):
                s += A[i][p] * B[p][j]
            out[i][j] = s
    return out
def dot(a, b):          return sum(x*y for x, y in zip(a, b))
def add(A, B):          return [[x+y for x, y in zip(ra, rb)] for ra, rb in zip(A, B)]
def transpose(A):       return [list(col) for col in zip(*A)]

def softmax(v):
    m = max(v)                       # subtract the max: same result, no overflow
    e = [math.exp(x - m) for x in v]
    s = sum(e)
    return [x/s for x in e]

def rmsnorm(row, gain):
    """Scale a vector to unit root-mean-square, then apply a learned per-dim gain."""
    rms = math.sqrt(sum(x*x for x in row)/len(row) + 1e-6)
    return [x/rms*g for x, g in zip(row, gain)]

def silu(x):            return x / (1.0 + math.exp(-x))

# ------------------------------------------------------------ hand-set weights
# Each of the 8 dimensions is given a meaning so the vectors stay readable.
# Head 0 sees dims 0-3, head 1 sees dims 4-7.
#   dim 0 'the'   1 'trophy'   2 'did'   3 'not'        <- head 0
#   dim 4 SINK    5 'fit'      6 'it'    7 always-on    <- head 1
EMBED = {
    #          0  1  2  3    4  5  6    7
    "the":    [1, 0, 0, 0,   2, 0, 0,   1],   # dim4=2: the "sink" every token can look at
    "trophy": [0, 1, 0, 0,   0, 0, 0,   1],
    "did":    [0, 0, 1, 0,   0, 0, 0,   1],
    "not":    [0, 0, 0, 1,   0, 0, 0,   1],
    "fit":    [0, 0, 0, 0,   0, 1, 0,   1],
    "it":     [0, 0, 0, 0,   0, 0, 1,   1],   # 'it' is ONLY itself -- see W_Q below
}

def eye_block(n, m, scale=1.0):
    """An n x m matrix with a scaled diagonal -- a 'pass it through' projection."""
    M = zeros(n, m)
    for i in range(min(n, m)):
        M[i][i] = scale
    return M

# W_K is the identity: a token's key is simply what it contains.
W_K = eye_block(D_MODEL, D_MODEL)

# W_Q is where the interesting behaviour lives, because a query is a DIFFERENT
# projection of the same vector: not "what I am" but "what I am looking for".
W_Q = eye_block(D_MODEL, D_MODEL)
W_Q[6][6] = 0.0; W_Q[6][1] = 1.0   # head 0: 'it' stops querying itself and asks for 'trophy'
W_Q[4][4] = 0.0                     # head 1: don't let the sink token query the sink twice
W_Q[7][7] = 0.0; W_Q[7][4] = 1.0   # head 1: the always-on dim makes EVERY token query the sink
W_V = eye_block(D_MODEL, D_MODEL)
W_O = eye_block(D_MODEL, D_MODEL)
NORM1_GAIN = [1.0]*D_MODEL
NORM2_GAIN = [1.0]*D_MODEL
NORMF_GAIN = [1.0]*D_MODEL
# The LM head is the embedding table transposed -- "weight tying". One matrix does
# double duty: id -> vector on the way in, vector -> score per id on the way out.
W_LM = transpose([EMBED[w] for w in VOCAB])          # [D_MODEL, VOCAB]
W_UP   = eye_block(D_MODEL, D_MLP, 0.5)
W_GATE = eye_block(D_MODEL, D_MLP, 0.5)
W_DOWN = eye_block(D_MLP, D_MODEL, 0.5)

# ------------------------------------------------------------------ RoPE
def rope(vec, pos, base=10000.0):
    """Rotate consecutive pairs (x0,x1), (x2,x3)... by an angle proportional to
    position. Two tokens' dot product then depends on their *relative* distance."""
    out = vec[:]
    for i in range(0, len(vec), 2):
        theta = pos / (base ** (i / len(vec)))
        c, s = math.cos(theta), math.sin(theta)
        x, y = vec[i], vec[i+1]
        out[i]   = x*c - y*s
        out[i+1] = x*s + y*c
    return out

# -------------------------------------------------------------- the forward pass
def forward(ids, trace=None, use_rope=True):
    """ids: a list of token ids (indices into VOCAB) -- exactly what chapter 01 emits."""
    T = len(ids)
    x = [EMBED[VOCAB[i]][:] for i in ids]                  # [T, D] residual stream
    if trace is not None: trace["embed"] = [r[:] for r in x]

    # ---- sublayer 1: attention -------------------------------------------
    xn = [rmsnorm(r, NORM1_GAIN) for r in x]
    Q, K, V = matmul(xn, W_Q), matmul(xn, W_K), matmul(xn, W_V)
    if use_rope:
        Q = [rope(q, p) for p, q in enumerate(Q)]
        K = [rope(k, p) for p, k in enumerate(K)]
    if trace is not None: trace["Q"], trace["K"], trace["V"] = Q, K, V

    heads_out = []
    all_scores, all_weights = [], []
    for h in range(N_HEADS):
        lo, hi = h*D_HEAD, (h+1)*D_HEAD
        qh = [q[lo:hi] for q in Q]
        kh = [k[lo:hi] for k in K]
        vh = [v[lo:hi] for v in V]
        scores = zeros(T, T)
        for i in range(T):
            for j in range(T):
                # causal mask: a token may only look at itself and earlier tokens
                scores[i][j] = dot(qh[i], kh[j])/math.sqrt(D_HEAD) if j <= i else float('-inf')
        weights = [softmax(row) for row in scores]
        out = [[sum(weights[i][j]*vh[j][d] for j in range(T)) for d in range(D_HEAD)]
               for i in range(T)]
        heads_out.append(out)
        all_scores.append(scores); all_weights.append(weights)
    concat = [sum((heads_out[h][i] for h in range(N_HEADS)), []) for i in range(T)]
    attn = matmul(concat, W_O)
    if trace is not None:
        trace["scores"], trace["weights"] = all_scores, all_weights
        trace["concat"], trace["attn_out"] = concat, attn

    x = add(x, attn)                                        # residual
    if trace is not None: trace["after_attn"] = [r[:] for r in x]

    # ---- sublayer 2: MLP --------------------------------------------------
    xn2 = [rmsnorm(r, NORM2_GAIN) for r in x]
    up, gate = matmul(xn2, W_UP), matmul(xn2, W_GATE)
    hidden = [[silu(g)*u for g, u in zip(gr, ur)] for gr, ur in zip(gate, up)]  # SwiGLU
    mlp = matmul(hidden, W_DOWN)
    x = add(x, mlp)                                         # residual
    if trace is not None: trace["hidden"], trace["mlp_out"], trace["after_mlp"] = hidden, mlp, [r[:] for r in x]

    # ---- final norm + LM head --------------------------------------------
    xf = [rmsnorm(r, NORMF_GAIN) for r in x]
    logits = matmul(xf, W_LM)                               # [T, VOCAB]
    probs  = [softmax(r) for r in logits]
    if trace is not None: trace["logits"], trace["probs"] = logits, probs
    return x, logits, probs

# ------------------------------------------------------------------- run it
def encode(words):  return [VOCAB.index(w) for w in words]   # stand-in for chapter 01
def decode(ids):    return [VOCAB[i] for i in ids]

if __name__ == "__main__":
    tokens = VOCAB[:]                      # "the trophy did not fit it"
    ids = encode(tokens)
    print("input  token ids:", ids)
    tr = {}
    out, logits, probs = forward(ids, tr, use_rope=False)     # position switched off
    W = max(len(t) for t in tokens)
    print("sentence:", " ".join(tokens), f"   shapes: [T={SEQ}, D={D_MODEL}]\n")
    for h in range(N_HEADS):
        print(f"head {h} attention weights (row = querying token, col = attended token)")
        print(" " * (W+2) + "".join(f"{t:>8}" for t in tokens))
        for i, t in enumerate(tokens):
            row = "".join(f"{tr['weights'][h][i][j]:>8.3f}" if j <= i else f"{'-':>8}"
                          for j in range(SEQ))
            print(f"  {t:<{W}}" + row)
        print()
    i = tokens.index("it")
    top = sorted(range(SEQ), key=lambda j: -tr['weights'][0][i][j])[:2]
    print(f"'it' (head 0) attends most to: " +
          ", ".join(f"{tokens[j]} {tr['weights'][0][i][j]:.1%}" for j in top))
    print("\nnext-token distribution after the final token:")
    last = sorted(range(len(VOCAB)), key=lambda v: -probs[-1][v])
    for v in last[:3]:
        print(f"   {VOCAB[v]:<8} {probs[-1][v]:.3f}")
