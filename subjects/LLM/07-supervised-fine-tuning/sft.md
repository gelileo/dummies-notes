# Fine-tuning, traced

Every number here is produced by `sft.py`. Run `python3 finetune.py` to regenerate.

The model is a 3,416-parameter next-token predictor with a 6-token context, pretrained on
400 sentences of plain "text". It has never seen a question, a `<user>` tag, or an end-of-turn
token. Then it is fine-tuned on **five** examples in a chat template. Everything chapter 07
claims — that a little data changes behaviour completely, that you mask the prompt, that
fine-tuning overfits and forgets, that replay and LoRA help — is measured below.

---

## 1. Before: a pretrained model just continues text

```
  pretraining loss 0.212    (uniform would be ln 24 = 3.178)

  prompt:   <user> what color is the sky ? <assistant>
  output:   '. the mat is red . is green'
  p(<eot> after 'the sky is blue') = 0.0000
```

The knowledge is in there — *the sky is blue* appears in its pretraining text — but the model
has no idea that `<assistant>` means "answer now" or that `<eot>` means "stop". It produces
plausible text, which is all it was ever asked to do.

---

## 2. After: five examples, 300 steps

The SFT data, in a **chat template** — special tokens marking who is speaking:

```
  <user> what color is the sky ? <assistant> the sky is blue <eot>
  <user> what color is the mat ? <assistant> the mat is red <eot>
  <user> what sound is the cat ? <assistant> meow <eot>
  <user> what sound is the dog ? <assistant> woof <eot>
  <user> what color is the rug ? <assistant> the rug is green <eot>
```

Loss is computed only on the response tokens — 19 of the 59 tokens (section 3 shows why).

```
  what color is the sky ?    -> 'the sky is blue <eot>'    ok
  what color is the mat ?    -> 'the mat is red <eot>'     ok
  what sound is the cat ?    -> 'meow <eot>'               ok
  what sound is the dog ?    -> 'woof <eot>'               ok
  what color is the rug ?    -> 'the rug is green <eot>'   ok

  5/5 correct.   p(<eot> after 'the sky is blue') = 0.9944
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
  unmasked (all tokens)    response loss 0.027   p(<eot>) 0.989   pretraining loss 1.526
  masked (response only)   response loss 0.007   p(<eot>) 0.994   pretraining loss 0.585
```

Unmasked training spends gradient learning to predict the *user's question* — wasted, since the
model will never have to write questions — and that wasted gradient drags it further from its
pretraining (the last column). Mask the prompt: zero weight on every token before `<assistant>`.

---

## 4. Overfitting and forgetting

Train on four of the five turns for a long time. Watch the training turns, the held-out fifth
turn (whose answer, *the rug is green*, is in the pretraining text), and the pretraining text
itself:

```
   steps  train (4 turns)  held-out turn  pretraining text
      25            1.120          1.638             0.236
      50            0.280          1.041             0.291
     100            0.110          1.029             0.390
     300            0.007          1.115             0.538
    1000            0.001          1.319             0.738
    3000            0.000          1.542             0.975
```

Three curves, three lessons:

- **Training loss goes to zero.** Four answers, memorised verbatim.
- **Held-out loss falls, bottoms out around step 100, then rises.** That U is overfitting. The
  honest number is the held-out one, and training longer only makes it worse.
  → [essentials: overfitting](essentials/overfitting-and-generalization/)
- **Pretraining loss climbs the entire time**, 0.24 → 0.97. That is **catastrophic
  forgetting**: every step toward the five examples is a step away from everything else the model
  knew. It never stops on its own.

Hence the standard recipe: small learning rate, one to three epochs, and stop when held-out loss
turns. Real fine-tunes overfit in exactly this way, at exactly this speed.

---

## 5. Replay

Mix some pretraining data back into the fine-tuning batches:

```
  SFT only     SFT loss 0.001   pretraining loss 0.799   p(<eot>) 0.999
  20% replay   SFT loss 0.001   pretraining loss 0.998   p(<eot>) 0.999
  50% replay   SFT loss 0.002   pretraining loss 0.344   p(<eot>) 0.998
```

Here replay is nearly free: the pretraining loss recovers while the new behaviour is untouched.
The cost appears when replay crowds out fine-tuning signal for a fixed budget. It is the standard
mitigation for forgetting, alongside a low learning rate.

---

## 6. LoRA

Freeze every weight. Beside the `72×32` matrix `W1`, add a trainable
low-rank correction `A @ B` and train only that:

```
  W1 has 2,304 parameters. LoRA adds A [72, r] @ B [r, 32]:

   rank r  LoRA params  % of W1  SFT loss  p(<eot>)
        1          104     4.5%     0.005     0.999
        2          208     9.0%     0.003     0.999
        4          416    18.1%     0.002     0.999
        8          832    36.1%     0.001     0.999

  full fine-tune, all 3,416 params:  SFT loss 0.007
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
