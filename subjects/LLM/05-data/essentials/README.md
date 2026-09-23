# Essentials — the ideas chapter 05 assumes

Chapter 05 is mostly engineering, and a programmer already has most of what it needs. Two ideas
are not standard equipment:

| Article | Read it when you hit… |
| --- | --- |
| [Hashing, Jaccard and MinHash](./hashing-and-set-similarity/) | "near-duplicate", "MinHash", how dedup works on a trillion tokens |
| [Zipf's law and the long tail](./zipf-and-the-long-tail/) | "most tokens appear once", "up-sampling", why rare words are under-trained |

## How this folder is laid out

```text
essentials/
  README.md                       this index
  hashing-and-set-similarity/
    README.md                     the article
    demo.py                       prints the numbers the article quotes
  zipf-and-the-long-tail/
    README.md
    demo.py                       measures Zipf on the curriculum's own 67KB field guide
```

```bash
cd hashing-and-set-similarity && python3 demo.py
```

Standard library only, deterministic.

## Owned here

Zipf is used by chapter 01 (vocabulary size) and chapter 06 (the linguistic instance of a power
law, whose general maths chapter 06 owns). MinHash is chapter 05's alone.
