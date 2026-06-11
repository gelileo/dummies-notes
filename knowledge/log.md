# Build Log

Append-only chronological log of significant changes to this project. Each entry records what changed, why, and which articles were touched. Read sequentially, this log tells the story of the project's decisions.

## [2026-06-10] compile | Phase 5 shipped — self-sufficient figures, composition retired

Phase 5 introduced the two-axis decomposition contract and retired the compose-from-children approach. This entry records what landed and the final state of the system.

**Two-axis contract** — `decomposition.json` now carries `mechanism_figurable` (can this concept's mechanism be taught in one standalone figure?) separately from `atomic` (stop decomposing?). The two booleans are independent: a non-atomic concept with prerequisites can still be figurable and will get its own self-sufficient mechanism figure. Validator enforces `mechanism_figurable` as a required boolean. Golden examples (`rsa-encryption`, `modular-arithmetic`) updated.

**Illustrator self-sufficiency rule** — every figure teaches its own concept standalone; a reader who has not seen prerequisite figures still grasps the mechanism. When prerequisites have their own figures, commentary adds short "go deeper" pointers (references, not re-teaching). Phase-4 compose-from-children mode **retired**: it mapped structural parts without teaching the target's own mechanism.

**Workflow illustrates every figurable node** — the `toIllustrate` filter changed from `atomic === true` to `mechanism_figurable === true`. Non-atomic-but-figurable nodes receive their own mechanism figure in the Illustrate pass. No separate compose step. `graph_check --require-illustrated` and `assemble.py` "Figure pending" both key off `mechanism_figurable`.

**TCP acceptance run** — tcp-connection-lifecycle re-run at `maxDepth: 2`; 5 nodes: root + unreliable-delivery + delivery-acknowledgement illustrated self-sufficiently (the last two are non-atomic-but-figurable); communication-protocol + data-packets reused from registry; computer-network logged as honest frontier. Chain review **passed** (`chain_review_pass: true`) — 4 blocking gaps collapsed to 1 minor frontier note. 60 tests green.

**Articles touched**: `concepts/dummies-notes/concept-decomposition.md`, `concepts/dummies-notes/illustration-engine.md`, `concepts/dummies-notes/orchestration-workflow.md`, `knowledge/index.md`, `CLAUDE.md`.

## [2026-06-10] feat(assemble): pending notice keys off mechanism_figurable; graph_check docstring (Phase 5 Task 6)

- `scripts/tests/test_assemble.py write_decomp`: updated helper signature to `write_decomp(graph_dir, slug, atomic, prereqs=(), figurable=None)` and added `"mechanism_figurable": atomic if figurable is None else figurable` to the data dict. Added `test_nonatomic_figurable_without_figure_shows_pending` to `TestDegradation` — a non-atomic + figurable=True node with no figure must show "Figure pending".
- `scripts/assemble.py load_full_graph`: added `"mechanism_figurable": bool(data.get("mechanism_figurable", data.get("atomic")))` to the node dict, mirroring the graph_check pattern. Pre-Phase-5 files without the field default to `atomic`.
- `scripts/assemble.py build_explainer`: changed the "Figure pending" branch condition from `node["atomic"]` to `node["mechanism_figurable"]`, so figurable non-atomic nodes also show the notice when their figure is absent.
- `scripts/graph_check.py` module docstring: updated "every atomic node has an attached figure" to "every figurable node has an attached figure" (one-phrase fix; no structural change).
- `knowledge/concepts/dummies-notes/orchestration-workflow.md`: updated step 6 Assemble description — figure embedding is no longer atomic-only; "Figure pending" now keyed to `mechanism_figurable`; non-figurable nodes are caption-only.
- Test suite: 60 tests, all passing.
- Articles touched: `concepts/dummies-notes/orchestration-workflow.md`.

## [2026-06-10] feat(workflow): illustrate figurable nodes; self-sufficiency prompt; delete compose (Phase 5 Task 5)

- `.claude/workflows/dummies-notes.js`: (1) `DECOMP_SCHEMA` gains `mechanism_figurable: { type: 'boolean' }` in properties and `'mechanism_figurable'` in required. (2) `nodes[slug]` object gains `mechanism_figurable: d.mechanism_figurable`. (3) `toIllustrate` filter flipped from `n.atomic === true` to `n.mechanism_figurable === true`; map gains `prereqs: (n.prereqMeta || []).map(p => p.name)`. Log line updated to "figurable concept(s)". (4) `illustrate()` prompt gains a self-sufficiency instruction when `c.prereqs.length > 0`: names the prerequisites, directs the agent to make the figure SELF-SUFFICIENT, and instructs "go deeper" commentary pointers. (5) Compose-from-children block deleted (~17 lines from `const rootNode = nodes[rootSlug]` through its closing `}`). (6) `meta.phases` Assemble detail updated; `meta.description` and Illustrate detail updated. Stale "compose-from-children" comment in the prereqMeta line updated.
- `knowledge/concepts/dummies-notes/orchestration-workflow.md`: Run shape step 3 updated — Illustrate now covers every figurable node (atomic or non-atomic), describes self-sufficiency rule and "go deeper" commentary pattern, and notes a figurable root gets its mechanism figure in the Illustrate pass. Step 6 Assemble updated — compose-from-children agent removed (compose retired); `scripts/assemble.py` runs directly. Stale "compose step" paragraph removed.
- `python3 scripts/validate-articles` passes.
- Articles touched: `concepts/dummies-notes/orchestration-workflow.md`.

## [2026-06-10] feat(graph_check): require figures for figurable nodes, not just atomic (Phase 5 Task 4)

- `scripts/tests/test_graph_check.py write_decomp`: updated helper to include `mechanism_figurable` field (defaults to `atomic` unless `figurable=` kwarg overrides). Added `TestFigurableCoverage` class with 2 tests: `test_nonatomic_figurable_unillustrated_errors` (non-atomic + figurable=True without a figure → ERROR containing "not illustrated" for that slug) and `test_nonatomic_nonfigurable_is_exempt` (non-atomic + figurable=False → no error for that slug). Confirmed failure before graph_check.py changes.
- `scripts/graph_check.py load_graph`: added `mechanism_figurable` to the node dict — `bool(data.get("mechanism_figurable", data["atomic"]))` so pre-Phase-5 files without the field default to `atomic`.
- `scripts/graph_check.py check_coverage`: changed illustration guard from `node["atomic"]` to `node["mechanism_figurable"]`; error message changed from "atomic but not illustrated" to "figurable but not illustrated" (still contains "not illustrated", so existing tests still pass).
- `scripts/graph_check.py main`: updated `--require-illustrated` help text to "figurable nodes must have an attached figure".
- `knowledge/concepts/dummies-notes/orchestration-workflow.md`: updated `## graph_check` section — `--require-illustrated` now requires a figure for every figurable (`mechanism_figurable: true`) node, not just atomic; non-figurable nodes are exempt; pre-Phase-5 files without the field default to `atomic`; unit test count updated to 14.
- Test suite: 59 tests, all passing.
- Articles touched: `concepts/dummies-notes/orchestration-workflow.md`.

## [2026-06-10] feat(illustrator): self-sufficiency rule + commentary go-deeper refs; retire compose (Phase 5 Task 3)

- `scripts/tests/test_render.py TestSkillRefs`: replaced `test_skill_md_documents_composition_mode` (checked "Composition figures"/"compose-from-children" tokens) with `test_skill_md_documents_self_sufficiency` (checks "Self-sufficient"/"go deeper" present, "compose-from-children" absent). Confirmed failure before SKILL.md edit.
- `.claude/skills/concept-illustrator/SKILL.md`: deleted `## Composition figures (compose-from-children)` section (~14 lines); added `## Self-sufficient figures` section (after output-contract) describing the standalone-teaching rule and the "go deeper" commentary pointer pattern.
- `knowledge/concepts/dummies-notes/illustration-engine.md`: replaced `## Compose-from-children mode` paragraph with `## Self-sufficient figures (Phase 5)` — figures are self-sufficient (teach standalone); commentary carries optional "go deeper" references; Phase-4 compose-from-children mode retired. Updated suite count to 58 tests, 1 skip.
- Test suite: 58 tests, 1 skip; `check_skill_refs.py` exits 0; `python3 scripts/validate-articles` passes.
- Articles touched: `concepts/dummies-notes/illustration-engine.md`.

## [2026-06-10] docs(decompose): SKILL.md two-axis guidance (stop vs draw) (Phase 5 Task 2)

- `tests/test_validate_decomposition.py TestSkillContract.test_skill_md_covers_the_contract`: added `"mechanism_figurable"` to the contract-token list; confirmed failure before SKILL.md update.
- `.claude/skills/concept-decompose/SKILL.md`: added `## Two axes: stop vs draw` section after the atomicity test step — explains `atomic` (stop decomposing) and `mechanism_figurable` (draw it) as independent judgments; gives the non-atomic+figurable pattern (`atomic: false, mechanism_figurable: true`); advises preferring figurable when uncertain.
- `knowledge/concepts/dummies-notes/concept-decomposition.md`: added `### Two-axis rule: stop vs draw` subsection under the schema section, describing the independence of both axes, when each is true, and the guidance to prefer figurable when uncertain.
- Test suite: 18 tests, all passing; `check_skill_refs.py` exits 0.
- Articles touched: `concepts/dummies-notes/concept-decomposition.md`.

## [2026-06-10] feat | decompose: add mechanism_figurable axis to the contract (Phase 5 Task 1)

- `validate_decomposition.py`: added check — `mechanism_figurable` must be a JSON bool (ERROR if missing or wrong type).
- `tests/test_validate_decomposition.py`: added `mechanism_figurable: True` to `good()` helper; added 4 new tests (missing field, wrong type, non-atomic+figurable clean, non-atomic+non-figurable clean). Suite: 18 tests, all passing.
- `references/decomposition-json.md`: added `mechanism_figurable` row to top-level fields table; added "Two axes: atomic vs mechanism_figurable" section explaining the independence of the two booleans.
- `examples/modular-arithmetic/decomposition.json`, `examples/rsa-encryption/decomposition.json`: added `"mechanism_figurable": true` to both golden examples.
- `knowledge/concepts/dummies-notes/concept-decomposition.md`: updated schema table and added explanatory sentence on the two-axis contract.

## [2026-06-10] compile | Phase 4 shipped — the dummies-notes system is complete

All four phases of the original spec are now built. This entry records what landed across Phase 4 and the final state of the system.

**Assembler (`scripts/assemble.py`)** — deterministic deliverable builder: `load_full_graph` / `find_root` / `topo_order` (Kahn's BFS, alphabetical tie-breaking); `build_explainer` (bottom-up inline slideshows, covered links, frontier stubs); `build_map` (nodes layered by depth, first-frame thumbnails, prerequisite edges, click-through to explainer); CLI (`graph_dir`, `--registry`, `--out`). 18 tests added (suite total 57), all passing.

**Compose-from-children mode** — added to `.claude/skills/concept-illustrator/SKILL.md`: single-frame structural composition figure for a non-atomic parent whose children are already illustrated; used by the Assemble phase to author the root figure.

**Assemble + ChainReview phases** — wired into `.claude/workflows/dummies-notes.js` as the final two phases of the full pipeline. Assemble: compose-from-children agent for non-atomic roots + `scripts/assemble.py` runner. ChainReview: fresh agent writes `output/<root>/chain-review.json`; gaps reported, no auto-repair (honest disclosure, not silent patching). Return object gains `index_html`, `map_html`, `chain_review_pass`, `chain_gaps`.

**Both deliverables produced**:
- `output/modular-arithmetic/` — atomic, chain review passed clean.
- `output/rsa-encryption/` — full run (4 nodes, maxDepth 1): covered-stop on modular-arithmetic, prime-numbers + asymmetric-cryptography illustrated, composition figure for root. Chain review **failed honestly** — 4 documented graph-level gaps shipped in `chain-review.json`. Capstone check working as designed: composition figures map structure but don't teach the target's own mechanism; deeper runs are needed for security-core nodes.

**Articles touched**: `concepts/dummies-notes/orchestration-workflow.md`, `concepts/dummies-notes/illustration-engine.md`, `knowledge/index.md`, `CLAUDE.md`.

## [2026-06-10] feat | workflow: Assemble + ChainReview phases — the full pipeline (Phase 4 Task 5)

- `.claude/workflows/dummies-notes.js`: added two new phases. `meta.phases` gains `{ title: 'Assemble', ... }` and `{ title: 'ChainReview', ... }` after Finalize; `meta.whenToUse` updated to drop "assembly is Phase 4" (now built), noting the run produces `output/<topic>/index.html` + `map.html`. Replaced the final `return` block with the full Assemble phase (compose-from-children agent for non-atomic roots + `scripts/assemble.py` runner) and ChainReview phase (fresh-eyes agent writes `output/<root>/chain-review.json`; gaps logged as a report, no auto-repair). Return object gains `index_html`, `map_html`, `chain_review_pass`, `chain_gaps`.
- `knowledge/concepts/dummies-notes/orchestration-workflow.md`: "Run shape (Phase 3)" heading updated to "Run shape"; steps 6–7 added (Assemble and ChainReview); "Phase 4 next" section replaced with a lean "Open question" section (figure invalidation/versioning — the one remaining deferred item).
- Articles touched: `concepts/dummies-notes/orchestration-workflow.md`.

## [2026-06-10] feat | illustrator: compose-from-children mode for composition figures (Phase 4 Task 4)

- `.claude/skills/concept-illustrator/SKILL.md`: added `## Composition figures (compose-from-children)` section (after the output-contract section) — specifies the single-frame structural composition figure for a non-atomic parent whose children are already illustrated; used by the assembly phase to author the target's root figure.
- `scripts/tests/test_render.py`: added `test_skill_md_documents_composition_mode` to `TestSkillRefs` — asserts both "Composition figures" and "compose-from-children" tokens are present in SKILL.md. Suite total: 58 tests, 1 skip.
- `knowledge/concepts/dummies-notes/illustration-engine.md`: added compose-from-children mode section.
- Articles touched: `concepts/dummies-notes/illustration-engine.md`.

## [2026-06-10] fix | assemble.py: empty-graph diagnostic + negative-path tests (review follow-ups)

- `scripts/assemble.py load_full_graph`: after the `for fname` loop, if `nodes` and `issues` are both empty, appends `("ERROR", "no decomposition files found in <graph_dir>")`. This prevents a silent crash inside `find_root` when the graph directory exists but holds no `.json` files; `main` prints the ERROR and exits 1.
- `scripts/tests/test_assemble.py`: appended `TestDegradation` (4 tests): atomic node with a broken figure shows "Figure pending"; covered entry with a missing figure dir degrades to "figure pending"; adversarial `<script>` tags in name/definition are HTML-escaped (no raw `<script>` in output); empty graph dir causes `main` to return 1. Suite total: 57 tests, all passing.
- Articles touched: `concepts/dummies-notes/orchestration-workflow.md`.

## [2026-06-10] feat | assemble.py concept map + CLI (Phase 4 Task 3)

- `scripts/assemble.py`: replaced the `build_map` stub with the real implementation. `MAP_CSS`, `_NODE_W/_NODE_H/_COL_W/_ROW_H` constants; `_depths` (BFS from root, assigns depth 0 to root and depth+1 to each prerequisite); `_thumb` (loads first frame SVG for illustrated nodes); `build_map` (layers nodes by depth, positions them on a canvas, draws `<line>` edges for each prerequisite, embeds thumbnail for illustrated nodes, links every node to `index.html#<slug>`). Added `main(argv=None)` CLI (`graph_dir`, `--registry`, `--out`) and `if __name__ == "__main__": sys.exit(main())` guard.
- `scripts/tests/test_assemble.py`: appended `TestMap` (3 tests — data-node per concept + edge count, links to explainer, illustrated thumbnails) and `TestCli` (2 tests — exit 0 with both files, exit 1 on missing graph). Suite total: 53 tests.
- `knowledge/concepts/dummies-notes/orchestration-workflow.md`: added map semantics sentence (nodes layered by depth from the root, illustrated nodes carry first-frame thumbnails, click-through to the explainer sections).
- Articles touched: `concepts/dummies-notes/orchestration-workflow.md`.

## [2026-06-10] feat | assemble.py explainer: bottom-up inline slideshows, covered links, frontier stubs (Phase 4 Task 2)

- `scripts/assemble.py`: added `PAGE_CSS`, `SLIDESHOW_JS`, `load_figure`, `figure_html`, `_children_list`, `_figure_dir_for`, `_ensure_viewer`, `build_explainer`, `classify_prereqs`, `assemble`, and a temporary `build_map` stub. Writes `output/<topic>/index.html` bottom-up: atomic nodes embed inline SVG slideshows; already-covered prereqs are linked to their registry viewer; intermediate nodes render caption-only with child links; frontier prereqs get a stub note.
- `scripts/tests/test_assemble.py`: added `TINY_SVG`, `make_figure`, `make_world` helpers and `TestExplainer` (5 tests — sections order, inline frames, covered linked, caption-only root, frontier stub). Suite total: 48 tests.
- `knowledge/concepts/dummies-notes/orchestration-workflow.md`: added explainer semantics sentence (bottom-up slideshows, covered linked, intermediate caption-only, frontier stubs).
- Articles touched: `concepts/dummies-notes/orchestration-workflow.md`.

## [2026-06-10] feat | assemble.py core: graph loading, root detection, bottom-up topological order (Phase 4 Task 1)

- Created `scripts/assemble.py`: deterministic assembler skeleton. Implements `load_full_graph` (reads `*.json` graph files from a directory into `{slug: {name, definition, atomic, prerequisites}}` nodes), `find_root` (the one node unreferenced by others), `topo_order` (Kahn's-style BFS with alphabetical tie-breaking — prerequisites before dependents, root last; raises on cycles). Module docstring and all Task 2–3 imports (`argparse`, `html`, `render`, `DEFAULT_ROOT`, `lookup`) present.
- Created `scripts/tests/test_assemble.py`: 8 tests across `TestLoadFullGraph`, `TestFindRoot`, `TestTopoOrder` (TDD — written before module, confirmed `No module named 'assemble'` failure, then all 43 passed).
- `knowledge/concepts/dummies-notes/orchestration-workflow.md`: added `scripts/assemble.py` to `affects:`; added body sentence: "Assembly is deterministic: `scripts/assemble.py` renders index.html + map.html from the graph + registry — no agent writes HTML."
- `CLAUDE.md`: added row `scripts/assemble.py` → `orchestration-workflow.md` to the article mapping table.
- Articles touched: `concepts/dummies-notes/orchestration-workflow.md`, `CLAUDE.md`.

## [2026-06-10] compile | Phase 3 knowledge-base reconciliation (Task 5)

Phase 3 shipped three production deliverables. This entry records what landed and the articles matured to reflect it.

**graph_check.py** (`scripts/graph_check.py`)
- Zero-dep stdlib gate for a concept-graph directory; three checks: `load_graph` (shape), `find_cycles` (DFS cross-node cycle detection, diamond-safe), `check_coverage` (every graph node registered; `--require-illustrated` requires atomic nodes to have figures); frontier prerequisites (no graph file, not registered) are WARNs.
- 12 unit tests in `scripts/tests/test_graph_check.py`; suite total 35 tests.

**Orchestrator workflow** (`.claude/workflows/dummies-notes.js`)
- Full BFS orchestration: registry-snapshot agent → BFS decompose with `MAX_DEPTH=2` / `MAX_NODES=12` caps + frontier logging → `pipeline()` illustrate→review per atomic node with `MAX_REPAIRS=2` and flag-and-continue → Finalize agent (python3-heredoc registration with `--prereqs`, attach-figure, index rebuild, `graph_check --require-illustrated`).
- Accepts `args` as object or JSON-encoded string.

**First end-to-end run** (modular arithmetic, 2026-06-10)
- 1 node, atomic; clock-face figure illustrated into `registry/modular-arithmetic/figure/` (5 frames, lint clean); blind-reader + fidelity-critic review passed with no repairs; entry promoted to `illustrated`; `graph_check --require-illustrated` clean. 6 agents total.

**Articles matured**
- `concepts/dummies-notes/orchestration-workflow.md`: `status: thin` → `mature`. Removed stale "in progress" phrasing and Phase 3 Task status sections; accurate graph_check test count (12/35); added Phase 4 next section (assembly + end-to-end chain review + figure invalidation open question).
- `knowledge/index.md`: orchestration-workflow row updated (dropped "in progress"; noted first run).
- `CLAUDE.md § Current state`: Phase 3 marked shipped; graph_check command added; Phase 4 scope updated.
- Articles touched: `concepts/dummies-notes/orchestration-workflow.md`, `knowledge/index.md`, `CLAUDE.md`.

## [2026-06-10] fix | workflow: persist prereqs on re-register; quoting-proof finalize registration

- `scripts/concept_registry.py register()`: idempotent re-registration now updates `prerequisites` when explicitly provided and different from the stored value, persisting graph edges for already-registered concepts without requiring a definition change.
- `scripts/tests/test_concept_registry.py`: added `test_reregister_updates_prerequisites` to `TestRegisterLookup`; suite total: 35 tests, all passing.
- `.claude/workflows/dummies-notes.js` Finalize agent step 1: replaced the shell-CLI approach with a python3 heredoc that calls `concept_registry.reg.register` directly, eliminating shell-quoting hazards.
- Articles touched: `concepts/dummies-notes/atomic-illustration-catalog.md`, `concepts/dummies-notes/orchestration-workflow.md`.

## [2026-06-10] feat | dummies-notes orchestrator workflow script (Phase 3 Task 3)

- Created `.claude/workflows/dummies-notes.js`: the full BFS orchestration script. Exports `meta` with four phases (Decompose/Illustrate/Review/Finalize). One registry-snapshot agent seeds `covered` map; BFS loop calls `concept-decompose` skill per node with depth cap (`maxDepth` default 2) and node cap (`maxNodes` default 12), both logged as frontier on hit. `pipeline()` per atomic node: illustrate → blind reader + fidelity critic review, ≤ `MAX_REPAIRS` (2) repair iterations, flag-and-continue on still-failing. Finalize agent registers all new nodes with `--prereqs`, attaches figures, rebuilds index, runs `graph_check.py --require-illustrated`. Returns root, graph_dir, nodes, illustrated, flagged, frontier, collisions, graph_check_clean.
- `knowledge/concepts/dummies-notes/orchestration-workflow.md`: verified "Run shape (Phase 3)" section accurately describes the shipped script — no wording changes needed.
- Articles touched: `concepts/dummies-notes/orchestration-workflow.md`.

## [2026-06-10] feat | graph_check: shape + cross-node cycles + registry coverage (Phase 3 Task 2)

- Created `scripts/graph_check.py`: zero-dep stdlib gate for a concept-graph directory (`decomposition.json` files as produced by the concept-decompose skill). Three checks: `load_graph` (every file parses with `slug` + `atomic`), `find_cycles` (DFS cycle detection across prerequisite edges within the graph), `check_coverage` (every graph node is registered; with `--require-illustrated` every atomic node must be `illustrated`). Frontier prerequisites — no graph file, not registered — are WARNs (not ERRORs), consistent with depth-capped runs.
- Created `scripts/tests/test_graph_check.py`: 11 tests (TDD — written before the module, confirmed `ModuleNotFoundError`, then all passed). Full suite: 33 tests (22 registry + 11 new), all passing.
- `knowledge/concepts/dummies-notes/orchestration-workflow.md`: verified article accurately describes the shipped semantics (frontier WARN, `--require-illustrated` flag, shape/cycle/coverage checks); no wording changes needed.
- Articles touched: `concepts/dummies-notes/orchestration-workflow.md`.

## [2026-06-10] doc | scope Phase 3 drift mapping + thin orchestration-workflow article

## [2026-06-10] compile | Phase 2 knowledge-base reconciliation (Task 8)

Phase 2 shipped two production subsystems. This entry summarises what landed and records the knowledge-base articles matured to reflect it.

**Decompose skill + validator + golden examples**
- `.claude/skills/concept-decompose/SKILL.md`: single-level contract — canonicalize (slug + plain definition) → atomicity test (≤ ~6-frame figure + common-knowledge prerequisites) → list direct prerequisites with `why` (jargon rule: unexplained terms become prerequisites) → reuse registry slugs → validate to `OK     clean`.
- `references/decomposition-json.md`: full schema for `decomposition.json` (concept/audience/atomic/atomic_reason/prerequisites + why).
- `scripts/validate_decomposition.py`: zero-dependency validator; 14 tests in `scripts/tests/` (includes `TestSkillContract`, `TestGoldenDecompositions`).
- `examples/rsa-encryption/decomposition.json`: non-atomic golden with three load-bearing prerequisites; jargon rule demonstrated throughout.
- `examples/modular-arithmetic/decomposition.json`: atomic golden, clock-metaphor, `prerequisites: []`; slug+definition byte-identical to the RSA prerequisite entry, exercising identity reuse.

**Registry + CLI + seed**
- `scripts/concept_registry.py`: zero-dependency register/lookup/attach-figure/build-index; identity = slug + definition (idempotent same-definition; collision → qualified slug); `_read_json` and `build_index` raise `RegistryError` on corrupt/malformed entries; 22 tests in `scripts/tests/test_concept_registry.py`.
- `scripts/concept-registry`: executable shell wrapper exposing all four verbs.
- `registry/` seeded with `quicksort` (`status: illustrated`, linked to Phase 1 golden figure) and `modular-arithmetic` (`status: registered`, definition matches decompose golden).
- `registry/index.json` rebuildable and byte-identical after rebuild.

**Articles matured**
- `concepts/dummies-notes/concept-decomposition.md`: `status: thin` → `mature`. Full skill description, schema table, atomicity rule, jargon rule, slug+definition identity, validator gate, golden examples, explicit Phase 3 scope for graph walk + cross-node cycle detection.
- `concepts/dummies-notes/atomic-illustration-catalog.md`: `status: thin` → `mature`. Storage layout, entry schema, status lifecycle, slug+definition addressing, portability (relative figure path), CLI verb table, error contract, seeded entries; versioning/invalidation explicitly deferred to Phase 3+ (no longer a stale undecided blocker).
- `knowledge/index.md`: one-liners for both articles updated to 2026-06-10.
- Articles touched: `concepts/dummies-notes/concept-decomposition.md`, `concepts/dummies-notes/atomic-illustration-catalog.md`, `knowledge/index.md`.

## [2026-06-10] feat | concept-decompose: golden decompositions — rsa (non-atomic) + modular-arithmetic (atomic) (Phase 2 Task 6)

- Authored `.claude/skills/concept-decompose/examples/rsa-encryption/decomposition.json`: non-atomic, with three load-bearing prerequisites (`modular-arithmetic`, `prime-numbers`, `asymmetric-cryptography`), each with a plain definition + `why`. Definitions obey the jargon rule — no "coprime"/"totient" or any unexplained term; the two-key idea, wrap-around counting, and primes are kept plain.
- Authored `.claude/skills/concept-decompose/examples/modular-arithmetic/decomposition.json`: atomic, `prerequisites: []`, `atomic_reason` cites the one-figure clock-face test. Its `concept` slug + definition are literally identical to the `modular-arithmetic` prerequisite entry in the rsa example, exercising the slug+definition = identity rule.
- Both validate `OK     clean` (exit 0).
- Added `TestGoldenDecompositions` (3 tests: rsa valid/non-atomic, modular-arithmetic valid/atomic, identity consistent across the two files) to `scripts/tests/test_validate_decomposition.py`; suite total is now 14 tests, all passing; `check_skill_refs.py` exits 0.
- Added a "Files in this skill" pointer in SKILL.md to both example files so the refs checker stays green.
- Updated `knowledge/concepts/dummies-notes/concept-decomposition.md`: noted the golden examples cover both atomicity branches and share the `modular-arithmetic` identity.
- Articles touched: `concepts/dummies-notes/concept-decomposition.md`.

## [2026-06-10] feat | concept-decompose: SKILL.md contract + reference-integrity check (Phase 2 Task 5)

- Authored `.claude/skills/concept-decompose/SKILL.md`: the skill's operating contract — Job (ONE concept → canonical identity + atomicity verdict + direct prerequisites as `decomposition.json`, one level only, never recurse), a 5-step Workflow (canonicalize/kebab slug + plain definition → atomicity test → list load-bearing prerequisites with the jargon rule → reuse registry slugs → validate to `OK     clean`), and a quality bar (repeatable definitions, no nice-to-knows, no self-cycles). References only shipped paths (`references/decomposition-json.md`, `scripts/validate_decomposition.py`).
- Created `scripts/check_skill_refs.py`: zero-dep reference-integrity guard mirroring the illustrator's; fails if SKILL.md cites an inline `references/`/`scripts/`/`examples/` path that doesn't exist.
- Added `TestSkillContract` (2 tests: references exist + contract tokens present) to `scripts/tests/test_validate_decomposition.py`; suite total is now 11 tests, all passing; `check_skill_refs.py` exits 0.
- Updated `knowledge/concepts/dummies-notes/concept-decomposition.md`: added a `## Skill (Phase 2)` section noting the single-level contract now exists at `.claude/skills/concept-decompose/` and that Workflow recursion is Phase 3.
- Articles touched: `concepts/dummies-notes/concept-decomposition.md`.

## [2026-06-10] feat | concept-decompose: decomposition.json schema + zero-dep validator (Phase 2 Task 4)

- Created `.claude/skills/concept-decompose/references/decomposition-json.md`: schema reference for `decomposition.json` — field tables, atomicity rule, slug rules, and a worked RSA example.
- Created `.claude/skills/concept-decompose/scripts/validate_decomposition.py`: zero-dep stdlib validator; `validate(data)` returns `(level, message)` tuples; CLI exits 1 on any ERROR, 2 on wrong usage.
- Created `.claude/skills/concept-decompose/scripts/tests/test_validate_decomposition.py`: 9 tests (TDD — written first, all passing after validator landed).
- Updated `knowledge/concepts/dummies-notes/concept-decomposition.md`: resolved the open atomicity-test question with the shipped rule (one figure ≤ ~6 frames + common-knowledge prerequisites; jargon ⇒ prerequisite; enforced by `validate_decomposition.py`).
- Articles touched: `concepts/dummies-notes/concept-decomposition.md`.

## [2026-06-09] compile | adopt living-doc + seed vision articles

- Adopted the living-documentation methodology (https://github.com/mpklu/living-doc) on this greenfield repo: installed `knowledge/`, `schemas/`, `scripts/` (drift-check, validate-articles), and `actions/drift-check/`.
- Merged the living-doc same-task rule into `CLAUDE.md` alongside the existing project vision.
- Wrote three thin foundational articles capturing the design before code exists: `concept-decomposition`, `illustration-engine`, `atomic-illustration-catalog`.
- Pre-commit hook and GitHub Action deferred until `git init` (repo is not yet under git).

## [2026-06-09] feat | concept-illustrator: figure.json validation + frame-consistency

- Added `validate_figure(dir_path, style_path)` to `scripts/render.py`: validates required fields, resolves frame files, runs `lint_svg` per frame, enforces frame-consistency (all frames must share identical `viewBox`).
- Added constants `FIGURE_REQUIRED` and `FIGURE_PLAYBACK` to encode the schema.
- Created `references/figure-json.md` (field table + rules + example).
- Added `TestValidateFigure` suite (4 tests) to `scripts/tests/test_render.py`; suite now runs 39 tests total.
- Updated `knowledge/concepts/dummies-notes/illustration-engine.md` with figure.json contract and linter summary.

## [2026-06-09] design | dummies_notes architecture spec

- Brainstormed and wrote the architecture design: `docs/superpowers/specs/2026-06-09-dummies-notes-design.md`.
- Decisions: Claude Code skills + a Workflow (no standalone app); autonomous recursive decomposition; output is both a bottom-up explainer doc and an interactive concept map over a shared registry.
- Reframed "reusable" as **referencing** (link covered concepts, don't re-illustrate); the registry is a reference graph, not a dedup cache.
- Style consistency is engineered (shared stylesheet/template + primitive visual-vocabulary + color-role conventions + linter gate), not inherited from reuse.
- Voice: vivid metaphor + plain language, restrained visuals; simplicity wins.
- Added fresh-eyes verification (separate-agent blind-reader + fidelity critic) at two altitudes (per-figure gate, end-to-end chain review) with a bounded repair loop.
- Build phased 1–4; Phase 1 (`concept-illustrator` made real) to be planned next. The three seed concept articles will be refined/renamed as those phases land.

## [2026-06-09] docs | concept-illustrator: author five reference docs

- Authored five canonical reference docs under `.claude/skills/concept-illustrator/references/`: `design-system.md` (palette, color-role conventions, type, canvas geometry, banned decorations), `archetypes.md` (flowchart / structural / illustrative / chart / sequence routing), `visual-vocabulary.md` (lint-clean primitive SVG snippets for list cell, pointer, node, edge, container, stack frame, function box, state styles — the one place literal SVG reuse lives), `voice-and-metaphor.md` (caption voice + metaphor bank), and `review-protocol.md` (blind-reader + fidelity-critic fresh-eyes review, automated in Phase 3).
- All visual-vocabulary SVG snippets verified lint-clean against `render.py` linter rules.
- Added `TestReferenceDocs` suite to `scripts/tests/test_render.py`; full suite now runs 44 tests, all passing.
- Updated `knowledge/concepts/dummies-notes/illustration-engine.md` with a `## Reference docs` section listing all five files.

## [2026-06-09] fix | concept-illustrator: documentation-consistency fixes (Task 9)

- `design-system.md § Color-role conventions`: added clarifying paragraph scoping teal/coral/gray state-roles to illustrative and sequence figures only; structural/flowchart/chart figures should use purple/blue/pink for neutral categories.
- `design-system.md § Canvas & geometry`: replaced informal "~40 px" with precise formula `H = y_max + 40`.
- `archetypes.md § Structural` worked example: changed category bands from `c-coral`/`c-teal` to `c-purple`/`c-blue` to avoid state-color misuse in a pure-category context.
- `visual-vocabulary.md § Graph node`: corrected prose — start/active node uses `c-teal`; `c-coral` is reserved for goal/target node.
- `review-protocol.md § Repair loop`: tightened "approximately two" to "exactly two retries"; added explicit instruction to register flagged and stop retrying after two failures.
- `voice-and-metaphor.md § Voice`: added bullet requiring one caption per frame in sequence figures, stating what is happening and why rather than restating the image.
- Updated `knowledge/concepts/dummies-notes/illustration-engine.md` with `## Color-role scope` section capturing the illustrative/sequence vs structural/flowchart/chart distinction.

## [2026-06-09] compile | Phase 1 — concept-illustrator made real

- Built `.claude/skills/concept-illustrator/`: real SKILL.md, _style.css + template.svg, reference docs (design-system, archetypes, visual-vocabulary, voice-and-metaphor, review-protocol, figure-json), and `scripts/render.py` (lint + figure validation + slideshow viewer + optional PNG), all unit-tested with stdlib unittest (46 tests).
- Added multi-frame figures with the frame-consistency rule; golden quicksort example.
- Matured `illustration-engine.md`; scoped its affects to the skill directory.

## [2026-06-10] fix | concept-illustrator: final-review hardening (CLI guards + doc accuracy + resource leak)

- `scripts/render.py main()`: added path-shape guards for `--viewer` (requires directory) and `--png` (requires `.svg` file); wrong-kind inputs now print a clean ERROR line and return 1 instead of crashing with a traceback.
- `SKILL.md`: corrected false claim that `--theme dark` "forces the dark palette"; replaced with accurate statement that PNG export rasterizes the document's default (light) rendering and `--theme` is reserved for a future enhancement.
- `scripts/check_skill_refs.py`: closed the `open(...).read()` file handle with a `with` block to eliminate ResourceWarning.
- `scripts/tests/test_render.py`: added `TestCli` (5 tests) covering both error-path guards and happy-path lint/viewer cases; suite total is now 51 tests, 1 skip.
- Articles touched: `concepts/dummies-notes/illustration-engine.md`.

## [2026-06-09] doc | narrow illustration-engine drift mapping to SKILL.md + render.py (Phase 1.5)

- Scoped `illustration-engine.md` `affects:` from the broad `concept-illustrator/**` glob to exactly `SKILL.md` and `scripts/render.py`; reference docs and assets no longer trigger article drift checks.
- Updated CLAUDE.md article-mapping table to two specific rows matching the new globs.

## [2026-06-09] docs | concept-illustrator: runbook-first workflow + runbook/commentary in output contract

- `SKILL.md § Workflow step 2`: added explicit runbook-first per-frame order — write runbook (what/why/how, honoring frame-consistency) → draw SVG → write caption + commentary. Noted runbook is persisted in `figure.json` and human-editable for re-runs.
- `SKILL.md § Output contract`: expanded `frames` entry description to list all four required per-frame fields (`file`, `caption`, `runbook`, `commentary`); noted `caption` is the only text shown in the HTML viewer; `commentary` is narration-only for slides/video.
- `knowledge/concepts/dummies-notes/illustration-engine.md`: updated `## figure.json contract` to reflect `{ file, caption, runbook, commentary }` and added runbook-first sentence.
- Articles touched: `concepts/dummies-notes/illustration-engine.md`.

## [2026-06-09] fix | quicksort figure: color-semantics + silent-swap review

- Revised all four frames in `examples/quicksort/` to use an unambiguous color model: `c-coral` = pivot (constant throughout), `c-teal` = current scan target (one cell, never the pivot), `c-gray` = settled left-zone cells, `box` = not-yet-scanned.
- Eliminated the "c-teal means two things" ambiguity (pivot was teal in frames 1–3 and so was the scan target in frame 2).
- Rewrote all four captions to explicitly narrate every swap; no array rearrangement is silent.
- Updated `CLAUDE.md § Current state` to reflect reality: git repo on `main`, pre-commit hook + GitHub Action installed, Phase 1 shipped, correct command references, phases 2–4 not yet built.
- Updated `illustration-engine.md` with `## Golden quicksort example — color-model (revised)` section.
- Articles touched: `concepts/dummies-notes/illustration-engine.md`.

## [2026-06-09] feat | concept-illustrator: enforce runbook + commentary per frame in validate_figure

- `scripts/render.py validate_figure`: added per-frame check — reports ERROR if `runbook` or `commentary` is absent or blank for any frame (including single-frame static figures).
- `scripts/tests/test_render.py`: updated `_write_figure` helper to include `runbook`/`commentary` on every generated frame; added `TestRunbookCommentary` (3 tests). Suite total: 55 tests, 1 skip.
- Articles touched: `concepts/dummies-notes/illustration-engine.md`.

## [2026-06-09] fix | concept-illustrator: workflow-clarity fixes (runbook scope + coordinate planning)

- `SKILL.md § Workflow step 2`: changed "For each frame, work in this order" to "For each frame — including a single static frame — work in this order:" so the runbook-first sub-sequence unambiguously applies to static figures, not just sequences.
- `SKILL.md § Workflow step 2 runbook sub-step`: folded coordinate/layout planning into the runbook sub-step (archetype layout, box positions/coordinates, colour roles, what changes from the previous frame); the box-width formula now appears there, before any SVG.
- `SKILL.md § Workflow`: replaced the separate "Plan coordinates before writing SVG" step with a blockquote note clarifying that coordinate planning happens inside the runbook step, not after drawing. Renumbered subsequent steps (old 4–9 → new 3–8).
- `references/figure-json.md`: trimmed the `runbook` row's Notes cell to just the definition; the standalone bold **runbook-first** paragraph below the table continues to carry the ordering rule.
- Articles touched: `concepts/dummies-notes/illustration-engine.md`.

## [2026-06-10] fix | concept-illustrator: harden per-frame runbook/commentary check in validate_figure

- `scripts/render.py validate_figure`: replaced the `(frame.get(field) or "").strip()` pattern with `isinstance(val, str) and val.strip()`, so non-string values (e.g. `123`) are caught as missing rather than raising `AttributeError`. Added an `else` branch for bare-string frames (e.g. `"frame-01.svg"`) so they now report ERROR ("frame must be an object …") instead of silently bypassing the runbook/commentary check.
- `scripts/tests/test_render.py`: added `test_non_string_runbook_errors` and `test_bare_string_frame_errors` to `TestRunbookCommentary`. Suite total: 57 tests, 1 skip.
- Articles touched: `concepts/dummies-notes/illustration-engine.md`.

## [2026-06-10] feat | concept-registry: seed first entries — quicksort (illustrated) + modular-arithmetic (Phase 2 Task 7)

- Seeded registry via CLI: `quicksort` registered and attached to the Phase 1 golden figure (`.claude/skills/concept-illustrator/examples/quicksort`); `status: illustrated`, relative `figure` path round-trips correctly. `modular-arithmetic` registered with a definition byte-identical to the golden decomposition (`concept-decompose/examples/modular-arithmetic/decomposition.json`); `status: registered`, awaiting its figure.
- `registry/index.json` rebuilt via `scripts/concept-registry index`; reports 2 concepts; byte-identical after test-suite rebuild (`git status` shows no diff).
- Added `TestSeededRegistry` (3 tests) to `scripts/tests/test_concept_registry.py`; suite total: 22 tests, all passing. Concept-decompose suite: 14 tests. Concept-illustrator suite: 57 tests, 1 skip.
- Updated `knowledge/concepts/dummies-notes/atomic-illustration-catalog.md`: noted the registry is live with its first two entries and the byte-identity guarantee; kept `status: thin` since versioning/invalidation is still an open question.
- Articles touched: `concepts/dummies-notes/atomic-illustration-catalog.md`.

## [2026-06-10] doc | scope Phase 2 drift mapping (decompose skill, registry)

- Narrowed `concept-decomposition.md` `affects:` from `src/decomposition/**` to the two concrete Phase 2 paths: `.claude/skills/concept-decompose/SKILL.md` and `.claude/skills/concept-decompose/scripts/validate_decomposition.py`.
- Narrowed `atomic-illustration-catalog.md` `affects:` from `src/catalog/**` to `scripts/concept_registry.py` and `registry/**`.
- Updated CLAUDE.md article-mapping table: replaced two broad rows with four specific rows matching the new globs. Illustration-engine rows unchanged.

## [2026-06-10] feat | concept-illustrator: closure rule — process figures end with the result

- `SKILL.md § Workflow step 2`: added the **End with the result** rule — a process/sequence figure must close with a frame showing the end state; for recursive or iterative algorithms a final fast-forward frame may collapse the remaining iterations and show the finished result, so the reader sees the mechanism AND that it worked.
- `references/archetypes.md § Sequence`: added the same closure rule citing the quicksort example (four frames show one partition pass; a final frame fast-forwards to the fully sorted array).
- Golden quicksort example extended from 4 to 5 frames: added `frame-05.svg` (runbook-first), the fast-forward closure showing the fully sorted `[1, 2, 3, 5, 8, 9]`. The pivot 3 stays coral at index 2 (placed pivots never move — pays off the dividing-wall metaphor); every other cell is gray and sorted. Appended the matching `frame-05` entry (file/caption/runbook/commentary) to `examples/quicksort/figure.json` and rebuilt `figure.html` (now 5 SVGs). Frames 1–4 untouched.
- Validation: figure lints clean, viewer rebuilt with 5 frames, 57 tests / 1 skip, `check_skill_refs.py` exit 0, articles valid.
- Articles touched: `concepts/dummies-notes/illustration-engine.md`.

## [2026-06-10] fix | concept-registry: harden against corrupted/partial entries (Task 3 amend)

- `scripts/concept_registry.py _read_json`: wraps `open`/`json.load` in a try/except; `OSError` and `json.JSONDecodeError` now raise `RegistryError("corrupt registry entry at …")` instead of propagating a raw traceback.
- `scripts/concept_registry.py build_index`: added try/except around the required-key lookups; `KeyError`/`TypeError` raises `RegistryError("malformed entry for '…'")`.
- `scripts/tests/test_concept_registry.py`: added `TestRobustness` (4 tests — corrupt JSON, corrupt-via-CLI, partial entry in index, attach-figure relpath outside root). Suite total: 19 tests, all passing.
- Articles touched: `concepts/dummies-notes/atomic-illustration-catalog.md`.

## [2026-06-10] feat | concept-registry: attach-figure, index, CLI wrapper (Phase 2 Task 3)

- Added `attach_figure(root, slug, figure_dir)` to `scripts/concept_registry.py`: validates slug is already registered and `figure_dir` contains `figure.json`, then stores the relative path and transitions `status` to `illustrated`.
- Added `build_index(root)`: scans all `<slug>/entry.json` files under root, writes `registry/index.json`, and returns the summary dict.
- Added `main(argv=None)` CLI with subcommands `register`, `lookup`, `attach-figure`, and `index`; errors from `RegistryError` print a clean `ERROR` line and return exit code 1.
- Created executable wrapper `scripts/concept-registry` so all verbs are reachable from the shell without a `python3 -m` prefix.
- Added `TestAttachAndIndex` (4 tests) and `TestCli` (4 tests) to `scripts/tests/test_concept_registry.py`; suite total is now 15 tests, all passing.
- Updated `knowledge/concepts/dummies-notes/atomic-illustration-catalog.md`: documented `status` lifecycle, `figure` relative-path field, and all four CLI verbs.

## [2026-06-10] feat | concept-registry: zero-dep register + lookup (Phase 2 Task 2)

- Created `scripts/concept_registry.py`: `register(root, slug, name, definition, prerequisites=())` and `lookup(root, slug)`. Entries persist at `registry/<slug>/entry.json`. Same-slug + same-definition is idempotent; same-slug + different-definition raises `RegistryError`; invalid slugs (non-kebab-case) and blank name/definition also raise `RegistryError`.
- Created `scripts/tests/__init__.py` and `scripts/tests/test_concept_registry.py` (7 tests, all passing).
- Updated `knowledge/concepts/dummies-notes/atomic-illustration-catalog.md`: resolved the open storage question — filesystem `registry/<slug>/entry.json` + rebuildable `registry/index.json` via `scripts/concept_registry.py`.

## [2026-06-10] feat | first dummies-notes workflow run (Phase 3 smoke)

- Ran the orchestrator end-to-end on "modular arithmetic": 1 node, atomic; figure
  illustrated into `registry/modular-arithmetic/figure/` (5 frames, lint clean);
  blind-reader + fidelity-critic review passed with no repairs; entry promoted to
  `illustrated`; `graph_check --require-illustrated` clean. 6 agents total.
- Hardened the workflow script to accept JSON-string args (caller footgun).
- Updated the seeded-registry test pin: modular-arithmetic is now illustrated.

## [2026-06-10] feat | first full dummies-notes run (Phase 4 acceptance)

- "RSA encryption" (maxDepth 1): covered-stop on modular-arithmetic; prime-numbers
  + asymmetric-cryptography illustrated (reviews clean); composition figure for the
  root; prerequisite edges persisted; output/rsa-encryption/index.html + map.html
  assembled; graph check clean. 14 agents.
- Chain review FAILED with 4 substantive graph-level gaps (chain-review.json ships
  with the output) — the capstone check working as designed. Finding: composition
  figures map structure but don't teach the target's mechanism; deeper runs needed
  for security-core nodes (factoring hardness).

## [2026-06-10] feat | user run: TCP connection lifecycle

- First user-requested topic: 4 nodes, 2 new figures (reviews clean), composition
  figure, edges persisted, deliverable assembled; graph check clean. 15 agents.
- Chain review failed with 4 gaps (shipped in chain-review.json) — repeating the
  RSA pattern: the composition figure doesn't teach the target's own mechanism,
  and a non-atomic mid-graph node (best-effort-delivery) renders without a figure
  or stub. Two-topic confirmation of the documented future-work items.

## [2026-06-10] finding | deeper TCP run exposes the atomic↔illustrate coupling

- Re-ran TCP at maxDepth 2. best-effort-delivery decomposed NON-atomic with a
  single prereq (data-packets, already illustrated), so the run added no new
  figure (illustrated:[], 7 agents) and the chain gaps persisted.
- Root cause (sharper than the RSA composition gap): the system illustrates only
  atomic leaves + the root composition. A node is "non-atomic" if it has ANY
  prerequisite — but best-effort-delivery's OWN mechanism is figure-sized (its
  decomposition literally says so). "Has a prerequisite" != "not worth drawing".
- Fix is a design change, not a deeper run: decouple "illustrate" from "atomic
  leaf" — give a node its own mechanism figure whenever its mechanism is
  figure-sized, regardless of prerequisites. Same root cause as RSA's missing
  mechanism figure. Candidate Phase 5.

## [2026-06-10] feat | Phase 5 acceptance — TCP re-run closes the chain-review gap

- Reset tcp-connection-lifecycle + best-effort-delivery; re-ran TCP (maxDepth 2).
- 5 nodes; root illustrated with a self-sufficient 5-frame lifecycle figure (not a
  composition map); unreliable-delivery + delivery-acknowledgement illustrated
  (non-atomic-but-figurable — the Phase 5 fix); communication-protocol + data-packets
  reused; computer-network honest frontier. 16 agents.
- chain_review_pass: TRUE (4 blocking gaps -> 1 minor frontier note). Self-sufficient
  mechanism figures work; composition retired. graph check clean; 60 tests green.

- 2026-06-11 — Phase 6 (video engine): began `scripts/build_video.py` + new article `video-engine.md`. Manifest-first; HTML player + opt-in MP4; reuses assemble ordering + render.export_png.

## [2026-06-11] feat(video): manifest builder — Task 2 of Video Engine

- `scripts/build_video.py` created: `build_manifest`, `load_frames`, `_duration_for`, `_slide`. Shared constants `DEFAULT_WPM`, `MIN_DUR`, `MAX_DUR`, `MIN_TTS_DUR`, `STAGE` defined at module level for use by later tasks.
- Reuses `asm.load_full_graph`, `asm.find_root`, `asm.topo_order`, `asm._figure_dir_for`, and `lookup` from the existing modules — no ordering logic reimplemented.
- `scripts/tests/test_build_video.py` created: 7 tests covering duration clamping (min/max/exact), slide ordering (prereqs before root), slide kinds (title/section/frame/closing counts), frame-slide field shapes, figureless-node skipping, and crossfade-only-within-concept transition rule.
- All 67 tests passing.
- Articles touched: `concepts/dummies-notes/video-engine.md`.

## [2026-06-11] feat(video): stage_svg — Task 4 of Video Engine

- `stage_svg(slide, stage)` added to `scripts/build_video.py`: composes one 16:9 SVG per slide by nesting the figure SVG (frame slides) or rendering a centered text card (title/section/closing).
- `_read_inner_svg(path)` strips XML prolog before `<svg` tag; `_esc(text)` escapes all interpolated user text.
- 2 new tests (`TestStageSvg`) added to `scripts/tests/test_build_video.py`: well-formed XML asserted via `ET.fromstring`, nested-SVG count verified, caption presence verified. 12 tests total, all passing.
- Articles touched: `concepts/dummies-notes/video-engine.md`.

## [2026-06-11] feat(video): HTML player — Task 5 of Video Engine

- `.claude/skills/concept-illustrator/assets/video.template.html` created: self-contained player with `{{SLIDES_HTML}}` and `{{MANIFEST_JSON}}` substitution points, crossfade/cut transitions, play/pause + prev/next + progress bar, optional Web Speech TTS narration toggle.
- `_slide_html(slide)` and `build_player(manifest, template_path, out_path)` added to `scripts/build_video.py`. Frame slides inline raw figure SVG via `_read_inner_svg`; card slides render caption as a styled div. Injected manifest is lightweight (no SVG text — only `kind`, `concept_slug`, `caption`, `narration`, `duration_s`, `transition` per slide).
- 1 new test (`TestPlayer`) added: 13 tests total, all passing.
- Articles touched: `concepts/dummies-notes/video-engine.md`.

## [2026-06-11] fix(video): escape injected manifest JSON for inline <script> context

- `build_player` in `scripts/build_video.py`: after `json.dumps(light)`, replace `<` → `<`, `>` → `>`, `&` → `&` to prevent narration/caption text containing `</script>` from breaking out of the inline script block (HTML injection vector).
- Docstring added to `build_player`; shared-marker-id assumption comment added to `_slide_html`.
- Regression test `TestPlayer.test_player_escapes_script_breakout_in_narration` added. 74 tests total, all passing.
- Articles touched: `concepts/dummies-notes/video-engine.md`.

## [2026-06-11] fix(video): robustness + docstring fixes for render_mp4

- Guard empty manifest: `render_mp4` returns `(None, ["empty manifest — no slides to render."])` when `manifest["slides"]` is absent/empty, preventing `IndexError` in `_build_silent_video` (`pngs[-1]`).
- Diagnostic when all say segments fail: appends a note when `have_say` is True but no segment succeeded.
- Docstrings clarified: `_effective_durations` and `_build_audio_track`.
- Test file: `import shutil` and `from unittest import mock` moved to the top stdlib block (were mid-file).
- 18 tests, 1 skip, all passing. `validate-articles` exit 0.
- Articles touched: `concepts/dummies-notes/video-engine.md`.

## [2026-06-11] feat(video): build() orchestrator + CLI — Task 7 of Video Engine

- `build(graph_dir, registry_root, out_dir, fmt, wpm, stage)` added to `scripts/build_video.py`: orchestrates `build_manifest` → write files → `build_player` / `render_mp4` based on `fmt`. Returns `(result_dict, issues)` or `(None, issues)` on ERROR.
- `main(argv)` CLI added: `--format html|mp4|both`, `--wpm`, `--out`, `--registry`; exits 0 on success, 1 on error. Single `if __name__ == "__main__": sys.exit(main())` block at end of file.
- 3 new tests (`TestBuildAndCli`): 21 tests total, 1 skip, all passing.
- Smoke test: `tcp-connection-lifecycle` — 19 slides, `video.html` 109 KB with `window.__MANIFEST__` and 14 inline SVGs.
- Articles touched: `concepts/dummies-notes/video-engine.md`.

## [2026-06-11] fix(video): portable manifest.json + video_html in result + CLI output improvement

- `scripts/build_video.py`: added `_REPO = os.path.dirname(_HERE)`. `build()` now writes repo-relative `image` paths in the on-disk `manifest.json` (via portable dict); in-memory manifest keeps absolute paths for renderers. `result` dict gains `video_html` key. CLI `OK` line points at `video.html` when produced.
- `scripts/tests/test_build_video.py`: added `test_manifest_image_paths_not_absolute` to `TestBuildAndCli`. 22 tests, 1 skip, all passing.
- `output/tcp-connection-lifecycle/video/manifest.json` regenerated with relative paths (`grep -c "/Users/" → 0`).
- Articles touched: `concepts/dummies-notes/video-engine.md`.

- 2026-06-11 — Phase 6: wired opt-in `Video` phase into dummies-notes.js (makeVideo/videoFormat); runs build_video.py after Assemble. Default runs unchanged.
- 2026-06-11 — Phase 6 COMPLETE (video engine shipped): scripts/build_video.py (manifest → script.md/captions.srt + self-contained HTML player; opt-in MP4 via ffmpeg+say with silent fallback), video.template.html, opt-in workflow Video phase. 158 tests green (1 ffmpeg-dependent MP4 smoke skipped). MP4 not yet validated end-to-end (no ffmpeg+rasterizer on the dev machine).
