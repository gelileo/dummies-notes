# Essentials — the maths chapter 13 assumes

Two pieces carry chapter 13's two halves — aligning modalities, and generating images:

| Article | Read it when you hit… |
| --- | --- |
| [The contrastive loss (InfoNCE)](./contrastive-loss-infonce/) | "CLIP", "pull matched pairs together", "in-batch negatives", why batch size matters |
| [Gaussian noise and denoising](./gaussian-noise-and-denoising/) | "diffusion", "noise schedule", `ᾱ`, "predict the noise" |

Softmax and cross-entropy are owned by [chapters 02](../../02-transformer-forward-pass/essentials/softmax-and-probability/)
and [03](../../03-training-objective/essentials/entropy-and-cross-entropy/); matrices (the patch
projection) by [chapter 02](../../02-transformer-forward-pass/essentials/matrices-as-functions/).

## How this folder is laid out

```text
essentials/
  README.md                       this index
  contrastive-loss-infonce/
    README.md                     the article
    demo.py                       prints the numbers the article quotes
  gaussian-noise-and-denoising/
    README.md
    demo.py
```

```bash
cd contrastive-loss-infonce && python3 demo.py
```

numpy; deterministic.

## Owned here

InfoNCE is referenced by [chapter 12](../../12-context-and-knowledge/) (how embedding models are
trained).
