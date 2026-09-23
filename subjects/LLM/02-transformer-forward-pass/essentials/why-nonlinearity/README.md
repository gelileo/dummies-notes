# Essential · Why a network needs a bend

**Needed for:** the MLP, SiLU and SwiGLU in [chapter 02](../../README.md) — and the answer to "why
does depth help at all?"

## The problem: stacked matrices collapse

[A matrix is a function](../matrices-as-functions/), and applying two in a row is the same as
applying one combined matrix. That is convenient — and it is fatal if matrices are all you have:

```
   x @ W1 @ W2 @ W3   = [-14.755984, -0.611764, -12.896185]
   x @ (W1 @ W2 @ W3) = [-14.755984, -0.611764, -12.896185]
   identical: True
   So without something non-linear between them, depth buys NOTHING:
   a 100-layer linear network is exactly one matrix wearing a costume.
```

Three layers produced a result you could have got from a single matrix. Extend that argument and
**a 100-layer purely-linear network is exactly one matrix wearing a costume.** All that depth,
all those parameters, and the family of functions it can express is no larger than one layer's.

The reason is that matrix operations only ever stretch, rotate and mix axes. Straight lines stay
straight, and whatever you compose from those stays in the same restricted family.

## The fix: bend the line between layers

Put a simple, non-straight function between the matrices — applied to each number on its own:

```
        x   relu(x)   silu(x)
       -3     0.000    -0.142
       -2     0.000    -0.238
       -1     0.000    -0.269
     -0.5     0.000    -0.189
        0     0.000     0.000
      0.5     0.500     0.311
        1     1.000     0.731
        2     2.000     1.762
        3     3.000     2.858
   Both flatten negatives and pass positives. SiLU does it smoothly, with
   no corner at zero - which makes it easier to train.
```

- **ReLU** — `max(0, x)`. Negatives become 0, positives pass through. One sharp corner.
- **SiLU** — `x · sigmoid(x)`. The same shape with the corner smoothed off, and it lets slightly
  negative values through instead of flattening them entirely. What modern models use.

The corner is the whole point. That single bend is enough that stacked layers stop collapsing:

```
   linear only      [-14.756, -0.6118, -12.8962]
   with SiLU        [-0.0, -0.2658, -0.0001]
   The second cannot be written as a single matrix. That is what depth is for.
```

The second result **cannot** be written as any single matrix. Now depth buys something: each extra
layer genuinely expands what the network can express, and with enough of them it can approximate
essentially any function.

## Where chapter 02 uses this

**SwiGLU**, the MLP's shape, is two up-projections where one is passed through SiLU and used to
**gate** the other — multiply them together elementwise — before projecting back down:

```python
hidden = silu(x @ W_gate) * (x @ W_up)
out    = hidden @ W_down
```

Two non-linear things are happening: the SiLU bend, and the multiplication of two computed values
(multiplying two things that both depend on `x` is itself non-linear). Gating lets the network
learn *"pass this through only when that other condition holds"*, which a plain bend cannot
express as directly.

**Attention has its own non-linearity**: [softmax](../softmax-and-probability/). Without it,
attention would also collapse into a single linear operation.

So every sublayer in the Transformer contains exactly one source of non-linearity — softmax in
attention, SiLU-and-gating in the MLP — and those are what make 32 stacked blocks worth more than
one.

## Run it

```bash
python3 demo.py
```

## Terms

| Term | Meaning |
| --- | --- |
| **linear** | Straight-line behaviour: scaling the input scales the output, and adding inputs adds outputs. |
| **non-linear** | Anything else. A bend, a corner, a multiplication of two variable things. |
| **activation function** | The small non-linear function applied to each number between layers. |
| **ReLU** | `max(0, x)`. The classic activation. |
| **sigmoid** | Squashes any number into the range 0–1. |
| **SiLU / Swish** | `x · sigmoid(x)`. A smooth ReLU, used in modern models. |
| **gating** | Multiplying one computed vector by another, so one controls how much of the other passes. |
| **SwiGLU** | The modern MLP: SiLU on one projection, used to gate a second, then projected down. |
