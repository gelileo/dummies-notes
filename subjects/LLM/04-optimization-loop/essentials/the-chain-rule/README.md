# Essential · The chain rule, and why backprop runs backwards

**Needed for:** *"backpropagation is the chain rule applied mechanically"* in
[chapter 04](../../README.md), and `autograd.py` there.

## Composing functions multiplies their slopes

If `y` depends on `u` and `u` depends on `x`, then a nudge to `x` moves `u` by `du/dx`, and that
movement of `u` moves `y` by `dy/du`. The total effect is the product:

```
   y = (3x+1)^2 at x=2.0:  u = 7.0
   dy/du = 2u = 14.0      du/dx = 3
   chain rule: dy/dx = dy/du * du/dx = 14.0 * 3 = 42.0
   numeric check:            42.000
```

That is the chain rule in full: **`dy/dx = dy/du × du/dx`**. It is not a special case; it is how
sensitivities combine whenever one thing feeds into another.

## A longer chain

```
   d = 5*exp(sin(x^2)) at x=0.5
   local slopes: dd/dc=5  dc/db=1.2807  db/da=0.9689  da/dx=1.0
   product = 6.2044
   numeric  = 6.2044
```

A neural network is a chain thousands of steps deep. Every operation knows its own local slope
— `2x`, `cos`, `exp`, or for a matrix multiply, the other matrix — and the gradient of the loss
with respect to anything is the product of the local slopes along the path from it to the loss.

## Why "backward"

```
   a loss is ONE number that depends on MILLIONS of parameters.
   forward-mode: one pass per input -> millions of passes.
   reverse-mode: start at the output with slope 1, walk back once,
   multiplying local slopes; every input gets its gradient in ONE pass.
               10 parameters: forward-mode             10 passes   reverse-mode 1 pass
            1,000 parameters: forward-mode          1,000 passes   reverse-mode 1 pass
    8,000,000,000 parameters: forward-mode  8,000,000,000 passes   reverse-mode 1 pass
```

A loss is one number that depends on millions of parameters. Going *forward* — asking "how does
the loss change if I nudge parameter *i*?" — costs one full pass per parameter. Going
*backward* — starting at the loss with a slope of 1 and multiplying local slopes as you walk
towards the inputs — gets every parameter's gradient in a single pass. That asymmetry is the
entire reason deep learning is computationally possible, and it is why the algorithm is called
back-propagation.

## The failure mode, and what fixed it

```
     1 layers, local slope 0.5 each: gradient x 5.00e-01
     5 layers, local slope 0.5 each: gradient x 3.12e-02
    10 layers, local slope 0.5 each: gradient x 9.77e-04
    20 layers, local slope 0.5 each: gradient x 9.54e-07
    50 layers, local slope 0.5 each: gradient x 8.88e-16
   this is why deep nets were untrainable -- and why the residual connection's
   '+1' slope (chapter 02) fixed it: 1 + small, multiplied, stays near 1.
    10 layers of (1 + 0.5*small): x 1.63  -- survives
    50 layers of (1 + 0.5*small): x 11.47  -- survives
```

Multiply twenty slopes below 1 and nothing survives — the **vanishing gradient**. Early layers
receive no signal and never learn. This is why deep networks were untrainable until residual
connections ([chapter 02](../../../02-transformer-forward-pass/)) added a `+1` to every layer's
local slope: `1 + small` multiplied many times stays near 1.

## Run it

```bash
python3 demo.py
```

## Terms

| Term | Meaning |
| --- | --- |
| **chain rule** | The derivative of a composition is the product of the derivatives: `dy/dx = dy/du · du/dx`. |
| **local slope / local derivative** | The derivative of one operation with respect to its own input, ignoring everything else. |
| **backpropagation** | Computing every parameter's gradient by walking from the loss back to the inputs, multiplying local slopes. |
| **reverse mode** | The direction backprop runs: output to inputs. One pass for all gradients. |
| **forward mode** | Input to output. One pass *per input* — too expensive for millions of parameters. |
| **vanishing gradient** | Many slopes below 1 multiplied together → gradient ≈ 0 → early layers stop learning. |
| **computation graph** | The record of which operations produced which values; what backward walks. |
