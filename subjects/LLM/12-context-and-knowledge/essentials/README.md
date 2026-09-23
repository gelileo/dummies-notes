# Essentials — the ideas chapter 12 assumes

Two classical pieces of information retrieval a programmer may not have met:

| Article | Read it when you hit… |
| --- | --- |
| [TF-IDF and BM25](./tf-idf-and-bm25/) | "keyword retrieval", "BM25", "hybrid search", why 'the' weighs nothing |
| [Nearest-neighbour search](./nearest-neighbour-search/) | "vector database", "HNSW", "approximate", "recall" |

Vectors and cosine similarity are owned by [chapter 02](../../02-transformer-forward-pass/essentials/vectors-and-dot-products/);
rotation and RoPE by [chapter 02](../../02-transformer-forward-pass/essentials/rotation-and-rope/).

## How this folder is laid out

```text
essentials/
  README.md                       this index
  tf-idf-and-bm25/
    README.md                     the article
    demo.py                       prints the numbers the article quotes
  nearest-neighbour-search/
    README.md
    demo.py
```

```bash
cd tf-idf-and-bm25 && python3 demo.py
```

Standard library and numpy; deterministic.

## Owned here

Nearest-neighbour search is referenced by [13](../../13-multimodality/) (retrieval over image
embeddings).
