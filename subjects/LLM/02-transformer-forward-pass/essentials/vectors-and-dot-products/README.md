# Essential · Vectors and dot products

**Needed for:** attention scores, embeddings, cosine similarity — everything in
[chapter 02](../../README.md) that talks about "direction" or "alignment".

## A vector is a list of numbers. That is the whole definition.

`[3, 4]` is a vector. So is `[0.2, -1.7, 0.03, ...]` with four thousand entries. In code it is an
array, and nothing more.

The *useful* part is a second way of seeing it: a vector is **an arrow pointing somewhere**.
`[3, 4]` means "go 3 along, 4 up". The numbers are directions-and-distances along each axis.

With two numbers you can draw it on paper. With three you can imagine it in a room. With 4096 you
cannot picture it at all — and you do not need to. Every rule below is arithmetic that works the
same at any size.

Two things about an arrow matter separately:

- **Its length** — how big it is. `[6, 8]` is twice as long as `[3, 4]`, pointing the same way.
- **Its direction** — which way it points, regardless of size.

For meaning, direction is usually what counts. A word that appears often may get a longer vector
without meaning anything different.

## The dot product

Multiply the two lists entry by entry, then add it all up:

```python
dot(a, b) = sum(x*y for x, y in zip(a, b))
dot([1,2,3], [4,5,6]) = 1*4 + 2*5 + 3*6 = 32
```

One line, one loop. And it computes something surprisingly useful: **how much two vectors point
the same way**.

```
angle    a . b   cosine   meaning
       0°    1.000    1.000   same direction
      30°    0.866    0.866   
      60°    0.500    0.500   
      90°    0.000    0.000   perpendicular - unrelated
     120°   -0.500   -0.500   
     180°   -1.000   -1.000   opposite
```

**Where those numbers come from.** `a` is fixed at `[1, 0]` and `b` is built as
`[cos(angle), sin(angle)]` — a point swept around a circle of radius 1. So the second term of the
dot product is always multiplied by zero and the whole thing collapses to `cos(angle)`:

```
       0°   [  1.000,   0.000]      1*  1.000 + 0*  0.000 =   1.000
      30°   [  0.866,   0.500]      1*  0.866 + 0*  0.500 =   0.866
      60°   [  0.500,   0.866]      1*  0.500 + 0*  0.866 =   0.500
      90°   [  0.000,   1.000]      1*  0.000 + 0*  1.000 =   0.000
     120°   [ -0.500,   0.866]      1* -0.500 + 0*  0.866 =  -0.500
     180°   [ -1.000,   0.000]      1* -1.000 + 0*  0.000 =  -1.000
```

They are the values you met in school: `cos 30° = √3/2 = 0.866`, `cos 60° = 1/2`,
`cos 120° = −1/2`.

Read the column: positive when two vectors point the same way, **zero when they are
perpendicular**, negative when opposed. A similarity score for the cost of one loop.

## The identity underneath

```
a · b  =  |a| × |b| × cos(angle)
```

A dot product is **length × length × alignment**. In the table above both vectors have length 1,
so the lengths drop out and the dot product *is* the cosine — which is why those two columns are
identical there. In general they are not:

```
                              vectors    a . b   cosine   equal?   note
                [1,0] . [0.866,0.500]    0.866    0.866      yes   both length 1
                [3,0] . [0.866,0.500]    2.598    0.866       no   a is 3x longer
                [3,0] . [8.660,5.000]   25.981    0.866       no   both longer
   The angle is 30° in all three rows. Only the cosine column knows that.
```

The angle is 30° in every row. The dot product reports 0.866, then 2.598, then 25.981, because it
measures size and alignment mixed together. Only the cosine stays at 0.866.

That matters in chapter 02: an attention score is a **raw dot product**, so it grows when query
and key vectors are simply longer, not just better matched. Keeping those scores in a usable
range is what [averages and normalization](../averages-and-normalization/) is about.

## Length versus direction

```
a = [3,4]                length 5.00
   b = [6,8]  (a doubled)   length 10.00
   c = [4,3]                length 5.00
   a.b = 50.0 but cosine(a,b) = 1.000  -> same direction, different size
   a.c = 24.0 and cosine(a,c) = 0.960  -> same size, different direction
```

The dot product mixes both together — it grows if you just make a vector longer. **Cosine
similarity** divides that out, leaving direction only:

```python
cosine(a, b) = dot(a, b) / (length(a) * length(b))
```

It always lands between −1 and 1: `1` same direction, `0` unrelated, `−1` opposite. When people
say two embeddings are "close", this is usually the number they mean.

## Where chapter 02 uses this

**Every attention score is a dot product.** A token's query is compared against another token's
key with exactly the loop above. A big score means "what I am looking for matches what you have";
zero means "you are irrelevant to me". The `'it'` → `'trophy'` match in
[`forward-pass.md`](../../forward-pass.md) is a single dot product coming out large.

`Q · Kᵀ` is just *all* of those dot products at once — every query against every key — arranged
in a grid. See [matrices as functions](../matrices-as-functions/).

## Run it

```bash
python3 demo.py
```

## Terms

| Term | Meaning |
| --- | --- |
| **vector** | A list of numbers; equivalently an arrow with a length and a direction. |
| **dimension** | How many numbers are in the list. `d_model = 4096` means 4096-number vectors. |
| **length / magnitude / norm** | How long the arrow is: `sqrt(dot(v, v))`. |
| **dot product** | Multiply entrywise, sum. Large when two vectors point the same way. |
| **cosine similarity** | Dot product with the lengths divided out, so only direction counts. Always between −1 and 1. |
| **orthogonal / perpendicular** | At right angles; dot product exactly zero; completely unrelated. |
