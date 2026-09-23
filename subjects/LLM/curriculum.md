# LLM curriculum — 15 chapters, top-down

A drill list for a programmer who is not a data scientist. Every chapter is a **technology that
exists in code** — a stage in building or running a language model — so the reason to drill into
it is always its position in the pipeline. Inside each chapter, drill down until you can
comfortably explain the leaf without going further; stop there.

`twelve-ideas-behind-modern-ai.md` is the *narrative* — read it once for orientation. These
chapters are what you actually work through. Each chapter README points back to the guide
sections it absorbs.

## The chapters

| # | Chapter | Stage | Absorbs from the twelve ideas |
| --- | --- | --- | --- |
| [01](01-tokenizer/) | Tokenizer | Build | §3 → Tokenization, BPE |
| [02](02-transformer-forward-pass/) | The Transformer forward pass | Build | §4 (all), §2 (the embedding table), §1 (why depth) |
| [03](03-training-objective/) | The training objective | Pretrain | §3 (main), §3 → Softmax & cross-entropy |
| [04](04-optimization-loop/) | The optimization loop | Pretrain | §1 → Backprop, Gradient descent; §8 → Mixed precision |
| [05](05-data/) | Data | Pretrain | §5 (Chinchilla's data lesson), §11 (contamination) |
| [06](06-planning-a-run/) | Planning a run | Pretrain | §5 (all: power laws, Chinchilla, 6ND) |
| [07](07-supervised-fine-tuning/) | Supervised fine-tuning | Post-train | §7 (the SFT half) |
| [08](08-preference-optimization/) | Preference optimization | Post-train | §7 → RL, PPO, reward models, DPO, AI feedback |
| [09](09-reasoning-training/) | Reasoning training | Post-train | §9 (all) |
| [10](10-inference-and-decoding/) | Inference and decoding | Run | §6 (prompting, ICL as the exploited phenomenon), §9 → test-time scaling |
| [11](11-efficiency/) | Efficiency | Run | §8 (all) |
| [12](12-context-and-knowledge/) | Context and knowledge | Run | §11 (all), §2 (embeddings as a product), §4 → RoPE |
| [13](13-multimodality/) | Multimodality | Run | §10 (all) |
| [14](14-tools-and-agents/) | Tools and agents | Run | §12 (all) |
| [15](15-evaluation/) | Evaluation | Measure | *(not in the guide)* |

## Shared prerequisites — the `essentials/` map

Every chapter carries an `essentials/` folder: the maths or theory it leans on that would stop a
capable high-school graduate, one article plus one runnable `demo.py` per concept. **Whichever
chapter first needs a concept owns its article; later chapters link there rather than
re-explaining.** The complete ownership map:

| Chapter | Owns these essentials |
| --- | --- |
| 01 | UTF-8 & bytes · compression & information (Huffman → BPE → bits per token) |
| 02 | vectors & dot products · matrices as functions · softmax & probability · averages & normalization · high-dimensional space · rotation & RoPE · why a network needs a bend |
| 03 | logarithms & bits · the probability of a sequence · entropy, cross-entropy & KL |
| 04 | derivatives & gradients · the chain rule · floating-point numbers · moving averages (Adam) |
| 05 | hashing, Jaccard & MinHash · Zipf's law |
| 06 | power laws & log-log plots · FLOPs & the units of compute |
| 07 | low-rank matrices (LoRA) · overfitting & generalization |
| 08 | expectation, sampling & baselines · the policy gradient · sigmoid & pairwise preference (Bradley–Terry) |
| 09 | compounding probabilities (binomial, pass@k) · z-scores & group normalisation |
| 10 | sampling from a distribution · geometric series & expected tries |
| 11 | the roofline & arithmetic intensity · quantization arithmetic |
| 12 | TF-IDF & BM25 · nearest-neighbour search |
| 13 | the contrastive loss (InfoNCE) · Gaussian noise & denoising |
| 14 | state machines & grammars |
| 15 | standard error & confidence intervals · multiple comparisons & the winner's curse |

38 essentials in all. Each chapter's `README.md` has a "Before the drill list: the maths" table
mapping *the sentence that stopped making sense* to the article that unblocks it.

## Suggested order

Folders are numbered by pipeline position; the reading order is slightly different so the
"why" of each chapter is already visible when you open it:

**02 → 03 → 04** (the machine, what it's trained to do, how it's trained — the core, take your time)
→ **01** (now the tokenizer's constraints make sense) → **10** (run a model and understand every knob)
→ **05 → 06** (what it was trained on and how the run was sized)
→ **07 → 08 → 09** (how a base model becomes an assistant, then a reasoner)
→ **15** (how any of the above is judged)
→ **11 → 12 → 13 → 14** (extensions; read, drill only what your work touches).

## Pairing with code

Chapters 02–04 and 10 map almost one-to-one onto Karpathy's *Neural Networks: Zero to Hero*
(micrograd → makemore → nanoGPT). Build alongside; the READMEs say which lecture matches.

## What is in every chapter

```text
NN-topic/
  README.md            why · one-picture mermaid · what it computes (signature + real example)
                       · terminology · files · drill list · shared prerequisites · build it
                       · done-when checklist · Q&A · notes
  <topic>.md           the main article — generated from a live run, so its numbers cannot drift
  <topic>.py           the generator
  <primary>.py         the runnable model/experiment the chapter is built on
  essentials/          one folder per prerequisite concept: README.md + demo.py
```

Every number in every article and README was produced by running the chapter's code. The scripts
are `python3 script.py`, standard library for 01–03 and numpy from 04 onward, deterministic.
`python3 ../../.claude/skills/drill-down-essentials/scripts/verify_essentials.py <chapter>`
checks structure, runs every demo, resolves every link and validates every mermaid block.

## Conventions

**`CLAUDE.md` in this folder is the working agreement** — how chapters are written (plain
language, examples before terminology, every number executed rather than asserted, generated
articles for anything table-heavy) and the Q&A protocol. Read it before writing chapter content.

- Each chapter folder has a `README.md` — scope, drill list, cross-refs, a done-when checklist,
  and a Notes section for your own writing.
- Add sub-notes as files in the chapter folder (`attention.md`, `rope.md`, …) when a leaf
  deserves more than a paragraph.
- Illustration comes later; nothing here is shaped for the workflow yet, on purpose.
