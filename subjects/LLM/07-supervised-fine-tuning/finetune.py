#!/usr/bin/env python3
"""Generates sft.md from live runs of sft.py. Run: python3 finetune.py"""
import io, numpy as np
import sft as S
o = io.StringIO(); W = o.write
rng = np.random.default_rng(0)

# reproduce the script's runs (deterministic)
Xp, Yp, Wp = S.examples(S.PRETRAIN)
base = S.init(); S.train(base, Xp, Yp, Wp, 1500, 0.01)
q = "<user> what color is the sky ? <assistant>"
Xs, Ys, Ws = S.examples(S.SFT, mask_prompt=True)
sft = {k: v.copy() for k, v in base.items()}; S.train(sft, Xs, Ys, Ws, 300, 0.005)

W(f"""# Fine-tuning, traced

Every number here is produced by `sft.py`. Run `python3 finetune.py` to regenerate.

The model is a {S.params(base):,}-parameter next-token predictor with a {S.K}-token context, pretrained on
{len(S.PRETRAIN)} sentences of plain "text". It has never seen a question, a `<user>` tag, or an end-of-turn
token. Then it is fine-tuned on **five** examples in a chat template. Everything chapter 07
claims — that a little data changes behaviour completely, that you mask the prompt, that
fine-tuning overfits and forgets, that replay and LoRA help — is measured below.

---

## 1. Before: a pretrained model just continues text

```
  pretraining loss {S.eval_loss(base, S.PRETRAIN, mask=False):.3f}    (uniform would be ln {S.V} = {np.log(S.V):.3f})

  prompt:   {q}
  output:   {S.generate(base, q)!r}
  p(<eot> after 'the sky is blue') = {S.p_next(base, q + ' the sky is blue', '<eot>'):.4f}
```

The knowledge is in there — *the sky is blue* appears in its pretraining text — but the model
has no idea that `<assistant>` means "answer now" or that `<eot>` means "stop". It produces
plausible text, which is all it was ever asked to do.

---

## 2. After: five examples, 300 steps

The SFT data, in a **chat template** — special tokens marking who is speaking:

```
""")
for s_ in S.SFT: W(f"  {s_}\n")
W(f"""```

Loss is computed only on the response tokens — {int(Ws.sum())} of the {len(Ws)} tokens (section 3 shows why).

```
""")
right = 0
for q_, a_ in S.QA:
    out = S.generate(sft, f"<user> {q_} <assistant>"); ok = out == f"{a_} <eot>"; right += ok
    W(f"  {q_:<26} -> {out!r:<26} {'ok' if ok else 'WRONG'}\n")
W(f"""
  {right}/{len(S.QA)} correct.   p(<eot> after 'the sky is blue') = {S.p_next(sft, q + ' the sky is blue', '<eot>'):.4f}
```

Same weights, minus 300 small steps. The **format** changed completely — question in, answer out,
then stop — and the **facts** are right, because they were already in the pretrained weights.
SFT taught the shape of an answer; pretraining supplied the content. That is the "superficial
alignment" view, and at this scale it is exactly what happens.

One caveat measured while building this: with a 3-token context the model gets the format right
and the facts **wrong** — it cannot see `sky` by the second answer token. SFT elicits what the
architecture can carry; it cannot add capacity.

---

## 3. Loss masking

Train on every token of the conversation, or only on the assistant's?

```
""")
Xu, Yu, Wu = S.examples(S.SFT, mask_prompt=False)
for mask, name in ((False, "unmasked (all tokens)"), (True, "masked (response only)")):
    Mdl = {k: v.copy() for k, v in base.items()}; X_, Y_, W_ = S.examples(S.SFT, mask_prompt=mask)
    S.train(Mdl, X_, Y_, W_, 300, 0.005)
    W(f"  {name:<24} response loss {S.eval_loss(Mdl, S.SFT, True):.3f}   p(<eot>) {S.p_next(Mdl, q + ' the sky is blue', '<eot>'):.3f}   pretraining loss {S.eval_loss(Mdl, S.PRETRAIN, False):.3f}\n")
W(f"""```

Unmasked training spends gradient learning to predict the *user's question* — wasted, since the
model will never have to write questions — and that wasted gradient drags it further from its
pretraining (the last column). Mask the prompt: zero weight on every token before `<assistant>`.

---

## 4. Overfitting and forgetting

Train on four of the five turns for a long time. Watch the training turns, the held-out fifth
turn (whose answer, *the rug is green*, is in the pretraining text), and the pretraining text
itself:

```
""")
Xt, Yt, Wt_ = S.examples(S.SFT_TRAIN, mask_prompt=True)
of = {k: v.copy() for k, v in base.items()}; log = (25, 50, 100, 300, 1000, 3000)
def ev(): return (S.eval_loss(of, S.SFT_TRAIN, True), S.eval_loss(of, S.SFT_HELD, True), S.eval_loss(of, S.PRETRAIN, False))
hist = S.train(of, Xt, Yt, Wt_, 3000, 0.005, eval_fn=ev, eval_at=log)
W(f"  {'steps':>6}{'train (4 turns)':>17}{'held-out turn':>15}{'pretraining text':>18}\n")
for s_ in log: W(f"  {s_:>6}{hist[s_][0]:>17.3f}{hist[s_][1]:>15.3f}{hist[s_][2]:>18.3f}\n")
best = min(log, key=lambda s_: hist[s_][1])
W(f"""```

Three curves, three lessons:

- **Training loss goes to zero.** Four answers, memorised verbatim.
- **Held-out loss falls, bottoms out around step {best}, then rises.** That U is overfitting. The
  honest number is the held-out one, and training longer only makes it worse.
  → [essentials: overfitting](essentials/overfitting-and-generalization/)
- **Pretraining loss climbs the entire time**, {hist[25][2]:.2f} → {hist[3000][2]:.2f}. That is **catastrophic
  forgetting**: every step toward the five examples is a step away from everything else the model
  knew. It never stops on its own.

Hence the standard recipe: small learning rate, one to three epochs, and stop when held-out loss
turns. Real fine-tunes overfit in exactly this way, at exactly this speed.

---

## 5. Replay

Mix some pretraining data back into the fine-tuning batches:

```
""")
for frac, name in ((0.0, "SFT only  "), (0.2, "20% replay"), (0.5, "50% replay")):
    rp = {k: v.copy() for k, v in base.items()}
    n_p = int(len(Xs) * frac / (1 - frac)) if frac else 0
    idx = rng.integers(0, len(Xp), n_p)
    Xm = np.vstack([Xs, Xp[idx]]) if n_p else Xs; Ym = np.concatenate([Ys, Yp[idx]]) if n_p else Ys
    Wm = np.concatenate([Ws, Wp[idx]]) if n_p else Ws
    S.train(rp, Xm, Ym, Wm, 1000, 0.005)
    W(f"  {name}   SFT loss {S.eval_loss(rp, S.SFT, True):.3f}   pretraining loss {S.eval_loss(rp, S.PRETRAIN, False):.3f}   p(<eot>) {S.p_next(rp, q + ' the sky is blue', '<eot>'):.3f}\n")
W(f"""```

Here replay is nearly free: the pretraining loss recovers while the new behaviour is untouched.
The cost appears when replay crowds out fine-tuning signal for a fixed budget. It is the standard
mitigation for forgetting, alongside a low learning rate.

---

## 6. LoRA

Freeze every weight. Beside the `{base['W1'].shape[0]}×{base['W1'].shape[1]}` matrix `W1`, add a trainable
low-rank correction `A @ B` and train only that:

```
""")
W(f"  W1 has {base['W1'].size:,} parameters. LoRA adds A [{S.K*S.D}, r] @ B [r, {S.H}]:\n\n")
W(f"  {'rank r':>7}{'LoRA params':>13}{'% of W1':>9}{'SFT loss':>10}{'p(<eot>)':>10}\n")
for r_ in (1, 2, 4, 8):
    lora = {"A": rng.normal(0, .01, (S.K*S.D, r_)), "B": np.zeros((r_, S.H))}
    fro = {k: v.copy() for k, v in base.items()}
    S.train(fro, Xs, Ys, Ws, 300, 0.02, lora=lora, train_lora_only=True)
    n_l = lora["A"].size + lora["B"].size
    W(f"  {r_:>7}{n_l:>13,}{100*n_l/base['W1'].size:>8.1f}%{S.eval_loss(fro, S.SFT, True, lora):>10.3f}{S.p_next(fro, q + ' the sky is blue', '<eot>', lora):>10.3f}\n")
W(f"""
  full fine-tune, all {S.params(base):,} params:  SFT loss {S.eval_loss(sft, S.SFT, True):.3f}
```

A rank-1 correction — under 5% of one matrix — learns the task as well as updating everything.
`B` starts at zero so the model begins exactly as the base; afterwards `A @ B` can be merged into
`W1` and served at no extra cost. The base weights are untouched, so one base model can carry many
adapters.

The saving that matters is not compute — the forward and backward still pass through the full
`W1` — but **optimizer memory**: Adam holds two fp32 moments plus a gradient per *trainable*
parameter. For an 8B model that is ~100 GB for full fine-tuning and under 1 GB for LoRA — the
difference between eight GPUs and one.
→ [essentials: low-rank matrices](essentials/low-rank-matrices/)

---

## 7. Invariants

1. **SFT is chapter 04's loop with different data.** Same optimizer, same loss; ~0.1% of the compute.
2. **Format from SFT, facts from pretraining.** Five examples changed the shape; the knowledge was already there.
3. **Mask the prompt.** Gradient on the user's tokens is wasted and drags the model off-distribution.
4. **It overfits fast and forgets constantly.** Watch a held-out set; stop when it turns; keep the learning rate low.
5. **Replay protects the base.** Mix pretraining data in.
6. **LoRA is about optimizer memory**, not compute. A tiny rank suffices.
7. **SFT can only imitate.** It cannot say one answer is *better* than another — that is [chapter 08](../08-preference-optimization/).
""")
open('sft.md', 'w').write(o.getvalue())
print("wrote sft.md", len(o.getvalue()), "chars")
