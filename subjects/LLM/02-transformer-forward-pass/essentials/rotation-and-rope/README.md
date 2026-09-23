# Essential · Rotation, and how RoPE encodes position

**Needed for:** positional encoding and RoPE in [chapter 02](../../README.md), and context extension
in [chapter 12](../../../12-context-and-knowledge/).

## Attention cannot see order

Attention compares every token with every other by dot product. Nothing in that comparison says
*where* either token sits — it is a set operation. "dog bites man" and "man bites dog" produce
identical queries, keys and values. Position has to be added deliberately.

The modern answer is to **rotate** each query and key by an angle that depends on its position.

## Rotating a point needs only sin and cos

```python
def rotate(x, y, angle):
    return (x*cos(angle) - y*sin(angle),
            x*sin(angle) + y*cos(angle))
```

```
     angle                 point
       0°   ( 1.000,  0.000)
      45°   ( 0.707,  0.707)
      90°   ( 0.000,  1.000)
     180°   (-1.000,  0.000)
     270°   (-0.000, -1.000)
```

Take the pair of numbers `(x, y)` as a point on a page and swing it around the origin. Sine and
cosine are just the machinery for "how far across and how far up does it land".

Crucially, **rotation does not change length**:

```
       0°   (  3.00,   4.00)   length 5.000
      37°   ( -0.01,   5.00)   length 5.000
      90°   ( -4.00,   3.00)   length 5.000
     211°   ( -0.51,  -4.97)   length 5.000
```

It turns a vector without stretching it. The information is all still there, pointed a new way —
which is why you can do this to a query vector without destroying what it means.

## The property RoPE is built on

```
   rotate BOTH vectors by the same amount and their dot product is unchanged;
   rotate them by DIFFERENT amounts and it depends only on the difference.
   positions (0,0)  gap  0   dot =  0.8000
   positions (1,1)  gap  0   dot =  0.8000
   positions (5,5)  gap  0   dot =  0.8000
   positions (0,1)  gap  1   dot =  0.4144
   positions (0,2)  gap  2   dot = -0.0726
   positions (3,5)  gap  2   dot = -0.0726
   Same gap -> same dot product, wherever the pair sits in the sequence.
   That is relative position, for free.
```

Rotate two vectors by different amounts and their dot product depends **only on the difference**
between those amounts. Positions 0 and 2 give the same answer as positions 3 and 5, because both
are two apart.

So: rotate each token's query and key by an angle proportional to its position, and every
attention score automatically becomes sensitive to **how far apart** the two tokens are, never to
where they sit absolutely. Relative position, with no extra parameters and nothing learned.

That is RoPE — *rotary position embedding*. It rotates pairs of dimensions `(0,1)`, `(2,3)`,
`(4,5)`… each pair treated as a little 2D point.

## Many speeds at once

Each pair of dimensions gets its own rotation speed:

```
     d_head   pairs   fastest rad/pos   slowest rad/pos
          4       2            1.0000          0.010000
         64      32            1.0000          0.000133
        128      64            1.0000          0.000115
   Fast pairs encode 'near or far'. Slow pairs barely move, so they carry
   meaning across long distances untouched. A d_head of 4 has no slow pairs,
   which is why the toy model in this chapter exaggerates RoPE's effect.
```

Fast pairs spin a lot per position, so they resolve "is this token near or far" sharply but wrap
around quickly. Slow pairs barely move across thousands of positions, so they carry meaning over
long distances essentially untouched. Using all the speeds at once gives both.

**This is also why the toy model in chapter 02 exaggerates RoPE.** With `d_head = 4` there are
only 2 pairs and the slowest still rotates 0.01 radians per position — there are no genuinely slow
pairs to protect the content. Llama-3's 64 pairs span four orders of magnitude, so most of them
hold content steady while a handful encode position.

**And it is why context can be extended after training.** Since position enters only as a rotation
angle, you can *slow all the angles down* and a model trained on 8k tokens will work at 128k —
the basis of position interpolation, NTK-aware scaling and YaRN.
→ [chapter 12](../../../12-context-and-knowledge/)

## Run it

```bash
python3 demo.py
```

## Terms

| Term | Meaning |
| --- | --- |
| **sine / cosine** | Functions giving the vertical and horizontal parts of an angle. Together they rotate points. |
| **radian** | An angle unit. A full turn is 2π ≈ 6.28 radians; 1 radian ≈ 57°. |
| **rotation** | Turning a vector about the origin. Changes direction, never length. |
| **absolute position** | Where a token sits in the sequence: 0, 1, 2… |
| **relative position** | How far apart two tokens are. What RoPE actually makes scores depend on. |
| **RoPE** | Rotary position embedding: rotate query and key by an angle proportional to position. |
