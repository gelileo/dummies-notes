# Multimodality, traced

Every number here is produced by `multimodal.py`. Run `python3 vision.py` to regenerate.

The Transformer does not know it is reading text; it mixes vectors. So anything that can be
turned into a sequence of vectors — image patches, audio frames, video — the same block from
[chapter 02](../02-transformer-forward-pass/) can consume. This chapter is the three moves that
made that real, each measured on a toy: **tokenize** another modality, **align** it with text,
and **generate** in the reverse direction.

---

## 1. An image is a sequence of patches

```
   toy                        32x32x3 pixels ->    16 patches of 8x8x3 =   192 numbers each
   ViT-B/16 at 224            224x224x3 pixels ->   196 patches of 16x16x3 =   768 numbers each
   1024x1024 photo, patch 14  1024x1024x3 pixels -> 5,329 patches of 14x14x3 =   588 numbers each
   toy: image (32, 32, 3) -> patches (16, 192) -> linear projection -> tokens (16, 64)
   from here the transformer block of chapter 02 applies unchanged. an image is ~256-1000 tokens;
   that count is the whole cost of 'looking at a picture'.
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
     step  InfoNCE loss  in-batch acc   (batch 64: chance 1/64; but only 4 classes, so same-class captions collide)
        1         6.268          0.05
       10         3.181          0.08
       50         3.032          0.08
      100         3.037          0.06
      400         2.906          0.03
   zero-shot accuracy on 500 fresh images:  before training 0.268   after 0.998   (chance 0.25)
   the loss is a softmax over the batch -- chapter 03's cross-entropy where the 'vocabulary'
   is the other items in the batch. bigger batch = more negatives = harder, better training.
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
   embed 500 new images; compare each to the 4 class captions; take the nearest:
   accuracy 0.998   (chance 0.25)
   no classifier was trained. the shared space makes 'which caption is closest' a classifier
   for any set of captions you can write. that is CLIP's trick, and the retrieval half of RAG.
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
   forward process: x_t = sqrt(abar_t) x_0 + sqrt(1-abar_t) eps.  abar at t=0,25,49: 0.999 0.248 0.005
   by the last step the data is indistinguishable from pure noise.
   train step     1: denoising loss (MSE on eps) 1.287
   train step   100: denoising loss (MSE on eps) 0.545
   train step  1000: denoising loss (MSE on eps) 0.334
   train step  3000: denoising loss (MSE on eps) 0.280
   sampled 400 points from noise.
   real data x-mean by cluster: -2.01 / 2.02;   samples: -1.82 / 1.73
   fraction of samples in each cluster: 0.51 / 0.49   (data: 0.50 / 0.50)
   training task: predict the noise that was added (plain regression). generation: start from
   noise and subtract predicted noise 50 times. text conditioning adds a caption embedding to
   the input; classifier-free guidance is 'how hard to listen to it'.
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
   16 kHz audio, 25 ms frames, 10 ms hop: 1 second -> 98 frames of 400 samples -> a spectrogram is an image
   video at 24 fps, 256 tokens per frame: 10 seconds -> 61,440 tokens. the token explosion is the problem.
   anything you can turn into a sequence of vectors, the same transformer reads.
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
