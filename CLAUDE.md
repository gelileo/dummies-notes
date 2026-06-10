# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project vision

`dummies_notes` is an AI-assisted learning tool. The goal: given a topic, concept, theorem, workflow, or obscure idea, produce **intuitive illustrations + captions** that make it understandable — rather than explaining everything in prose.

The core strategy is **recursive divide-and-conquer over a reasoning toolchain**:

- Given a target concept, recursively/iteratively discover its *dependency concepts* — the prerequisites on the reasoning chain needed to understand it.
- Keep decomposing until reaching **atomic concepts/workflows**: small enough that a single illustration explains them clearly.
- Each atomic illustration is **reusable and portable** — a standalone unit that can be composed into the reasoning chains of *other*, larger concepts.

Two layers: (1) a **decomposition engine** that builds the concept dependency graph down to atomic level, and (2) an **illustration engine** that renders each node as a clean, self-contained figure. Reusability implies atomic illustrations are cataloged/content-addressed, so a concept appearing in many chains is drawn once and referenced everywhere.

## Living documentation methodology

This project follows the living-documentation methodology at https://github.com/mpklu/living-doc. The first principle (**capture first, refine second**) and the **same-task rule** apply here.

The knowledge base in `knowledge/` is the source of truth and must always mirror the code. Entry point: `knowledge/index.md`. Compile log: `knowledge/log.md`. The frontmatter schema is `schemas/article-frontmatter.schema.json`.

### The rule

Every code change that alters behaviour, config, models, or architecture **must update the relevant `knowledge/concepts/*.md` article(s) in the same task** and append an entry to `knowledge/log.md`. Don't batch knowledge updates for later — a skipped update goes stale before the next read, and the next session trusts the stale article and produces wrong work.

**Capture first, refine second:** when unsure whether a change is doc-relevant, write the update anyway. When unsure where an article belongs, pick the closest fit and write it. Missing context is unrecoverable; an imperfect article costs minutes.

### Before any commit

1. List the files in this commit's diff.
2. For each: does any article's `affects:` frontmatter glob match it? Open those articles. (Run `python3 scripts/drift-check --warn-only` to see matches.)
3. Did this change alter behaviour, configuration, models, structure, or a documented decision?
4. If yes: stage the article update + a `log.md` entry **in this same commit**.
5. If no article exists for the touched code path: write a thin one now (~200 words).
6. If genuinely doc-irrelevant (typo, formatting, behaviour-identical refactor): the commit body must say so: `no knowledge impact: <reason>`.

### Red flags — these thoughts mean STOP and audit

"I'll update docs after this lands." · "The article is roughly correct." · "Too small to document." · "Ship and circle back." · "The reviewer can flag it."

### What lives where

| Location | Contains | Authority |
| --- | --- | --- |
| `knowledge/concepts/` | Standalone reference articles, grouped by area | How each thing works and why |
| `knowledge/connections/` | Cross-concept articles | How the pieces fit together |
| `example/` | Reference material (not installed) — illustration style/quality bar | Design inspiration only |
| `src/` *(when created)* | Implementation | What the system does |
| `tests/` *(when created)* | Tests | Testable behaviour |

### Article mapping — update these when the matching code changes

Each article's `affects:` globs drive `drift-check`; keep this table in sync.

| When you change... | Update this article |
| --- | --- |
| `.claude/skills/concept-decompose/**` | `concepts/dummies-notes/concept-decomposition.md` |
| `.claude/skills/concept-illustrator/**` | `concepts/dummies-notes/illustration-engine.md` |
| `src/catalog/**`, `registry/**` | `concepts/dummies-notes/atomic-illustration-catalog.md` |

### When code has no matching article

Write the first thin article in the same task. Place internal concepts at `concepts/dummies-notes/{topic}.md`, cross-cutting articles at `connections/{topic}.md`. Capture the **why** (constraints, alternatives ruled out), not just the post-change state. Add a row to the table above and a note in `log.md`.

### Catch drift

After implementing, ask: "does anything in `knowledge/` now contradict what I built?" Check signatures, field lists, config, folder structure. **Real data beats the article.** Append a compile entry to `knowledge/log.md`.

## Current state

This is a git repo on `main`. The living-doc pre-commit hook and GitHub Action are installed and active.

**Phase 1 shipped**: the `concept-illustrator` skill lives at `.claude/skills/concept-illustrator/`:
- `SKILL.md` — the skill contract
- `assets/` — `template.svg`, `_style.css`, `slideshow.template.html`
- `references/` — design-system, archetypes, visual-vocabulary, voice-and-metaphor, review-protocol, figure-json
- `scripts/render.py` — SVG lint + figure-dir validation + slideshow viewer builder + optional PNG export
- `examples/quicksort/` — the golden reference figure (4-frame slideshow)
- `scripts/tests/` — unit tests

Real commands:

```bash
# run the illustrator's test suite
python3 -m unittest discover -s .claude/skills/concept-illustrator/scripts/tests -p 'test_*.py'

# lint one SVG / validate a figure dir / build its viewer
python3 .claude/skills/concept-illustrator/scripts/render.py <file.svg|figure-dir> [--viewer out.html]

# validate knowledge frontmatter / drift
python3 scripts/validate-articles
python3 scripts/drift-check --warn-only
```

**Phases 2–4** (concept-decompose, concept-registry, the dummies-notes Workflow, assembly + map viewer) are **not yet built**. See `docs/superpowers/specs/2026-06-09-dummies-notes-design.md` and `docs/superpowers/plans/`.

`example/` is the original design reference: `concept-illustrator-SKILL.md` plus a finished sample figure (`example-binary-search.svg` + light/dark PNGs). The shipped implementation supersedes it — treat `example/` as historical reference only.

### Illustration conventions

These conventions are the **shipped implementation** in `.claude/skills/concept-illustrator/references/` (design-system.md, archetypes.md, visual-vocabulary.md, voice-and-metaphor.md). The golden example figure at `examples/quicksort/` demonstrates them in practice.

- **Archetype routing on the verb, not the noun**: flowchart (steps), structural (containment), illustrative (intuition — the default & most valuable; invent a spatial metaphor), chart (quantities). One archetype per figure.
- **Self-contained SVG**: embedded `<style>` + arrow marker, renders standalone, light+dark via `@media (prefers-color-scheme:dark)`.
- **Restrained system**: `viewBox="0 0 680 H"`; two type sizes (`th`/`t` 14px, `ts` 12px); sentence case; 0.5 strokes; color encodes *category* via named ramps; no gradients/shadows/emoji.
- One-archetype-per-file maps directly to the project's "atomic, reusable illustration" unit.
