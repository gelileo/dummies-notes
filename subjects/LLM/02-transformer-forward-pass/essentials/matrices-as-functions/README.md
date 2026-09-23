# Essential · Matrices as functions

**Needed for:** `W_Q`, `W_K`, `W_V`, `W_O`, the embedding table, the MLP, the LM head — every
learned thing in [chapter 02](../../README.md) is a matrix.

## A matrix is a grid of numbers that acts like a function

You already know functions that take a number and return a number. A matrix is a function that
takes a **vector** and returns a **vector**. Feed it an arrow, get a different arrow back.

```
input           [1.0, 0.0]
   @ stretch-x     [2.0, 0.0]   (x doubled)
   @ rotate 90°    [0.0, 1.0]   (pointing a new way)
```

That is genuinely all a "linear layer" is. When chapter 02 says *"the query is a projection of the
token's vector"*, it means: take the token's vector, pass it through the matrix `W_Q`, get a
different vector out.

A matrix can stretch, shrink, rotate, flatten or mix the axes together — but it always does the
same thing to every input, and it never bends straight lines. That last restriction matters:
see [why non-linearity](../why-nonlinearity/).

## Shapes, and the one rule you need

Write a matrix's size as `[rows, columns]`. Multiplying goes:

```
[n, k] @ [k, m]  ->  [n, m]
```

**The two inner numbers must match, and they disappear.** That is the whole rule, and nearly every
shape error you will ever hit is a violation of it.

```
: [n,k] @ [k,m] -> [n,m]. the inner numbers must match, and they vanish
```

## Every output number is one dot product

```
is one dot product
```

So a matrix multiply is just a lot of [dot products](../vectors-and-dot-products/) arranged in a
grid — row *i* of the left against column *j* of the right lands at position `[i][j]`.

That is exactly what `Q · Kᵀ` is in attention: `[T, d] @ [d, T] -> [T, T]`, a grid where entry
`[i][j]` is "how well does token *i*'s query match token *j*'s key". The `T`s survive and the `d`
vanishes, because `d` is what got summed over.

## Doing two in a row is the same as doing one

```
: doing two matrices in a row IS one matrix ===
   v @ STRETCH @ ROT90 = [0.0, 2.0]
   v @ (STRETCH@ROT90) = [0.0, 2.0]   <- same answer
```

Matrix multiplication **composes**: applying `A` then `B` equals applying the single matrix `A@B`.
Handy — and also a serious problem, which [why non-linearity](../why-nonlinearity/) is about.

## Why this is where the compute goes

A `[n, k] @ [k, m]` multiply costs `n × k × m` multiply-adds. For Llama-3 that is matrices like
`[4096, 14336]` being applied to thousands of tokens — billions of operations per layer, all
independent. Independence is why GPUs are the right hardware: they do thousands of these at once.
That is the whole hardware story in [chapter 11](../../../11-efficiency/).

## Run it

```bash
python3 demo.py
```

## Terms

| Term | Meaning |
| --- | --- |
| **matrix** | A grid of numbers; a function mapping vectors to vectors. |
| **shape** `[n, m]` | *n* rows, *m* columns. |
| **matrix multiplication** `A @ B` | Each output entry is a dot product of a row of `A` with a column of `B`. |
| **transpose** `Aᵀ` | Flip rows and columns. `[n, m]` becomes `[m, n]`. |
| **projection** | Passing a vector through a matrix to get a new vector. What `W_Q`, `W_K`, `W_V` do. |
| **linear layer** | A matrix multiply, sometimes plus a constant. The basic building block. |
| **identity matrix** | 1s on the diagonal, 0s elsewhere. Leaves any vector unchanged. |
