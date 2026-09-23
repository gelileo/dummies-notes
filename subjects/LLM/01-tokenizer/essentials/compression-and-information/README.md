# Essential · Compression and information

**Needed for:** *"the tokenizer is a compression scheme"*, *"merge the most frequent pair"* in
[chapter 01](../../README.md), and the bridge to *"loss in bits per token"* in
[chapter 03](../../../03-training-objective/).

Measured on the curriculum's own field guide (67,652 bytes).

## The baseline: eight bits for everything

```
   67,652 bytes x 8 = 541,216 bits.  8.000 bits per byte. this is the baseline.
```

## The floor: entropy

```
   125 distinct byte values. entropy = 4.691 bits per byte.
   no code that assigns one codeword per byte can average fewer bits than this.
```

If you assign one codeword per byte, no scheme can average fewer bits than the entropy of the
byte distribution ([chapter 03's essential](../../../03-training-objective/essentials/entropy-and-cross-entropy/)).
Here that is 4.69 bits — already far below 8, because text is nothing like uniform.

## Huffman: frequent bytes get short codes

```
     byte   count  code length   code
      ' '   10622            3   110
      'e'    6539            3   000
      't'    4759            4   1011
      'a'    4145            4   1001
      '%'       1           17   11110101101000110
      '¦'       1           16   1000101001100001
   total 319,283 bits = 4.719 bits per byte   (entropy floor 4.691; fixed width 8.000)
   the most common byte gets a 3-bit code; the rarest get 15+. that is the whole idea.
```

Build the code by repeatedly joining the two least frequent symbols. The space character gets
three bits; a byte that appears once gets seventeen. Total 4.72 bits per byte — within a hair of
the entropy floor. **Frequent things should be cheap to write down.** That sentence is the whole
of information theory as it applies here.

## BPE is the same principle, one level up

```
    merges   tokens  vocab bits/token   total bits  bits per byte
         0   67,652    256       8.00      541,216          8.000
        24   52,928    280       8.13      430,267          6.360
       100   40,218    356       8.48      340,877          5.039
       300   31,664    556       9.12      288,742          4.268
   more merges: fewer tokens, each costing a little more to name. the product falls below
   Huffman's per-byte code because a token captures a whole frequent string at once.
   (this uses a fixed log2(vocab) bits per token; a real compressor would Huffman-code the
    tokens too and do better still.)
```

Huffman shortens the code for a frequent *byte*. BPE gives a frequent *string* a single token. More
merges mean fewer tokens, each slightly more expensive to name, and the product drops **below what
any per-byte code can reach** — because a token captures a whole common string in one symbol.
Chapter 01's "merge the most frequent pair" is greedy compression, and now you can see the number
it is minimising.

## The through-line

```
   chapter 03 measures a model in bits per token. a model that predicts well IS a good code:
   assign -log2 p bits to each token and the total is the compressed size. tokenizer, Huffman,
   language model -- three rungs of one ladder: frequent things should be cheap to write down.
```

## Run it

```bash
python3 demo.py
```

## Terms

| Term | Meaning |
| --- | --- |
| **fixed-width code** | Every symbol costs the same number of bits. 8 per byte. |
| **entropy** | The average surprise of a source; the floor on bits per symbol for any per-symbol code. |
| **Huffman coding** | Build a prefix code by merging the two least frequent symbols repeatedly. Near-optimal per symbol. |
| **prefix code** | No codeword is the start of another, so a bit stream decodes unambiguously. |
| **bits per byte / per token** | Compression ratio, in the units the loss uses. |
| **greedy compression** | Take the step that shrinks the total most right now. BPE's merge rule. |
