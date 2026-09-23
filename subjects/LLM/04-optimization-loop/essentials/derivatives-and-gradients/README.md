# Essential · Derivatives and gradients

**Needed for:** *"the gradient tells each weight which way to move"* and every `w -= lr * grad`
in [chapter 04](../../README.md).

## A derivative is a slope

Nudge the input a tiny bit; how much does the output move? That ratio is the derivative. You
can measure it with nothing but arithmetic:

```
   f(x) = x^2
       x   (f(x+h)-f(x))/h    2x
      -2           -4.0000    -4
      -1           -2.0000    -2
       0            0.0000     0
       1            2.0000     2
       3            6.0000     6
   The slope of x^2 is 2x. Negative slope = f is falling as x grows.
```

`(f(x+h) − f(x)) / h` with a tiny `h` — that is the *definition*, and it is also a perfectly good
way to compute one. Chapter 04 uses exactly this to check that its hand-written gradients are
right.

## A gradient is one slope per input

With several inputs, ask the question once per input while holding the others still. Each answer
is a **partial derivative**; the vector of all of them is the **gradient**:

```
   f(x,y) = x^2 + 3y^2   at (1, 1): gradient = (2.000, 6.000)   [exact: (2, 6)]
   f(x,y) = x^2 + 3y^2   at (2, -1): gradient = (4.000, -6.000)   [exact: (4, -6)]
   f(x,y) = x^2 + 3y^2   at (0, 0): gradient = (0.000, 0.000)   [exact: (0, 0)]
   Each entry: hold everything else still, nudge one input, measure. That is a
   'partial derivative'. The vector of all of them is the gradient.
```

A model with 8 billion parameters has a gradient with 8 billion entries — one slope each. Nothing
about the idea changes with size.

## It points uphill, so step the other way

The gradient is the direction of steepest *increase*. To make a loss smaller you subtract it:
`x ← x − lr · gradient`. The size of that step is the **learning rate**, and it is the single most
consequential number in training:

```
   start at (2.0, -1.0), f = 7.000
   small step  lr=0.05: f after each step ->   4.710    3.345    2.479    1.895    1.479    1.171
   good step   lr=0.15: f after each step ->   1.990    0.961    0.471    0.231    0.113    0.055
   too big     lr=0.40: f after each step ->   6.040   11.531   22.589   44.274   86.776  170.082
   Small: creeps. Good: converges. Too big: overshoots and grows -- the same
   picture as a learning rate that is too high.
```

Too small and you crawl. Too large and you overshoot the bottom, land higher up the other side,
and diverge. The same three behaviours show up in chapter 04's learning-rate sweep on a real
model.

## Run it

```bash
python3 demo.py
```

## Terms

| Term | Meaning |
| --- | --- |
| **derivative** | Slope of a function at a point: how much the output moves per tiny nudge of the input. |
| **finite difference** | `(f(x+h) − f(x)) / h` for small `h`. The definition, used as a check. |
| **partial derivative** | The derivative with respect to one input, all others held still. |
| **gradient** | The vector of all partial derivatives. Points in the direction of steepest increase. |
| **gradient descent** | Repeatedly step *against* the gradient to make a function smaller. |
| **learning rate** | The step size multiplier. Too small crawls, too large diverges. |
| **minimum** | A point where the gradient is zero and the function is locally smallest. |
