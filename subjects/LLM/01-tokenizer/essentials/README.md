# Essentials — the ideas chapter 01 assumes

Chapter 01 is the most self-contained chapter, and a programmer has most of it. Two ideas are
worth their own page because the chapter's guarantees rest on them:

| Article | Read it when you hit… |
| --- | --- |
| [UTF-8 and bytes](./utf-8-and-bytes/) | "ids 0–255 are the raw bytes", "nothing is unrepresentable", the streaming `\ufffd` glitch |
| [Compression and information](./compression-and-information/) | "the tokenizer is a compression scheme", "merge the most frequent pair", "bits per token" |

## How this folder is laid out

```text
essentials/
  README.md                       this index
  utf-8-and-bytes/
    README.md                     the article
    demo.py                       prints the bytes the article quotes
  compression-and-information/
    README.md
    demo.py                       Huffman vs BPE on the field guide
```

```bash
cd compression-and-information && python3 demo.py
```

Standard library only; deterministic.

## Owned here

Compression-as-information is the bridge into [chapter 03](../../03-training-objective/)'s
"loss is bits"; UTF-8 is referenced by [10](../../10-inference-and-decoding/) (streaming).
