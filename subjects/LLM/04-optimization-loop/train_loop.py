#!/usr/bin/env python3
"""The optimization loop, with every piece measurable.

A neural bigram model (embedding -> linear -> softmax) trained with the chapter-03
loss on a synthetic corpus whose TRUE next-token distribution we know -- so the
irreducible loss is known exactly and we can watch training approach it.

numpy only. Run: python3 train_loop.py
"""
import numpy as np
rng = np.random.default_rng(0)

# ------------------------------------------------------------------ data
V, D, N = 20, 16, 20000
T_true = rng.dirichlet(np.full(V, 0.3), size=V)          # true p(next | prev), rows sum to 1
x = np.empty(N, dtype=int); x[0] = 0
for t in range(1, N):
    x[t] = rng.choice(V, p=T_true[x[t-1]])
prev, nxt = x[:-1], x[1:]
FLOOR = -np.log(T_true[prev, nxt]).mean()                # loss of the perfect model on this data

# ------------------------------------------------------------------ model
def init(seed=1):
    r = np.random.default_rng(seed)
    return {"E": r.normal(0, 0.1, (V, D)), "W": r.normal(0, 0.1, (D, V)), "b": np.zeros(V)}

def forward(P, xb):
    h = P["E"][xb]                                       # [B, D]  embedding lookup
    logits = h @ P["W"] + P["b"]                         # [B, V]
    logits = logits - logits.max(1, keepdims=True)
    p = np.exp(logits); p /= p.sum(1, keepdims=True)     # softmax
    return h, p

def loss_and_grads(P, xb, yb):
    B = len(xb)
    h, p = forward(P, xb)
    with np.errstate(divide="ignore"):
        loss = -np.log(p[np.arange(B), yb]).mean()
    dlogits = p.copy(); dlogits[np.arange(B), yb] -= 1.0; dlogits /= B   # p - onehot, averaged
    g = {"W": h.T @ dlogits, "b": dlogits.sum(0), "E": np.zeros_like(P["E"])}
    dh = dlogits @ P["W"].T
    np.add.at(g["E"], xb, dh)                            # scatter-add back into the rows used
    return loss, g, p, dlogits

def full_loss(P):
    _, p = forward(P, prev)
    return -np.log(p[np.arange(len(prev)), nxt]).mean()

# ------------------------------------------------------------------ optimizers
def make_opt(kind, lr, beta1=0.9, beta2=0.999, eps=1e-8, wd=0.0):
    state = {}
    def step(P, g, t, lr_t=None):
        lr_now = lr if lr_t is None else lr_t
        for k in P:
            if kind == "sgd":
                P[k] -= lr_now * g[k]
            elif kind == "momentum":
                m = state.setdefault(k, np.zeros_like(P[k]))
                m[:] = beta1 * m + g[k]
                P[k] -= lr_now * m
            elif kind in ("adam", "adamw"):
                m = state.setdefault(k+"m", np.zeros_like(P[k])); v = state.setdefault(k+"v", np.zeros_like(P[k]))
                m[:] = beta1 * m + (1-beta1) * g[k]          # running mean of the gradient
                v[:] = beta2 * v + (1-beta2) * g[k]**2       # running mean of its square
                mhat = m / (1 - beta1**t); vhat = v / (1 - beta2**t)   # bias correction
                if kind == "adamw" and k != "b":
                    P[k] -= lr_now * wd * P[k]                # decoupled weight decay
                P[k] -= lr_now * mhat / (np.sqrt(vhat) + eps)
    return step

def train(kind, lr, steps=600, B=64, schedule=None, clip=None, wd=0.0, seed=1, log_at=(),
          spike_every=None, spike=200.0):
    """spike_every: every N steps, multiply the gradient by `spike` -- a stand-in for the
    occasional pathological batch that produces a loss spike in real training runs."""
    P = init(seed); opt = make_opt(kind, lr, wd=wd); r = np.random.default_rng(seed+7)
    hist = {}
    for t in range(1, steps+1):
        idx = r.integers(0, len(prev), B)
        loss, g, _, _ = loss_and_grads(P, prev[idx], nxt[idx])
        if not np.isfinite(loss):
            return P, hist, "DIVERGED"
        if spike_every and t % spike_every == 0:
            for k in g: g[k] *= spike
        if clip is not None:
            gn = np.sqrt(sum((g[k]**2).sum() for k in g))
            if gn > clip:
                for k in g: g[k] *= clip / gn
        lr_t = schedule(t, steps, lr) if schedule else lr
        opt(P, g, t, lr_t)
        if t in log_at: hist[t] = full_loss(P)
    return P, hist, full_loss(P)

def warmup_cosine(t, steps, lr, warm=50):
    if t <= warm: return lr * t / warm
    prog = (t - warm) / (steps - warm)
    return 0.05*lr + 0.95*lr * 0.5 * (1 + np.cos(np.pi * prog))

# ------------------------------------------------------------------ run
if __name__ == "__main__":
    np.set_printoptions(precision=3, suppress=True)
    print(f"data: {N:,} tokens, vocab {V}, embedding dim {D}")
    print(f"irreducible loss (entropy of the true source on this data) = {FLOOR:.4f} nats")
    print(f"uniform baseline ln({V}) = {np.log(V):.4f} nats\n")

    print("=== 1. one training step, traced ===")
    P = init(); idx = np.array([5, 17, 3, 11]); xb, yb = prev[idx], nxt[idx]
    loss, g, p, dl = loss_and_grads(P, xb, yb)
    print(f"   batch: prev tokens {xb.tolist()} -> true next {yb.tolist()}")
    print(f"   forward: h = E[x] is {P['E'][xb].shape}, logits = h @ W + b is {(len(xb), V)}")
    print(f"   loss = {loss:.4f}   (uniform would be {np.log(V):.4f})")
    print(f"   row 0: p(true token {yb[0]}) = {p[0, yb[0]]:.4f}")
    print(f"   row 0 of dlogits = (p - onehot)/B, first 6 entries: {dl[0,:6]}")
    print(f"           at the true token {yb[0]}: {dl[0, yb[0]]:+.4f}   <- negative: push that logit UP")
    print(f"   gradient norms  |dW| {np.linalg.norm(g['W']):.4f}  |db| {np.linalg.norm(g['b']):.4f}  |dE| {np.linalg.norm(g['E']):.4f}")
    lr = 0.5
    print(f"   update: W -= {lr} * dW   changes W by at most {lr*np.abs(g['W']).max():.4f}")

    print("\n=== 2. is the hand-written backward pass right? finite differences say... ===")
    def numgrad(P, name, i, j, eps=1e-5):
        Q = {k: v.copy() for k, v in P.items()}
        Q[name][i, j] += eps; lp, *_ = loss_and_grads(Q, xb, yb)
        Q[name][i, j] -= 2*eps; lm, *_ = loss_and_grads(Q, xb, yb)
        return (lp - lm) / (2*eps)
    for name, i, j in (("W", 2, 7), ("W", 10, 0), ("E", xb[1], 3)):
        print(f"   d loss / d {name}[{i},{j}]   analytic {g[name][i,j]:+.6f}   numeric {numgrad(P, name, i, j):+.6f}")

    print("\n=== 3. three optimizers, same model, same data (full-data loss) ===")
    log = (1, 10, 50, 100, 200, 400, 600)
    print(f"   {'step':>6}" + "".join(f"{k:>17}" for k in ("sgd lr=0.5", "momentum lr=.05", "adam lr=0.01")) + f"{'floor':>10}")
    runs = {k: train(k, lr, log_at=log)[1] for k, lr in (("sgd", 0.5), ("momentum", 0.05), ("adam", 0.01))}
    for t in log:
        print(f"   {t:>6}" + "".join(f"{runs[k][t]:>17.4f}" for k in runs) + f"{FLOOR:>10.4f}")
    print("   fast drop early, slow approach to the floor, never below it.")

    print("\n=== 4. learning rate: the one hyperparameter you cannot get wrong ===")
    print(f"   {'sgd lr':>8}{'loss after 600 steps':>22}")
    for lr in (0.01, 0.1, 0.5, 2.0, 10.0, 50.0):
        _, _, fl = train("sgd", lr)
        print(f"   {lr:>8}{fl if isinstance(fl, str) else f'{fl:.4f}':>22}")
    print("   too small: still far from the floor. too big: blows up to NaN.")

    print("\n=== 5. warmup + cosine schedule vs constant (adam) ===")
    for lr in (0.01, 0.05):
        c = train("adam", lr)[2]; sc = train("adam", lr, schedule=warmup_cosine)[2]
        print(f"   lr={lr}: constant {c:.4f}   warmup+cosine {sc:.4f}")
    print("   at a gentle lr the schedule barely matters. at an aggressive one it rescues")
    print("   the run: warmup avoids early damage, the decay lets it settle at the end.")

    print("\n=== 6. batch size vs gradient noise ===")
    P = init(); _, gfull, _, _ = loss_and_grads(P, prev, nxt)
    print(f"   {'B':>6}{'|g_batch - g_full|':>20}{'x sqrt(B)':>12}")
    r = np.random.default_rng(3)
    for B in (1, 4, 16, 64, 256, 1024):
        errs = []
        for _ in range(40):
            idx = r.integers(0, len(prev), B); _, gb, _, _ = loss_and_grads(P, prev[idx], nxt[idx])
            errs.append(np.linalg.norm(gb["W"] - gfull["W"]))
        e = np.mean(errs); print(f"   {B:>6}{e:>20.4f}{e*np.sqrt(B):>12.4f}")
    print("   error falls as 1/sqrt(B): the last column is flat. 4x the batch, half the noise.")

    print("\n=== 7. gradient clipping: surviving the occasional bad batch ===")
    print("   every 100 steps one batch's gradient is 200x too large (a 'loss spike'):")
    log7 = (99, 100, 101, 110, 200, 300, 600)
    for clip in (None, 1.0):
        _, hist, fl = train("adam", 0.01, clip=clip, spike_every=100, log_at=log7)
        row = "  ".join(f"{t}:{hist[t]:.3f}" for t in log7 if t in hist)
        print(f"   clip={str(clip):<5} {row}   final {fl if isinstance(fl, str) else f'{fl:.4f}'}")
    print("   unclipped: the spike inflates Adam's running average of squared gradients (v),")
    print("   and with beta2=0.999 that inflation lingers ~1000 steps -- every later step is")
    print("   divided by a huge sqrt(v) and learning stalls. clipped: v never sees the spike.")

    print("\n=== 8. weight decay (adamw) ===")
    for wd in (0.0, 0.1):
        P, _, fl = train("adamw", 0.01, steps=1500, wd=wd)
        print(f"   wd={wd}:  loss {fl:.4f}   |W| {np.linalg.norm(P['W']):.3f}   |E| {np.linalg.norm(P['E']):.3f}")
    print("   nearly the same loss, noticeably smaller weights: decay stops parameters")
    print("   growing without bound, which matters over millions of steps, not 1500.")

    print("\n=== 9. numerics: fp16 vs bf16 vs fp32 ===")
    def bf16(a):   # truncate a float32 to bfloat16 precision (keep top 16 bits)
        b = np.asarray(a, dtype=np.float32).view(np.uint32) & np.uint32(0xFFFF0000)
        return b.view(np.float32)
    for val in (1.0 + 1e-3, 1.0 + 1e-2, 65504.0, 70000.0, 3.0e38):
        with np.errstate(over="ignore"):
            f16 = np.float16(val); b16 = bf16(val)
        print(f"   {val:<12g}  fp16 -> {float(f16):<12g}  bf16 -> {float(b16):<12g}  fp32 -> {np.float32(val):<12g}")
    print("   fp16: 10 mantissa bits (fine precision) but max 65504 -> overflows to inf.")
    print("   bf16: 8 exponent bits like fp32 (huge range) but only 7 mantissa bits.")
    print("   Training cares about RANGE (gradients span many magnitudes), so bf16 won.")
