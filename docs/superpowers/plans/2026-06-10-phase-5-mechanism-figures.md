# Phase 5 — self-sufficient mechanism figures — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split the decompose contract's `atomic` into two axes (`atomic` = stop decomposing; `mechanism_figurable` = drawable standalone), illustrate every figurable node (not just leaves), retire composition figures, and make every figure self-sufficient with optional "go deeper" prerequisite references.

**Architecture:** Additive `mechanism_figurable` boolean on `decomposition.json` (validator + skill + goldens). The workflow's illustrate filter flips from `atomic` to `mechanism_figurable` and the compose-from-children step is deleted. `graph_check`'s coverage check and `assemble.py`'s "pending" branch key off `mechanism_figurable` (defaulting to `atomic` for pre-Phase-5 graph files). The illustrator contract gains a self-sufficiency rule and commentary cross-references; its compose mode is removed. Acceptance re-runs the TCP topic after a one-time reset of two stale entries.

**Tech Stack:** Python 3 stdlib + unittest; the Workflow JS runtime. No new dependencies. Spec: `docs/superpowers/specs/2026-06-10-mechanism-figures-design.md`.

**Conventions:**
- Suites: registry+graph+assemble `python3 -m unittest discover -s scripts/tests -p 'test_*.py'`; decompose `... -s .claude/skills/concept-decompose/scripts/tests ...`; illustrator `... -s .claude/skills/concept-illustrator/scripts/tests ...`.
- **Drift gate (all surfaces already mapped):** `validate_decomposition.py` + decompose `SKILL.md` → `concept-decomposition.md`; illustrator `SKILL.md` → `illustration-engine.md`; `.claude/workflows/**`, `scripts/graph_check.py`, `scripts/assemble.py` → `orchestration-workflow.md`; `registry/**` → `atomic-illustration-catalog.md`. A commit touching a mapped path MUST update its article in the same commit; reference docs/tests are unmapped. Never `--no-verify`; STOP if unexpectedly blocked.
- Articles keep plain `updated: 2026-06-10` dates.

## Model policy

Implementers **sonnet** (edits are specified verbatim below). Reviews: spec=sonnet, quality/final=opus. Task 7 (acceptance) is **controller-run** (invokes the Workflow tool — consent obtained at execution handoff). Workflow agents inherit the session model.

## File structure

| File | Change | Task |
|------|--------|------|
| `.claude/skills/concept-decompose/scripts/validate_decomposition.py` (+tests) | require `mechanism_figurable` bool | 1 |
| `.claude/skills/concept-decompose/references/decomposition-json.md` | document the field + two axes | 1 |
| `.claude/skills/concept-decompose/examples/*/decomposition.json` | add the field to both goldens | 1 |
| `.claude/skills/concept-decompose/SKILL.md` (+ contract test) | two-axis guidance | 2 |
| `.claude/skills/concept-illustrator/SKILL.md` (+ test) | self-sufficiency rule, commentary cross-refs, retire compose | 3 |
| `scripts/graph_check.py` (+tests) | figurable coverage | 4 |
| `.claude/workflows/dummies-notes.js` | illustrate filter → figurable; delete compose; self-sufficiency prompt | 5 |
| `scripts/assemble.py` (+tests) | pending branch keys off figurable | 6 |
| `registry/*`, `output/tcp-connection-lifecycle/*` | acceptance re-run artifacts | 7 |
| knowledge articles | matured/accurate | 8 |

---

## Task 1: `mechanism_figurable` in the validator, schema doc, and goldens

**Model: sonnet.** **Files:** Modify `.claude/skills/concept-decompose/scripts/validate_decomposition.py`, `.claude/skills/concept-decompose/scripts/tests/test_validate_decomposition.py`, `.claude/skills/concept-decompose/references/decomposition-json.md`, both `examples/*/decomposition.json`; Modify `knowledge/concepts/dummies-notes/concept-decomposition.md` + `knowledge/log.md` (validate_decomposition.py is mapped).

- [ ] **Step 1: Update the test `good()` helper and add failing tests**

In `test_validate_decomposition.py`, the `good()` helper returns a dict without the new field. Add `"mechanism_figurable": True,` to it (e.g. right after the `"atomic": False,` line). Then append to `class TestValidate` (as new methods):

```python
    def test_missing_mechanism_figurable_errors(self):
        d = good()
        del d["mechanism_figurable"]
        self.assertTrue(any("mechanism_figurable" in m for m in errors(d)))

    def test_mechanism_figurable_must_be_bool(self):
        d = good()
        d["mechanism_figurable"] = "yes"
        self.assertTrue(any("mechanism_figurable" in m for m in errors(d)))

    def test_non_atomic_figurable_is_clean(self):
        d = good()  # atomic False, mechanism_figurable True, one prereq
        self.assertEqual(errors(d), [])

    def test_non_atomic_non_figurable_is_clean(self):
        d = good()
        d["mechanism_figurable"] = False  # a genuine umbrella concept
        self.assertEqual(errors(d), [])
```

- [ ] **Step 2: Run to verify failure**

Run: `python3 -m unittest discover -s .claude/skills/concept-decompose/scripts/tests -p 'test_*.py'`
Expected: FAIL — `test_missing_mechanism_figurable_errors` / `test_mechanism_figurable_must_be_bool` fail (no such check yet). The golden-example tests will ALSO fail once Step 3 lands and before Step 5 — that's expected; Step 5 fixes the goldens.

- [ ] **Step 3: Add the check to `validate_decomposition.py`**

In `validate()`, immediately after the `atomic` check block:
```python
    if not isinstance(data.get("atomic"), bool):
        issues.append(("ERROR", "'atomic' must be true or false (a JSON bool)"))
```
add:
```python
    if not isinstance(data.get("mechanism_figurable"), bool):
        issues.append(("ERROR", "'mechanism_figurable' must be true or false (a JSON bool)"))
```

- [ ] **Step 4: Document the field in `decomposition-json.md`**

In the top-level fields table, add a row after the `atomic` row:
```markdown
| `mechanism_figurable` | bool | yes | can THIS concept's own mechanism be taught self-sufficiently in one figure, regardless of prerequisites? Independent of `atomic`. |
```
And add a short paragraph after the Atomicity section:
```markdown
## Two axes: atomic vs mechanism_figurable

`atomic` and `mechanism_figurable` are independent. `atomic` answers "should we
stop decomposing?" (are the remaining prerequisites common knowledge).
`mechanism_figurable` answers "is this concept's own mechanism one self-sufficient
figure?" — judged *assuming* the prerequisites are understood elsewhere. A concept
can be non-atomic (it has prerequisites worth their own figures) yet figurable (its
own mechanism is one figure) — e.g. a network protocol's connection lifecycle. Such
a concept gets its own self-sufficient figure AND its prerequisites get theirs.
```

- [ ] **Step 5: Add the field to both golden examples**

In `examples/modular-arithmetic/decomposition.json` add `"mechanism_figurable": true,` (alongside `atomic`). In `examples/rsa-encryption/decomposition.json` add `"mechanism_figurable": true,`. (Both are figurable: modular-arithmetic is a clock-face figure; RSA's mechanism — two keys, lock/unlock — is one figure even though it's non-atomic.)

- [ ] **Step 6: Run to verify pass**

Run: `python3 -m unittest discover -s .claude/skills/concept-decompose/scripts/tests -p 'test_*.py'`
Expected: PASS (existing + 4 new). Also confirm the goldens validate: `python3 .claude/skills/concept-decompose/scripts/validate_decomposition.py .claude/skills/concept-decompose/examples/rsa-encryption/decomposition.json` → `OK     clean`.

- [ ] **Step 7: Update the article + commit**

In `concept-decomposition.md`, add a sentence under the identity/atomicity material: the contract now carries `mechanism_figurable` (drawable standalone) separately from `atomic` (stop decomposing); a non-atomic concept can still be figurable. Keep `status: mature`, `updated: 2026-06-10`. Append a `knowledge/log.md` line.

```bash
git add .claude/skills/concept-decompose/ knowledge/
git commit -m "feat(decompose): add mechanism_figurable axis to the contract"
```

---

## Task 2: Two-axis guidance in the decompose `SKILL.md`

**Model: sonnet.** **Files:** Modify `.claude/skills/concept-decompose/SKILL.md`, `.claude/skills/concept-decompose/scripts/tests/test_validate_decomposition.py`; Modify `knowledge/concepts/dummies-notes/concept-decomposition.md` + `knowledge/log.md` (SKILL.md mapped).

- [ ] **Step 1: Extend the contract-token test**

In `test_validate_decomposition.py`, `class TestSkillContract`, `test_skill_md_covers_the_contract` checks for tokens. Add `"mechanism_figurable"` to its token list.

- [ ] **Step 2: Run to verify it fails**

Run: `python3 -m unittest discover -s .claude/skills/concept-decompose/scripts/tests -p 'test_*.py'`
Expected: FAIL — `SKILL.md missing 'mechanism_figurable'`.

- [ ] **Step 3: Add the two-axis section to `SKILL.md`**

After the atomicity test step, add:
```markdown
## Two axes: stop vs draw

`atomic` and `mechanism_figurable` are SEPARATE judgments — set both.

- **`atomic`** — stop decomposing? True when the remaining prerequisites are
  common knowledge for the audience.
- **`mechanism_figurable`** — could ONE self-sufficient figure teach this
  concept's own mechanism, *assuming* its prerequisites are understood elsewhere?

These do not move together. A connection lifecycle or a public-key scheme is
**not atomic** (it rests on packets, on primes) yet **is figurable** (its own
mechanism — the handshake, the two keys — is one clear figure). Mark such a
concept `atomic: false, mechanism_figurable: true`: the workflow will give it its
own self-sufficient figure AND keep decomposing its prerequisites. Reserve
`mechanism_figurable: false` for a genuine umbrella with no single mechanism of
its own (a broad field). When in doubt, prefer figurable — a self-sufficient
figure is the whole point.
```

- [ ] **Step 4: Run to verify pass**

Run: `python3 -m unittest discover -s .claude/skills/concept-decompose/scripts/tests -p 'test_*.py'`
Expected: PASS. Also `python3 .claude/skills/concept-decompose/scripts/check_skill_refs.py; echo $?` → 0.

- [ ] **Step 5: Update the article + commit**

In `concept-decomposition.md`, ensure the two-axis rule is described (extend the Task 1 sentence if needed). Append a `knowledge/log.md` line.

```bash
git add .claude/skills/concept-decompose/ knowledge/
git commit -m "docs(decompose): SKILL.md two-axis guidance (stop vs draw)"
```

---

## Task 3: Illustrator contract — self-sufficiency, commentary cross-refs, retire compose

**Model: sonnet.** **Files:** Modify `.claude/skills/concept-illustrator/SKILL.md`, `.claude/skills/concept-illustrator/scripts/tests/test_render.py`; Modify `knowledge/concepts/dummies-notes/illustration-engine.md` + `knowledge/log.md` (SKILL.md mapped).

- [ ] **Step 1: Replace the compose contract test with a self-sufficiency test**

In `test_render.py`, `class TestSkillRefs`, the method `test_skill_md_documents_composition_mode` checks for tokens `("Composition figures", "compose-from-children")`. REPLACE that method with:

```python
    def test_skill_md_documents_self_sufficiency(self):
        with open(os.path.join(os.path.dirname(SCRIPTS_DIR), "SKILL.md"),
                  encoding="utf-8") as fh:
            text = fh.read()
        for token in ("Self-sufficient", "go deeper"):
            self.assertIn(token, text)
        self.assertNotIn("compose-from-children", text)  # retired in Phase 5
```

- [ ] **Step 2: Run to verify it fails**

Run: `python3 -m unittest discover -s .claude/skills/concept-illustrator/scripts/tests -p 'test_*.py'`
Expected: FAIL — "Self-sufficient" not found AND/OR "compose-from-children" still present.

- [ ] **Step 3: Edit `SKILL.md`**

(a) DELETE the entire `## Composition figures (compose-from-children)` section (heading through the end of that section, up to the next `##`).

(b) Add a new section (place it near the output-contract / archetype guidance):
```markdown
## Self-sufficient figures

Every figure must teach its own concept STANDALONE. A reader who lands on this
figure cold — without having seen any prerequisite's figure — should still grasp
the concept's mechanism. Illustrate THIS concept's own mechanism; you may name a
prerequisite in passing, but never require the reader to have studied it.

A concept with prerequisites is illustrated the same way as a leaf — the only
difference is the **commentary**: when the concept builds on fundamentals that
have their own figures, add a short "go deeper" pointer in the commentary, e.g.
"for the clock-math underneath this, see the modular-arithmetic figure." It is a
reference, not a dependency — the figure stands on its own; the pointer is for the
curious. (Reader-facing prerequisite links live in the assembled explainer's
"Builds on" list; these commentary pointers serve the narration/transcript.)
```

- [ ] **Step 4: Run to verify pass**

Run: `python3 -m unittest discover -s .claude/skills/concept-illustrator/scripts/tests -p 'test_*.py'`
Expected: PASS (58, 1 skip). `python3 .claude/skills/concept-illustrator/scripts/check_skill_refs.py; echo $?` → 0 (the deleted section referenced no unique paths; if it did, confirm nothing now-missing is still referenced).

- [ ] **Step 5: Update the article + commit**

In `illustration-engine.md`, replace the compose-from-children mention with: figures are self-sufficient (teach the concept standalone); commentary carries optional "go deeper" references to prerequisite figures; the Phase-4 compose-from-children mode is retired (Phase 5). Keep `status: mature`, `updated: 2026-06-10`. Append a `knowledge/log.md` line.

```bash
git add .claude/skills/concept-illustrator/ knowledge/
git commit -m "feat(illustrator): self-sufficiency rule + commentary go-deeper refs; retire compose"
```

---

## Task 4: graph_check — figurable coverage

**Model: sonnet.** **Files:** Modify `scripts/graph_check.py`, `scripts/tests/test_graph_check.py`; Modify `knowledge/concepts/dummies-notes/orchestration-workflow.md` + `knowledge/log.md` (graph_check.py mapped).

- [ ] **Step 1: Write the failing tests**

In `test_graph_check.py`, the `write_decomp` helper writes a decomposition without `mechanism_figurable`. Update it to write the field, defaulting to `atomic` unless overridden — change its signature and body:

```python
def write_decomp(graph_dir, slug, atomic, prereqs=(), figurable=None):
    os.makedirs(graph_dir, exist_ok=True)
    data = {
        "concept": {"slug": slug, "name": slug, "definition": f"{slug} def."},
        "audience": "a curious adult with no domain background",
        "atomic": atomic,
        "mechanism_figurable": atomic if figurable is None else figurable,
        "atomic_reason": "test fixture.",
        "prerequisites": [
            {"slug": p, "name": p, "definition": f"{p} def.", "why": "needed."}
            for p in prereqs
        ],
    }
    with open(os.path.join(graph_dir, f"{slug}.json"), "w", encoding="utf-8") as fh:
        json.dump(data, fh)
```

Append a new test class:
```python
class TestFigurableCoverage(unittest.TestCase):
    def test_nonatomic_figurable_unillustrated_errors(self):
        with tempfile.TemporaryDirectory() as base:
            graph, registry = os.path.join(base, "g"), os.path.join(base, "r")
            write_decomp(graph, "best-effort", False, ["packets"], figurable=True)
            write_decomp(graph, "packets", True)
            reg.register(registry, "best-effort", "B", "b def.")
            reg.register(registry, "packets", "P", "p def.")
            nodes, _ = gc.load_graph(graph)
            issues = gc.check_coverage(nodes, registry, require_illustrated=True)
            self.assertTrue(any("not illustrated" in m for m in errors(issues)
                                if "best-effort" in m))

    def test_nonatomic_nonfigurable_is_exempt(self):
        with tempfile.TemporaryDirectory() as base:
            graph, registry = os.path.join(base, "g"), os.path.join(base, "r")
            write_decomp(graph, "umbrella", False, ["packets"], figurable=False)
            write_decomp(graph, "packets", True)
            reg.register(registry, "umbrella", "U", "u def.")
            reg.register(registry, "packets", "P", "p def.")
            reg.attach_figure(registry, "packets",
                              _mk_fig(os.path.join(base, "fig")))
            nodes, _ = gc.load_graph(graph)
            issues = gc.check_coverage(nodes, registry, require_illustrated=True)
            self.assertFalse(any("umbrella" in m for m in errors(issues)))


def _mk_fig(d):
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "figure.json"), "w", encoding="utf-8") as fh:
        json.dump({"concept_slug": "packets"}, fh)
    return d
```

- [ ] **Step 2: Run to verify failure** — `test_nonatomic_figurable_unillustrated_errors` fails (coverage still keys off `atomic`).

- [ ] **Step 3: Update `graph_check.py`**

In `load_graph`, change the node dict line:
```python
        nodes[slug] = {"atomic": data["atomic"], "prerequisites": prereqs}
```
to:
```python
        nodes[slug] = {"atomic": data["atomic"],
                       "mechanism_figurable": bool(data.get("mechanism_figurable", data["atomic"])),
                       "prerequisites": prereqs}
```
In `check_coverage`, change:
```python
        if node["atomic"] and require_illustrated and entry["status"] != "illustrated":
            issues.append(("ERROR", f"{slug}: atomic but not illustrated"))
```
to:
```python
        if node["mechanism_figurable"] and require_illustrated and entry["status"] != "illustrated":
            issues.append(("ERROR", f"{slug}: figurable but not illustrated"))
```

- [ ] **Step 4: Run to verify pass** — full scripts suite green (existing graph_check tests still pass: their atomic nodes default figurable=atomic).

- [ ] **Step 5: Update the article + commit**

In `orchestration-workflow.md` graph_check section: `--require-illustrated` now requires a figure for every **figurable** node (not just atomic); non-figurable nodes are exempt. Append a `knowledge/log.md` line.

```bash
git add scripts/ knowledge/
git commit -m "feat(graph_check): require figures for figurable nodes, not just atomic"
```

---

## Task 5: Workflow — illustrate figurable nodes, delete compose, self-sufficiency prompt

**Model: sonnet.** **Files:** Modify `.claude/workflows/dummies-notes.js`; Modify `knowledge/concepts/dummies-notes/orchestration-workflow.md` + `knowledge/log.md` (mapped).

- [ ] **Step 1: Thread `mechanism_figurable` into `nodes`**

In the decompose loop, the `nodes[slug] = { ... }` object literal — add a field after `atomic: d.atomic,`:
```javascript
    mechanism_figurable: d.mechanism_figurable,
```
Also add `mechanism_figurable` to `DECOMP_SCHEMA`: in its `properties`, add `mechanism_figurable: { type: 'boolean' },` and add `'mechanism_figurable'` to its `required` array.

- [ ] **Step 2: Flip the illustrate filter and carry prerequisites**

Replace the `toIllustrate` block:
```javascript
const toIllustrate = Object.entries(nodes)
  .filter(([slug, n]) => !n.covered && n.atomic === true &&
    !(covered[slug] && covered[slug].status === 'illustrated'))
  .map(([slug, n]) => ({ slug, name: n.name, definition: n.definition }))
log(`${toIllustrate.length} atomic concept(s) to illustrate`)
```
with:
```javascript
const toIllustrate = Object.entries(nodes)
  .filter(([slug, n]) => !n.covered && n.mechanism_figurable === true &&
    !(covered[slug] && covered[slug].status === 'illustrated'))
  .map(([slug, n]) => ({ slug, name: n.name, definition: n.definition,
    prereqs: (n.prereqMeta || []).map(p => p.name) }))
log(`${toIllustrate.length} figurable concept(s) to illustrate`)
```

- [ ] **Step 3: Add the self-sufficiency instruction to `illustrate()`**

In the `illustrate(c, critique)` function's prompt string, after the `Concept slug/Name/Definition` line, insert:
```javascript
    (c.prereqs && c.prereqs.length
      ? `This concept builds on: ${c.prereqs.join(', ')}. Make the figure SELF-SUFFICIENT — teach this concept's own mechanism so a reader who has not seen those prerequisites still understands it. In the commentary, add a short "go deeper" pointer to each prerequisite that has its own figure (reference, do not re-teach).\n`
      : '') +
```

- [ ] **Step 4: Delete the compose-from-children step**

Remove the entire block starting at `const rootNode = nodes[rootSlug]` through the closing `}` of the `if (rootNode && rootNode.atomic === false) { ... }` (the compose `agent(...)` call). The figurable root is now illustrated in the pipeline like any node; no composition fallback. Leave the `const assembled = await agent(...)` that follows intact.

In `meta.phases`, change the Assemble entry's `detail` to drop the compose wording:
```javascript
    { title: 'Assemble', detail: 'render index.html + map.html from the graph + figures' },
```

- [ ] **Step 5: Verify**

```bash
node --check .claude/workflows/dummies-notes.js && echo "node ok"
python3 - <<'EOF'
t = open('.claude/workflows/dummies-notes.js', encoding='utf-8').read()
assert "mechanism_figurable === true" in t, "filter not flipped"
assert "compose-from-children" not in t and "compose:${rootSlug}" not in t, "compose not removed"
assert "SELF-SUFFICIENT" in t, "self-sufficiency prompt missing"
assert t.count('{') == t.count('}') and t.count('(') == t.count(')')
print("workflow ok")
EOF
```
Expected: `node ok` and `workflow ok`.

- [ ] **Step 6: Update the article + commit**

In `orchestration-workflow.md`, update the Run shape: Illustrate covers every **figurable** node (atomic or not); the Assemble step no longer composes a root figure (compose retired) — a figurable root gets a self-sufficient figure in the Illustrate pass. Append a `knowledge/log.md` line.

```bash
git add .claude/workflows/ knowledge/
git commit -m "feat(workflow): illustrate figurable nodes; self-sufficiency prompt; delete compose"
```

---

## Task 6: assemble.py — "pending" branch keys off figurable

**Model: sonnet.** **Files:** Modify `scripts/assemble.py`, `scripts/tests/test_assemble.py`; Modify `knowledge/concepts/dummies-notes/orchestration-workflow.md` + `knowledge/log.md` (assemble.py mapped).

- [ ] **Step 1: Write the failing test**

In `test_assemble.py`, the `write_decomp` helper omits `mechanism_figurable`. Update it to include it (default to `atomic`), mirroring Task 4 — change its signature to `def write_decomp(graph_dir, slug, atomic, prereqs=(), figurable=None):` and add `"mechanism_figurable": atomic if figurable is None else figurable,` to the data dict.

Append to `class TestDegradation`:
```python
    def test_nonatomic_figurable_without_figure_shows_pending(self):
        with tempfile.TemporaryDirectory() as base:
            graph = os.path.join(base, "out", "graph")
            registry = os.path.join(base, "registry")
            write_decomp(graph, "lifecycle", False, ["packets"], figurable=True)
            write_decomp(graph, "packets", True)
            reg.register(registry, "lifecycle", "Lifecycle", "Plain definition of lifecycle.")
            reg.register(registry, "packets", "Packets", "Plain definition of packets.")
            reg.attach_figure(registry, "packets",
                              make_figure(os.path.join(registry, "packets", "figure"), "packets"))
            asm.assemble(graph, registry, os.path.join(base, "out"))
            text = open(os.path.join(base, "out", "index.html"), encoding="utf-8").read()
            lifecycle = text[text.index('<section id="lifecycle"'):]
            self.assertIn("Figure pending", lifecycle)
```

- [ ] **Step 2: Run to verify failure** — the non-atomic figurable `lifecycle` node currently shows no "Figure pending" (the branch keys off `atomic`, which is False).

- [ ] **Step 3: Update `assemble.py`**

In `load_full_graph`, the node dict — add a field after the `"atomic": ...` line:
```python
            "mechanism_figurable": bool(data.get("mechanism_figurable", data.get("atomic"))),
```
In `build_explainer`, change the per-node branch:
```python
        elif node["atomic"]:
            parts.append('<p class="meta">Figure pending for this concept.</p>')
```
to:
```python
        elif node["mechanism_figurable"]:
            parts.append('<p class="meta">Figure pending for this concept.</p>')
```

- [ ] **Step 4: Run to verify pass** — full scripts suite green (existing assemble tests: atomic nodes default figurable=atomic, so unchanged behavior).

- [ ] **Step 5: Update the article + commit**

In `orchestration-workflow.md`, one sentence: the assembler embeds any node's figure inline and shows "Figure pending" for a figurable node still missing its figure (non-figurable nodes are caption-only). Append a `knowledge/log.md` line.

```bash
git add scripts/ knowledge/
git commit -m "feat(assemble): pending notice keys off mechanism_figurable"
```

---

## Task 7: Acceptance — reset + re-run TCP (CONTROLLER-RUN)

**Controller-run** (invokes the Workflow tool). This closes the loop on the topic that motivated Phase 5.

- [ ] **Step 1: One-time reset of the two stale entries**

```bash
cd /Users/kunlu/Projects/gelileo/dummies_notes
rm -rf registry/tcp-connection-lifecycle registry/best-effort-delivery
rm -rf output/tcp-connection-lifecycle
scripts/concept-registry index
scripts/concept-registry lookup communication-protocol   # confirm still illustrated
scripts/concept-registry lookup data-packets             # confirm still illustrated
```
Expected: the two TCP entries are gone from `registry/index.json`; `communication-protocol` and `data-packets` remain `illustrated` (they prove reuse on the re-run).

- [ ] **Step 2: Re-run the workflow** (controller): `Workflow {scriptPath: ".claude/workflows/dummies-notes.js", args: {topic: "TCP connection lifecycle", maxDepth: 2}}`. Expected return: `chain_review_pass` ideally true, or with materially fewer/different gaps; `illustrated` includes `best-effort-delivery` and `tcp-connection-lifecycle`; `communication-protocol`/`data-packets` NOT re-illustrated (covered-link-stop). If the run errors or returns flagged figures, READ the artifacts, diagnose, fix-and-rerun (resume via `resumeFromRunId` if a script edit is needed).

- [ ] **Step 3: Verify the artifacts**

```bash
python3 scripts/graph_check.py output/tcp-connection-lifecycle/graph --require-illustrated
for s in tcp-connection-lifecycle best-effort-delivery; do
  python3 .claude/skills/concept-illustrator/scripts/render.py registry/$s/figure | tail -1
done
python3 -c "import json;e=json.load(open('registry/tcp-connection-lifecycle/entry.json'));print('root:',e['status'],e['prerequisites'])"
python3 -c "import json;c=json.load(open('output/tcp-connection-lifecycle/chain-review.json'));print('chain pass:',c['pass'],'gaps:',len(c['gaps']))"
python3 -m unittest discover -s scripts/tests -p 'test_*.py'
```
Expected: graph check `OK ... --require-illustrated` clean; both figures lint clean; root illustrated with its 3 prerequisite edges; chain review pass=true or with the original "broken arc / unmet prerequisite / handshake leap" gaps closed; scripts suite green. Open `output/tcp-connection-lifecycle/index.html` and confirm: best-effort-delivery now has a figure inline; the TCP section shows a self-sufficient lifecycle figure (not a parts-convergence diagram); communication-protocol/data-packets are reused.

- [ ] **Step 4: Commit the run** (registry/** mapped → touch `atomic-illustration-catalog.md`)

Update `atomic-illustration-catalog.md` (best-effort-delivery now illustrated; tcp root now a self-sufficient mechanism figure) and append a `knowledge/log.md` entry recording the re-run and the chain-review outcome (honestly, whatever it is). Then:

```bash
git add output/ registry/ knowledge/
git commit -m "feat(run): TCP re-run with mechanism figures — closes the Phase 5 loop

best-effort-delivery and the TCP lifecycle now get self-sufficient figures;
packets/protocol reused; chain review <outcome>."
```

---

## Task 8: Finalize the knowledge base

**Model: sonnet.** **Files:** Modify `knowledge/concepts/dummies-notes/{concept-decomposition,illustration-engine,orchestration-workflow}.md`, `knowledge/index.md`, `knowledge/log.md`, `CLAUDE.md`.

- [ ] **Step 1:** Confirm all three articles read accurately for the shipped Phase 5: `concept-decomposition.md` (two-axis: atomic = stop, mechanism_figurable = draw); `illustration-engine.md` (self-sufficiency rule, commentary go-deeper refs, compose retired); `orchestration-workflow.md` (illustrate figurable nodes, no compose step, figurable coverage gate, TCP re-run record). Fix any residual stale wording (e.g. lingering compose-from-children mentions). All `status: mature`, `updated: 2026-06-10`.
- [ ] **Step 2:** `CLAUDE.md`: update the "Known open items" line — composition is retired; figures are self-sufficient; the one remaining open item is figure invalidation/versioning (re-running to pick up new/changed figures needs a manual reset, as Phase 5's acceptance showed).
- [ ] **Step 3:** `knowledge/index.md` rows refreshed if wording changed; append a `knowledge/log.md` compile entry for Phase 5.
- [ ] **Step 4:** Verify + commit:

```bash
python3 scripts/validate-articles
python3 -m unittest discover -s scripts/tests -p 'test_*.py'
git add knowledge/ CLAUDE.md
git commit -m "docs: Phase 5 shipped — self-sufficient figures, composition retired"
```

---

## Definition of done (Phase 5)

- `decomposition.json` carries required `mechanism_figurable`; validator enforces it; goldens + decompose SKILL.md set/explain it.
- Illustrator SKILL.md states the self-sufficiency rule + commentary go-deeper refs; compose-from-children is gone (no references remain).
- Workflow illustrates every figurable node and no longer composes a root figure; `graph_check --require-illustrated` and `assemble.py` key off `mechanism_figurable`.
- TCP re-run: `best-effort-delivery` and `tcp-connection-lifecycle` have self-sufficient figures, `communication-protocol`/`data-packets` reused, graph check clean, chain-review gaps closed or honestly documented.
- All three suites green; articles valid + mature; CLAUDE.md current.
