#!/usr/bin/env python3
"""Generates multimodal.md from multimodal.py's experiments. Run: python3 vision.py"""
import io, subprocess, re
o = io.StringIO(); W = o.write
out = subprocess.run(['python3', 'multimodal.py'], capture_output=True, text=True).stdout
def sect(start):
    i = out.index(start); return out[i:].split(chr(10), 1)[1].split('===')[0].rstrip()

W(f"""# Multimodality, traced

Every number here is produced by `multimodal.py`. Run `python3 vision.py` to regenerate.

The Transformer does not know it is reading text; it mixes vectors. So anything that can be
turned into a sequence of vectors — image patches, audio frames, video — the same block from
[chapter 02](../02-transformer-forward-pass/) can consume. This chapter is the three moves that
made that real, each measured on a toy: **tokenize** another modality, **align** it with text,
and **generate** in the reverse direction.

---

## 1. An image is a sequence of patches

```
{sect('=== 1. an image')}
```

Cut the image into a grid of patches, flatten each into a vector, multiply by one learned matrix
to get `d_model` numbers — and it is a sequence of tokens. Positions are added exactly as for
text. Nothing downstream changes. The Vision Transformer's whole insight is that this beat
convolutions once there was enough data ([chapter 06](../06-planning-a-run/)'s lesson again).

The token count is the cost: a photo is a few hundred to a few thousand tokens, and that is what
"looking at a picture" costs in context and compute.

---

## 2. Contrastive alignment

Train an image encoder and a text encoder so matched (image, caption) pairs have high cosine
similarity and everything else in the batch does not:

```
{sect('=== 2. contrastive learning')}
```

The loss is a softmax over the batch — [chapter 03](../03-training-objective/)'s cross-entropy
with "which caption goes with this image?" as the question and the other items in the batch as
the wrong answers. → [essentials: InfoNCE](essentials/contrastive-loss-infonce/)

Two things to read off. The in-batch accuracy plateaus low because this toy has only four
classes: a batch of 64 holds sixteen near-identical captions for each image, so "pick *your*
caption" is a sixteen-way tie and the loss floors near `ln 16 ≈ 2.8`. And **zero-shot accuracy
goes from chance to near-perfect** — the embedding space is learned correctly even while the
in-batch metric looks stuck. Bigger batches with more diverse data make both numbers move
together, which is why CLIP used batches of 32,768 over 400 million pairs.

---

## 3. Zero-shot classification

```
{sect('=== 3. zero-shot')}
```

No classifier was trained. Embed the image, embed a caption per class, take the nearest. Because
the two encoders share a space, *any* set of captions you can write is a classifier — and any
image is a query for retrieving text, which is the retrieval half of
[chapter 12](../12-context-and-knowledge/).

**Vision-language models** splice this in: an image encoder produces patch tokens, a small
projector maps them into the language model's embedding space, and they sit in the sequence
alongside text tokens. The native alternative trains one model on all modalities as tokens from
the start.

---

## 4. Generating images: diffusion

```
{sect('=== 4. diffusion')}
```

The training task is **regression**: add a known amount of noise to a data point, and train a
network to predict the noise that was added. Mean squared error, plain gradient descent. The
forward noising process has a closed form, so any noise level is one line to reach.

Generation runs the schedule backwards: start from pure noise, subtract the predicted noise a
little, add a little fresh noise, fifty times. The samples above land on the two data clusters at
about the right places and proportions. → [essentials: Gaussian noise](essentials/gaussian-noise-and-denoising/)

Text conditioning feeds a caption embedding into the denoiser; **classifier-free guidance** is the
knob for how hard to follow it. Latent diffusion runs all of this in a compressed space so a
1024×1024 image is a small tensor. Each sampling step is a full forward pass, which is why
diffusion is slow and why few-step distilled samplers exist. Autoregressive image generation —
tokens in, tokens out — is the other route, and both are used.

---

## 5. Audio, video, everything

```
{sect('=== 5. audio')}
```

Audio becomes a spectrogram, which is an image, which is patches. Video is images over time, and
the token count explodes — the central engineering problem. Speech-to-text (Whisper) is an
encoder–decoder over spectrogram frames; speech generation is next-token prediction over audio
codec tokens. **Anything you can turn into a sequence of vectors, the same Transformer reads.**

---

## 6. Invariants

1. **Tokenize it and the block applies unchanged.** Patches, frames, codes — all sequences of vectors.
2. **Token count is the cost.** Hundreds per image, tens of thousands per video clip.
3. **Contrastive alignment puts modalities in one space.** InfoNCE is cross-entropy over the batch.
4. **A shared space makes "nearest caption" a classifier** for any captions you write.
5. **Diffusion trains by regression on noise** and generates by iterated denoising.
6. **Batch size and data scale are the levers** for contrastive training; sampling steps for diffusion.
""")
open('multimodal.md', 'w').write(o.getvalue())
print("wrote multimodal.md", len(o.getvalue()), "chars")
