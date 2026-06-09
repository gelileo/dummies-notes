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

Populated as modules land. Each article's `affects:` globs drive `drift-check`; keep this table in sync.

| When you change... | Update this article |
| --- | --- |
| The concept dependency-graph / decomposition logic | `concepts/dummies-notes/concept-decomposition.md` |
| Figure generation, SVG output, archetype routing | `concepts/dummies-notes/illustration-engine.md` |
| Storage/lookup/addressing of reusable atomic figures | `concepts/dummies-notes/atomic-illustration-catalog.md` |

### When code has no matching article

Write the first thin article in the same task. Place internal concepts at `concepts/dummies-notes/{topic}.md`, cross-cutting articles at `connections/{topic}.md`. Capture the **why** (constraints, alternatives ruled out), not just the post-change state. Add a row to the table above and a note in `log.md`.

### Catch drift

After implementing, ask: "does anything in `knowledge/` now contradict what I built?" Check signatures, field lists, config, folder structure. **Real data beats the article.** Append a compile entry to `knowledge/log.md`.

## Current state

Greenfield. No source code, git repo, or build tooling exists yet — **do not invent build/lint/test commands**. The living-doc tooling is in place and works:

```bash
python3 scripts/validate-articles    # validate frontmatter of all knowledge articles
python3 scripts/drift-check --help    # code↔article drift check (needs a git repo with a base ref)
```

The pre-commit hook and GitHub Action from living-doc are **not yet installed** — they require `git init` first (this is not a git repo). Add them (`.pre-commit-config.yaml` / `.github/workflows/`) once the repo is initialized.

`example/` is reference-only: `concept-illustrator-SKILL.md` is the **design reference** for the illustration engine, with a finished sample figure (`example-binary-search.svg` + light/dark PNGs). Note its referenced helper files (`scripts/render.py`, `assets/template.svg`, …) are *not* present — only the SKILL.md and outputs were copied in.

### Illustration conventions (target spec, from `example/`)

- **Archetype routing on the verb, not the noun**: flowchart (steps), structural (containment), illustrative (intuition — the default & most valuable; invent a spatial metaphor), chart (quantities). One archetype per figure.
- **Self-contained SVG**: embedded `<style>` + arrow marker, renders standalone, light+dark via `@media (prefers-color-scheme:dark)`.
- **Restrained system**: `viewBox="0 0 680 H"`; two type sizes (`th`/`t` 14px, `ts` 12px); sentence case; 0.5 strokes; color encodes *category* via named ramps; no gradients/shadows/emoji.
- One-archetype-per-file maps directly to the project's "atomic, reusable illustration" unit.
