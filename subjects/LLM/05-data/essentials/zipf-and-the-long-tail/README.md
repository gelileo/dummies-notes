# Essential · Zipf's law and the long tail

**Needed for:** *"most tokens appear once"*, *"rare tokens get almost no training signal"* in
[chapter 05](../../README.md), and the vocabulary-size argument in [chapter 01](../../../01-tokenizer/).

## Measured on a real document

Word counts in the 67KB field guide this curriculum started from:

```
    rank        word  count  rank x count  share of text
       1         the    627           627           5.9%
       2           a    409           818           3.8%
       3         and    310           930           2.9%
       4          is    232           928           2.2%
       5          of    203          1015           1.9%
      10          it    120          1200           1.1%
      20        each     51          1020           0.5%
      50        line     28          1400           0.3%
     100          do     14          1400           0.1%
     500       short      4          2000           0.0%
   rank x count hovers around a constant: that is Zipf's law. the 2nd word is
   about half as common as the 1st, the 10th about a tenth, and so on.
```

**Rank × count stays roughly constant.** The second most common word appears about half as often
as the first, the tenth about a tenth as often. That regularity is **Zipf's law**, and it holds
for every natural-language corpus anyone has measured, at every scale.

## A tiny head, an enormous tail

```
   top   10 words cover  23.0% of all text
   top  100 words cover  49.4% of all text
   top  500 words cover  75.5% of all text
   words seen exactly once: 1,040 of 2,163 distinct (48%)
   words seen fewer than 5 times: 1,740 (80%)
```

A few hundred words account for most of what is written. Meanwhile more than half of all
*distinct* words appear exactly once in ten thousand — and that ratio barely improves as the
corpus grows, because new rare words keep arriving.

## A straight line on log-log axes

```
     log10 rank  log10 count
           0.00         2.80
           1.00         2.08
           2.00         1.15
           3.00         0.30
   each 10x in rank costs roughly one unit of log10 count: slope about -1.
   (chapter 06 owns the general power-law maths; this is the linguistic instance.)
```

Each 10× step in rank costs about one unit of `log10 count` — slope near −1. That straight line is
the fingerprint of a **power law**, and [chapter 06](../../../06-planning-a-run/) owns the general
maths of fitting and reading one. This is the linguistic instance.

## Why it matters for training

```
   a token's embedding is updated once per occurrence. the token at rank 1 got
   627 updates from this document; a rank-1000 token got 2.
   half the vocabulary is essentially untrained on any given corpus. subword
   tokenization (chapter 01) exists partly to pool that signal.
```

A token's embedding is updated once per occurrence. The head gets hundreds of thousands of
updates; the tail gets a handful. Half the vocabulary is, in effect, barely trained on any given
corpus. Two things in this curriculum exist largely because of that: subword tokenization
([chapter 01](../../../01-tokenizer/)), which lets rare words share pieces with common ones, and
the data-mixture decisions in chapter 05, which deliberately up-sample sources that would
otherwise sit in the tail.

## Run it

```bash
python3 demo.py
```

## Terms

| Term | Meaning |
| --- | --- |
| **Zipf's law** | Frequency ∝ 1/rank. The *r*-th most common word appears about 1/*r* as often as the most common. |
| **rank** | Position in the sorted-by-frequency list. |
| **long tail** | The huge number of items that each occur rarely. |
| **head** | The few items that account for most occurrences. |
| **hapax** | A word that appears exactly once in a corpus. Often half the vocabulary. |
| **power law** | `y ∝ xᵇ`. A straight line on log-log axes. Zipf is one with `b ≈ −1`. |
| **up-sampling** | Repeating an under-represented source so the model sees it more often than its natural share. |
