# Essential · Why 4096 dimensions is strange

**Needed for:** understanding why embeddings work at all, and what *superposition* means in
[chapter 02](../../README.md).

Your intuition for space comes from 2 and 3 dimensions. Most of it is wrong at 4096, and the
differences are not footnotes — they are the reason the whole approach works.

## Random directions are almost always perpendicular

Pick two arrows at random and measure the angle between them:

```
        d   mean angle  mean |cosine|   within 10° of 90°
        2        88.4°          0.630                 10%
        3        91.0°          0.493                 19%
       10        87.7°          0.255                 38%
      100        89.9°          0.078                 92%
     1000        90.1°          0.024                100%
     4096        90.0°          0.013                100%
   In 2D, two random arrows are often close together. In 4096D they are
   essentially ALWAYS perpendicular -- there is simply that much room.
```

In 2D two random arrows are frequently close together — only 10% land near perpendicular. In
4096D, **100%** do, and the average `|cosine|` is `0.013`, essentially zero.

This is not a quirk. It is the most important fact about high-dimensional space: **there is so
much room that things are unrelated by default.** Two randomly chosen directions carry no
accidental resemblance to one another.

Which is exactly what an embedding table needs. Give every token a random starting vector and they
all begin mutually unrelated; training then *deliberately* moves the few that should be similar
closer together. Any similarity you measure afterwards is signal, not leftover noise.

## You can pack in far more directions than you have dimensions

Exactly perpendicular directions are limited: `d` dimensions give you exactly `d` of them. But if
*nearly* perpendicular is good enough, the picture changes completely:

```
   exactly perpendicular: only d of them. but if 'nearly' is good enough,
   far more. pack N random directions and measure the WORST overlap:
        d   N packed  worst |cosine| of any pair
       64        500                       0.495
      256      2,000                       0.253
     1024      5,000                       0.145
     4096      5,000                       0.071
   5,000 directions in 4096 dimensions, none overlapping much. That is why a
   4096-number vector can track far more than 4096 features: they are packed
   in as nearly-separate directions rather than perfectly separate ones.
```

5,000 directions in 4096 dimensions, and the worst overlap between any pair is `0.071` — near
enough to unrelated for every practical purpose.

## Superposition

That is what lets a model track more features than it has dimensions. Store several features in
one vector by adding their directions together, then read each one back out with a dot product:

```
   stored 'plural' + 'animal' in one 512-dim vector, then measured each feature:
      plural       0.991   <- present
      past         0.040   
      question     0.053   
      animal       0.991   <- present
```

Two features stored in a single 512-number vector, both read back at `0.99`, with the absent ones
at `0.04` and `0.05` — a clean separation. This is **superposition**: features packed as
nearly-separate directions that overlap slightly, rather than each owning a dimension outright.

Two consequences worth carrying forward:

- A 4096-dimension residual stream can carry **far more than 4096** distinct features.
- **A single dimension rarely means one clean thing.** Features are spread across many dimensions
  and dimensions are shared between features. That is a large part of why interpretability is
  hard, and why researchers hunt for *directions* rather than reading individual numbers.

## Run it

```bash
python3 demo.py
```

## Terms

| Term | Meaning |
| --- | --- |
| **high-dimensional** | Many numbers per vector — 4096 for Llama-3-8B. |
| **nearly orthogonal** | Almost perpendicular; cosine close to 0; effectively unrelated. |
| **superposition** | Packing more features into `d` dimensions than `d`, as nearly-separate directions. |
| **feature** | Something the model tracks — "is plural", "is code", "is a question" — stored as a direction. |
| **direction** | A vector treated as pointing somewhere, with its length ignored. |
