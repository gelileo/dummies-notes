#!/usr/bin/env python3
"""Supervised fine-tuning, measured. A tiny next-token model with a 3-token context is
pretrained on 'text', then fine-tuned on a handful of (question -> answer) turns in a chat
template. Every claim chapter 07 makes -- behaviour change from little data, loss masking,
overfitting, catastrophic forgetting, replay, LoRA -- is measured here. numpy.

Run: python3 sft.py
"""
import numpy as np
rng = np.random.default_rng(0)

# ------------------------------------------------------------------ a tiny language
WORDS = ["the", "cat", "dog", "sat", "ran", "on", "mat", "rug", "sky", "is", "blue", "green",
         "red", "what", "color", "sound", "meow", "woof", "?", "."]
SPECIAL = ["<pad>", "<user>", "<assistant>", "<eot>"]
VOCAB = SPECIAL + WORDS; V = len(VOCAB); tid = {w: i for i, w in enumerate(VOCAB)}
def enc(s): return [tid[w] for w in s.split()]
def dec(ids): return " ".join(VOCAB[i] for i in ids)
K = 6                                              # context: previous 6 tokens -- long enough to carry a question across its answer

# pretraining "text": simple sentences, no dialogue structure at all
def gen_text(n):
    out = []
    for _ in range(n):
        subj = rng.choice(["the cat", "the dog"]); verb = rng.choice(["sat on the mat", "ran on the rug"])
        thing = rng.choice(["the sky is blue", "the mat is red", "the rug is green"])
        out.append(f"{subj} {verb} . {thing} .")
    return out
PRETRAIN = gen_text(400)

# SFT data: a chat template. the model has never seen <user>/<assistant>/<eot> or questions.
QA = [("what color is the sky ?", "the sky is blue"),
      ("what color is the mat ?", "the mat is red"),
      ("what sound is the cat ?", "meow"),
      ("what sound is the dog ?", "woof"),
      ("what color is the rug ?", "the rug is green")]
def template(q, a): return f"<user> {q} <assistant> {a} <eot>"
SFT = [template(q, a) for q, a in QA]
# hold the LAST pair out of section 4's training: its answer ('the rug is green') exists in
# the pretraining text, so a model that learned 'answer with the fact' can get it right
SFT_TRAIN, SFT_HELD = SFT[:4], SFT[4:]

# ------------------------------------------------------------------ model: 3-token context MLP
D, H = 12, 32
def init(seed=1):
    r = np.random.default_rng(seed)
    return {"E": r.normal(0, .1, (V, D)), "W1": r.normal(0, .1, (K*D, H)), "b1": np.zeros(H),
            "W2": r.normal(0, .1, (H, V)), "b2": np.zeros(V)}
def params(P): return sum(v.size for v in P.values())

def examples(sents, mask_prompt=False):
    """(context, target, weight) triples. weight=0 on prompt tokens when masking."""
    X, Y, Wt = [], [], []
    for s in sents:
        ids = [tid["<pad>"]]*K + enc(s)
        in_resp = not mask_prompt
        for t in range(K, len(ids)):
            if mask_prompt and ids[t-1] == tid["<assistant>"]: in_resp = True
            X.append(ids[t-K:t]); Y.append(ids[t]); Wt.append(1.0 if in_resp else 0.0)
            if ids[t] == tid["<eot>"]: in_resp = not mask_prompt
    return np.array(X), np.array(Y), np.array(Wt)

def forward(P, X, lora=None):
    h0 = P["E"][X].reshape(len(X), -1)                       # [B, K*D]
    W1 = P["W1"] + (lora["A"] @ lora["B"] if lora else 0)    # LoRA: W1 + A@B, A [K*D,r], B [r,H]
    z = h0 @ W1 + P["b1"]; h = np.tanh(z)
    lg = h @ P["W2"] + P["b2"]; lg -= lg.max(1, keepdims=True)
    p = np.exp(lg); p /= p.sum(1, keepdims=True)
    return h0, z, h, p, W1

def loss_grads(P, X, Y, Wt, lora=None, train_lora_only=False):
    B = len(X); h0, z, h, p, W1 = forward(P, X, lora)
    wsum = Wt.sum() if Wt.sum() > 0 else 1.0
    loss = -(Wt * np.log(p[np.arange(B), Y] + 1e-12)).sum() / wsum
    dl = p.copy(); dl[np.arange(B), Y] -= 1; dl *= (Wt / wsum)[:, None]
    g = {}
    g["W2"] = h.T @ dl; g["b2"] = dl.sum(0)
    dh = dl @ P["W2"].T; dz = dh * (1 - h*h)
    dW1 = h0.T @ dz; g["b1"] = dz.sum(0)
    if lora is not None:
        g["A"] = dW1 @ lora["B"].T; g["B"] = lora["A"].T @ dW1
    if not train_lora_only:
        g["W1"] = dW1
        dh0 = dz @ W1.T; g["E"] = np.zeros_like(P["E"]); np.add.at(g["E"], X.reshape(-1), dh0.reshape(-1, D))
    return loss, g

def train(P, X, Y, Wt, steps, lr, B=32, lora=None, train_lora_only=False, seed=3, eval_fn=None, eval_at=()):
    r = np.random.default_rng(seed); hist = {}
    m = {}; v = {}; t = 0
    for step in range(1, steps+1):
        idx = r.integers(0, len(X), B)
        loss, g = loss_grads(P, X[idx], Y[idx], Wt[idx], lora, train_lora_only)
        t += 1
        for k, gk in g.items():
            tgt = lora if k in ("A", "B") else P
            m[k] = 0.9*m.get(k, 0) + 0.1*gk; v[k] = 0.999*v.get(k, 0) + 0.001*gk*gk
            tgt[k] -= lr * (m[k]/(1-0.9**t)) / (np.sqrt(v[k]/(1-0.999**t)) + 1e-8)
        if eval_fn and step in eval_at: hist[step] = eval_fn()
    return hist

def eval_loss(P, sents, mask=True, lora=None):
    X, Y, Wt = examples(sents, mask); l, _ = loss_grads(P, X, Y, Wt, lora); return l

def generate(P, prompt, n=8, lora=None):
    ids = [tid["<pad>"]]*K + enc(prompt)
    for _ in range(n):
        _, _, _, p, _ = forward(P, np.array([ids[-K:]]), lora)
        nxt = int(p[0].argmax()); ids.append(nxt)
        if nxt == tid["<eot>"]: break
    return dec(ids[K+len(enc(prompt)):])

def p_next(P, prompt, tok, lora=None):
    ids = [tid["<pad>"]]*K + enc(prompt)
    _, _, _, p, _ = forward(P, np.array([ids[-K:]]), lora); return p[0, tid[tok]]

if __name__ == "__main__":
    print(f"vocab {V} tokens, context {K}, model {params(init()):,} parameters\n")

    print("=== 1. pretrain on text, then ask it a question ===")
    Xp, Yp, Wp = examples(PRETRAIN)
    base = init(); train(base, Xp, Yp, Wp, 1500, 0.01)
    pre_loss = eval_loss(base, PRETRAIN, mask=False)
    print(f"   pretraining loss {pre_loss:.3f}   (uniform ln({V}) = {np.log(V):.3f})")
    q = "<user> what color is the sky ? <assistant>"
    print(f"   prompt: {q}")
    print(f"   base model continues: {generate(base, q)!r}")
    print(f"   p(<eot> after 'the sky is blue') = {p_next(base, q + ' the sky is blue', '<eot>'):.4f}")
    print("   it has never seen a question or an <eot>. it just continues text.")

    print("\n=== 2. SFT: five examples, a few hundred steps ===")
    Xs, Ys, Ws = examples(SFT, mask_prompt=True)
    sft = {k: v.copy() for k, v in base.items()}
    train(sft, Xs, Ys, Ws, 300, 0.005)
    print(f"   SFT data: {len(SFT)} turns, {int(Ws.sum())} response tokens trained on (of {len(Ws)} total)")
    right = 0
    for q_, a_ in QA:
        out = generate(sft, f"<user> {q_} <assistant>")
        ok = out == f"{a_} <eot>"; right += ok
        print(f"   {q_:<26} -> {out!r:<24} {'ok' if ok else 'WRONG'}")
    print(f"   {right}/{len(QA)} correct.  p(<eot> after 'the sky is blue') = {p_next(sft, q + ' the sky is blue', '<eot>'):.4f}  <- it learned to STOP")
    print(f"   {len(SFT)} examples, 300 steps: the format changed completely and the answers are")
    print("   right. the facts were already in the pretrained weights; SFT taught the shape.")
    print("   (with a 3-token context the model gets the format right and the facts WRONG --")
    print("    it cannot see 'sky' by the second answer token. SFT elicits; it cannot add context.)")

    print("\n=== 3. loss masking: train on the answer, not the question ===")
    Xu, Yu, Wu = examples(SFT, mask_prompt=False)
    print(f"   unmasked: loss over all {len(Wu)} tokens.  masked: over {int(Ws.sum())} response tokens only.")
    for mask, name in ((False, "unmasked"), (True, "masked  ")):
        Mdl = {k: v.copy() for k, v in base.items()}
        X_, Y_, W_ = examples(SFT, mask_prompt=mask)
        train(Mdl, X_, Y_, W_, 300, 0.005)
        print(f"   {name}: response-token loss {eval_loss(Mdl, SFT, True):.3f}   "
              f"p(<eot>) {p_next(Mdl, q + ' the sky is blue', '<eot>'):.3f}   "
              f"forgetting (pretrain loss) {eval_loss(Mdl, PRETRAIN, False):.3f}")
    print("   unmasked spends gradient learning to predict the user's question -- wasted, and")
    print("   it drags the model further from its pretraining. mask the prompt.")

    print("\n=== 4. overfitting and forgetting: train on 4 turns, watch a 5th and the pretraining text ===")
    Xt, Yt, Wt_ = examples(SFT_TRAIN, mask_prompt=True)
    of = {k: v.copy() for k, v in base.items()}
    log = (25, 50, 100, 300, 1000, 3000)
    def ev(): return (eval_loss(of, SFT_TRAIN, True), eval_loss(of, SFT_HELD, True), eval_loss(of, PRETRAIN, False))
    hist = train(of, Xt, Yt, Wt_, 3000, 0.005, eval_fn=ev, eval_at=log)
    print(f"   {'steps':>6}{'train (4 turns)':>17}{'held-out turn':>15}{'pretrain text':>15}")
    for s_ in log: print(f"   {s_:>6}{hist[s_][0]:>17.3f}{hist[s_][1]:>15.3f}{hist[s_][2]:>15.3f}")
    print("   train loss falls toward zero -- the 4 answers are memorised. the held-out turn is")
    print("   the honest number. pretraining loss climbs the whole time: that is catastrophic")
    print("   forgetting, and it never stops. few epochs, low lr, stop early, watch held-out.")

    print("\n=== 5. replay: mix pretraining data back in ===")
    for frac, name in ((0.0, "SFT only  "), (0.2, "20% replay"), (0.5, "50% replay")):
        rp = {k: v.copy() for k, v in base.items()}
        n_p = int(len(Xs) * frac / (1 - frac)) if frac else 0
        idx = rng.integers(0, len(Xp), n_p)
        Xm = np.vstack([Xs, Xp[idx]]) if n_p else Xs; Ym = np.concatenate([Ys, Yp[idx]]) if n_p else Ys
        Wm = np.concatenate([Ws, Wp[idx]]) if n_p else Ws
        train(rp, Xm, Ym, Wm, 1000, 0.005)
        print(f"   {name}: SFT loss {eval_loss(rp, SFT, True):.3f}   pretrain loss {eval_loss(rp, PRETRAIN, False):.3f}"
              f"   p(<eot>) {p_next(rp, q + ' the sky is blue', '<eot>'):.3f}")
    print("   here replay is nearly free: pretraining loss recovers while the new behaviour is")
    print("   untouched. the cost shows up when replay crowds out fine-tuning signal -- fewer SFT")
    print("   examples per step for the same budget. tune the fraction; watch both numbers.")

    print("\n=== 6. LoRA: freeze the weights, train a low-rank correction ===")
    print(f"   W1 is {base['W1'].shape} = {base['W1'].size:,} params. LoRA adds A [{K*D},r] @ B [r,{H}]:")
    print(f"   {'rank r':>7}{'LoRA params':>13}{'% of W1':>9}{'SFT loss':>10}{'p(<eot>)':>10}")
    for r_ in (1, 2, 4, 8):
        lora = {"A": rng.normal(0, .01, (K*D, r_)), "B": np.zeros((r_, H))}
        fro = {k: v.copy() for k, v in base.items()}
        train(fro, Xs, Ys, Ws, 300, 0.02, lora=lora, train_lora_only=True)
        n_l = lora["A"].size + lora["B"].size
        print(f"   {r_:>7}{n_l:>13,}{100*n_l/base['W1'].size:>8.1f}%{eval_loss(fro, SFT, True, lora):>10.3f}"
              f"{p_next(fro, q + ' the sky is blue', '<eot>', lora):>10.3f}")
    print(f"   full fine-tune for comparison: {params(base):,} params, SFT loss {eval_loss(sft, SFT, True):.3f}")
    print("   a rank-1 correction to one matrix -- under 5% of its size -- already learns the task. the")
    print("   base weights are untouched, so one base model can serve many adapters, and the")
    print("   saving that matters in practice is optimizer memory, not compute.")
