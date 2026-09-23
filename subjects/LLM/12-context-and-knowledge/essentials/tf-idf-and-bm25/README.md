# Essential · TF-IDF and BM25

**Needed for:** *"keyword retrieval"*, *"BM25"*, *"hybrid search"* in [chapter 12](../../README.md).

## Counting words rewards the wrong ones

```
   doc 0: 'the cat sat on the mat'
   counts: {'the': 2, 'cat': 1, 'sat': 1, 'on': 1, 'mat': 1}   -> 'the' is the top term. useless.
```

## Rarity across documents is what makes a word informative

```
   the            appears in 3/5 documents
   sat            appears in 3/5 documents
   cat            appears in 2/5 documents
   quantization   appears in 1/5 documents
```

```
   idf(t) = log(N / df(t))     (+1 variants keep it positive)
   the            idf = log(5/3) = 0.511
   sat            idf = log(5/3) = 0.511
   cat            idf = log(5/2) = 0.916
   quantization   idf = log(5/1) = 1.609
   'the' is in every document: idf 0, weight 0. 'quantization' is in one: highest weight.
```

`idf = log(N / df)`. A word in every document scores zero; a word in one document scores highest.
This is the entire insight: **a term's weight is how surprising it is to see it** — the same
log-of-rarity as [chapter 03's surprise](../../../03-training-objective/essentials/logarithms-and-bits/).

## TF-IDF: count here × rarity everywhere

```
   doc 0: 'the cat sat on the mat'
          top weights: mat 1.61, the 1.02, cat 0.92
   doc 2: 'quantization stores weights in fewer bits'
          top weights: quantization 1.61, stores 1.61, fewer 1.61
   a document becomes a vector over the vocabulary; cosine similarity between those
   vectors is the classical 'embedding' -- chapter 02's geometry with counts instead of learning.
```

Each document becomes a vector over the vocabulary. Cosine similarity between those vectors is
the classical "embedding" — [chapter 02's geometry](../../../02-transformer-forward-pass/essentials/vectors-and-dot-products/)
built from counts instead of learned.

## BM25: two fixes to raw counts

```
   1. saturation: the 10th occurrence of a word matters less than the 1st.
     count  raw tf  BM25 tf (dl=avg)
         1       1              1.00
         2       2              1.43
         5       5              1.92
        10      10              2.17
        50      50              2.43
   2. length normalisation: a match in a short document counts more than in a long one.
      doc length   3.4 words (avg 6.8):  tf=2 -> 1.70
      doc length   6.8 words (avg 6.8):  tf=2 -> 1.43
      doc length  20.4 words (avg 6.8):  tf=2 -> 0.87
   BM25 = sum over query terms of idf(t) x saturated, length-normalised tf. it has been
   the keyword-search baseline since the 1990s and still beats embeddings on exact terms.
```

**Saturation** — the tenth occurrence of a word says little more than the first. **Length
normalisation** — a match in a short document is stronger evidence than the same match buried in
a long one. BM25 has been the keyword-search baseline since the 1990s and still beats learned
embeddings on exact terms, identifiers and rare names, which is why production retrieval runs it
alongside them.

## Run it

```bash
python3 demo.py
```

## Terms

| Term | Meaning |
| --- | --- |
| **term frequency (tf)** | How often a word appears in *this* document. |
| **document frequency (df)** | How many documents contain the word. |
| **inverse document frequency (idf)** | `log(N/df)`. Rare across the corpus = informative. |
| **TF-IDF** | `tf × idf`. Count here times rarity everywhere. A document as a weighted word vector. |
| **BM25** | TF-IDF with saturating tf and length normalisation. The keyword baseline. |
| **bag of words** | Treating a document as its word counts, ignoring order. |
| **hybrid retrieval** | Keyword (BM25) and embedding retrieval combined, then reranked. |
