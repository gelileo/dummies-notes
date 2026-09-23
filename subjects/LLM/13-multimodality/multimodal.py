#!/usr/bin/env python3
"""Multimodality, measured: patchify an image into tokens; train a CLIP-style contrastive
model on synthetic (image, caption) pairs and do zero-shot classification with it; and train
a tiny diffusion denoiser on 2-D points and sample from it. numpy.  Run: python3 multimodal.py
"""
import numpy as np
rng = np.random.default_rng(0)
def softmax(z, axis=-1): e = np.exp(z - z.max(axis, keepdims=True)); return e / e.sum(axis, keepdims=True)

if __name__ == "__main__":
    np.set_printoptions(precision=3, suppress=True)

    print("=== 1. an image is a sequence of patches ===")
    for name, hw, patch in (("toy", (32, 32), 8), ("ViT-B/16 at 224", (224, 224), 16), ("1024x1024 photo, patch 14", (1024, 1024), 14)):
        n = (hw[0]//patch) * (hw[1]//patch); dim = patch*patch*3
        print(f"   {name:<26} {hw[0]}x{hw[1]}x3 pixels -> {n:>5,} patches of {patch}x{patch}x3 = {dim:>5} numbers each")
    img = rng.random((32, 32, 3))
    patches = img.reshape(4, 8, 4, 8, 3).transpose(0, 2, 1, 3, 4).reshape(16, -1)   # [16 patches, 192]
    Wp = rng.normal(0, .05, (192, 64)); tokens = patches @ Wp
    print(f"   toy: image {img.shape} -> patches {patches.shape} -> linear projection -> tokens {tokens.shape}")
    print("   from here the transformer block of chapter 02 applies unchanged. an image is ~256-1000 tokens;")
    print("   that count is the whole cost of 'looking at a picture'.")

    print("\n=== 2. contrastive learning: pull matched pairs together, push everything else apart ===")
    # synthetic world: 4 classes. an 'image' is a noisy 16-d class prototype; a 'caption' is a noisy 12-d prototype.
    C, DI, DT, DE = 4, 16, 12, 8
    img_proto = rng.normal(size=(C, DI)); txt_proto = rng.normal(size=(C, DT))
    def make(n):
        y = rng.integers(0, C, n)
        return img_proto[y] + 0.6*rng.normal(size=(n, DI)), txt_proto[y] + 0.6*rng.normal(size=(n, DT)), y
    Wi = rng.normal(0, .1, (DI, DE)); Wt = rng.normal(0, .1, (DT, DE)); temp = 0.1
    def encode(X, W):
        Z = X @ W; n = np.linalg.norm(Z, axis=1, keepdims=True); return Z / n, Z, n
    def infonce(I, Tt):
        logits = I @ Tt.T / temp                          # [B, B]: image i vs caption j
        B = len(I); tgt = np.arange(B)
        li = -np.log(softmax(logits)[tgt, tgt]).mean()    # each image should pick its own caption
        lt = -np.log(softmax(logits.T)[tgt, tgt]).mean()  # and each caption its own image
        return (li + lt) / 2, logits
    def zero_shot_acc():
        Xi_, _, y_ = make(500); I_ = encode(Xi_, Wi)[0]; Tn = encode(txt_proto, Wt)[0]
        return np.mean((I_ @ Tn.T).argmax(1) == y_)
    acc_before = zero_shot_acc()
    print(f"   {'step':>6}{'InfoNCE loss':>14}{'in-batch acc':>14}   (batch 64: chance 1/64; but only 4 classes, so same-class captions collide)")
    for step in range(1, 401):
        Xi, Xt, y = make(64)
        (I, Zi, ni), (Tt, Zt, nt) = encode(Xi, Wi), encode(Xt, Wt)
        loss, logits = infonce(I, Tt)
        B = len(I); P = softmax(logits); Q = softmax(logits.T)
        dI = ((P - np.eye(B)) @ Tt + (Q - np.eye(B)).T @ Tt) / (2*B*temp)   # d loss / d normalised image emb
        dT = ((P - np.eye(B)).T @ I + (Q - np.eye(B)) @ I) / (2*B*temp)
        # chain through the normalisation: d(z/|z|) = (I - u u^T) / |z|
        dZi = (dI - I * (I * dI).sum(1, keepdims=True)) / ni
        dZt = (dT - Tt * (Tt * dT).sum(1, keepdims=True)) / nt
        Wi -= 0.05 * Xi.T @ dZi; Wt -= 0.05 * Xt.T @ dZt
        if step in (1, 10, 50, 100, 400):
            acc = (logits.argmax(1) == np.arange(B)).mean()
            print(f"   {step:>6}{loss:>14.3f}{acc:>14.2f}")
    print(f"   zero-shot accuracy on 500 fresh images:  before training {acc_before:.3f}   after {zero_shot_acc():.3f}   (chance 0.25)")
    print("   the loss is a softmax over the batch -- chapter 03's cross-entropy where the 'vocabulary'")
    print("   is the other items in the batch. bigger batch = more negatives = harder, better training.")

    print("\n=== 3. zero-shot classification: nearest caption wins ===")
    Xi, _, y = make(500)
    I = encode(Xi, Wi)[0]; T_names = encode(txt_proto, Wt)[0]    # 'a photo of a <class k>' for each class
    pred = (I @ T_names.T).argmax(1)
    print(f"   embed 500 new images; compare each to the 4 class captions; take the nearest:")
    print(f"   accuracy {np.mean(pred == y):.3f}   (chance 0.25)")
    print("   no classifier was trained. the shared space makes 'which caption is closest' a classifier")
    print("   for any set of captions you can write. that is CLIP's trick, and the retrieval half of RAG.")

    print("\n=== 4. diffusion: learn to remove a little noise, then remove it many times ===")
    # data: points on two clusters in 2-D
    def data(n): c = rng.integers(0, 2, n); return np.stack([c*4.0 - 2.0 + 0.3*rng.normal(size=n), 0.3*rng.normal(size=n)], 1)
    STEPS = 50; betas = np.linspace(1e-3, 0.2, STEPS); alphas = 1 - betas; abar = np.cumprod(alphas)
    print(f"   forward process: x_t = sqrt(abar_t) x_0 + sqrt(1-abar_t) eps.  abar at t=0,25,49: {abar[0]:.3f} {abar[25]:.3f} {abar[49]:.3f}")
    print("   by the last step the data is indistinguishable from pure noise.")
    # denoiser: small MLP predicting eps from (x_t, t)
    H = 64; W1 = rng.normal(0, .3, (3, H)); b1 = np.zeros(H); W2 = rng.normal(0, .3, (H, 2)); b2 = np.zeros(2)
    def net(x, t):
        inp = np.concatenate([x, (t/STEPS)[:, None]], 1); h = np.tanh(inp @ W1 + b1); return h @ W2 + b2, h, inp
    lr = 0.01
    for step in range(1, 3001):
        x0 = data(256); t = rng.integers(0, STEPS, 256); eps = rng.normal(size=x0.shape)
        xt = np.sqrt(abar[t])[:, None]*x0 + np.sqrt(1-abar[t])[:, None]*eps
        pred, h, inp = net(xt, t); d = 2*(pred - eps)/256
        gW2 = h.T @ d; gb2 = d.sum(0); dh = d @ W2.T * (1-h*h); gW1 = inp.T @ dh; gb1 = dh.sum(0)
        W2 -= lr*gW2; b2 -= lr*gb2; W1 -= lr*gW1; b1 -= lr*gb1
        if step in (1, 100, 1000, 3000):
            print(f"   train step {step:>5}: denoising loss (MSE on eps) {np.mean((pred-eps)**2):.3f}")
    # sample: start from noise, step backwards
    x = rng.normal(size=(400, 2))
    for t in range(STEPS-1, -1, -1):
        eps_hat, _, _ = net(x, np.full(400, t))
        x = (x - betas[t]/np.sqrt(1-abar[t]) * eps_hat) / np.sqrt(alphas[t])
        if t > 0: x += np.sqrt(betas[t]) * rng.normal(size=x.shape)
    real = data(400)
    print(f"   sampled 400 points from noise.")
    print(f"   real data x-mean by cluster: {real[real[:,0]<0,0].mean():.2f} / {real[real[:,0]>0,0].mean():.2f};   samples: {x[x[:,0]<0,0].mean():.2f} / {x[x[:,0]>0,0].mean():.2f}")
    print(f"   fraction of samples in each cluster: {np.mean(x[:,0]<0):.2f} / {np.mean(x[:,0]>0):.2f}   (data: 0.50 / 0.50)")
    print("   training task: predict the noise that was added (plain regression). generation: start from")
    print("   noise and subtract predicted noise 50 times. text conditioning adds a caption embedding to")
    print("   the input; classifier-free guidance is 'how hard to listen to it'.")

    print("\n=== 5. audio, video: the same move ===")
    print(f"   16 kHz audio, 25 ms frames, 10 ms hop: 1 second -> {int((16000 - 400)/160)+1} frames of 400 samples -> a spectrogram is an image")
    print(f"   video at 24 fps, 256 tokens per frame: 10 seconds -> {24*10*256:,} tokens. the token explosion is the problem.")
    print("   anything you can turn into a sequence of vectors, the same transformer reads.")
