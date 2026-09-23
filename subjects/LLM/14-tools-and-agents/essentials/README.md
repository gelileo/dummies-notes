# Essentials — the idea chapter 14 assumes

Chapter 14 is programming — loops, JSON, APIs — and a programmer has it. One idea is worth a page
because it is what makes tool calls *safe to parse*:

| Article | Read it when you hit… |
| --- | --- |
| [State machines and grammars](./state-machines-and-grammars/) | "constrained decoding", "the call must parse", "JSON mode", "grammar mask" |

Compounding error over steps is owned by
[chapter 09](../../09-reasoning-training/essentials/compounding-probabilities/); the policy
gradient used to train agents by [chapter 08](../../08-preference-optimization/essentials/the-policy-gradient/).

## How this folder is laid out

```text
essentials/
  README.md                       this index
  state-machines-and-grammars/
    README.md                     the article
    demo.py                       prints the strings the article quotes
```

```bash
cd state-machines-and-grammars && python3 demo.py
```

Standard library; deterministic.
