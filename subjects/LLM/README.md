# LLM / AI — subject folder

Starting material for diving into AI technology and the mathematics underneath it.

| File | What it is |
| --- | --- |
| `curriculum.md` | **Start here.** The 15-chapter drill plan: chapter table, shared-prerequisite ownership, suggested order. |
| `01-tokenizer/` … `15-evaluation/` | **All fifteen chapters are built.** Each has a README (drill list, terminology, one-picture diagram, done-when checklist, Q&A), a main article generated from a live run of the chapter's own code, the runnable scripts, and an `essentials/` folder of prerequisite articles with demos — forty essentials in total. |
| `CLAUDE.md` | The working agreement for this curriculum: plain language, every number executed, generated articles, essentials for anything a high-school graduate would stumble on. |
| `twelve-ideas-behind-modern-ai.md` | The narrative field guide (markdown). Read once for orientation; chapters point back into it by section. |
| `twelve-ideas-behind-modern-ai.html` | The same guide as the original Claude artifact, verbatim and self-contained (inline SVGs, light/dark, sticky TOC). |
| `figures/` | The guide's 12 figures as standalone SVGs — embedded `@media (prefers-color-scheme:dark)`, same convention as `.claude/skills/concept-illustrator/assets/template.svg`. |

Source artifact: `2204c00f-c7fc-426c-ac2a-c084942bdddd` (private, owned by this account).

## Shape of the content

Twelve concepts, in the order they became load-bearing: representation learning · embeddings ·
next-token prediction · attention & the Transformer · scaling laws · in-context learning ·
pretrain-then-align · hardware co-design · reasoning & test-time compute · multimodality ·
long context & retrieval · tool use & agency.

Each has a one-liner, prose, a figure, a worked example, then its prerequisites at two depths:

- `### ↳ Depends on: …` — first level
- `#### ↳↳ Which depends on: …` — second level

That nesting is already a concept dependency graph, which is exactly the input shape
`concept-decompose` / the `dummies-notes` workflow wants — the drill-down headings map onto
`prerequisites`, and the one-liners make good `definition` strings.

## Approach

Top-down. Every chapter is a technology that exists in code — a stage of building or running a
model — so the reason to drill into it is its position in the pipeline. Drill each chapter's
leaves until you can explain them comfortably; stop there. The mathematics (linear algebra,
gradients, probability, RL, power laws, statistics) is not a separate tier: each piece is owned
by the first chapter that needs it and referenced from the rest — see the shared-prerequisites
table in `curriculum.md`.

Illustration with the `dummies-notes` workflow comes *after* the learning, not alongside it.

## Reading order

`curriculum.md` suggests **02 → 03 → 04** first (the machine, its loss, its loop), then 01 and 10,
then 05–09, then 15, then 11–14. Chapters 01 and 02 have accumulated Q&A from being read; the rest
have empty Q&A sections waiting for questions — which is where the value has come from so far.

Note: a couple of markdown viewers refuse to render linked SVGs. If figures look blank, open the
HTML copy instead — the pictures there are inline.
