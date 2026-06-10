export const meta = {
  name: 'dummies-notes',
  description: 'Decompose a topic into a concept graph, illustrate atomic concepts, review with fresh eyes, and register figures',
  whenToUse: 'args: {topic: string, definition?: string, maxDepth?: number, maxNodes?: number}. Run produces output/<topic>/index.html (bottom-up explainer) + output/<topic>/map.html (concept map).',
  phases: [
    { title: 'Decompose', detail: 'registry-aware BFS, one skill call per node' },
    { title: 'Illustrate', detail: 'runbook-first figure per atomic concept' },
    { title: 'Review', detail: 'blind reader + fidelity critic, two repairs max' },
    { title: 'Finalize', detail: 'register, attach figures, graph check' },
    { title: 'Assemble', detail: 'compose root figure if needed; render index.html + map.html' },
    { title: 'ChainReview', detail: 'fresh-eyes pass over the assembled explainer' },
  ],
}

// args may arrive as a JSON-encoded string depending on the caller — accept both.
let A = args
if (typeof A === 'string') { try { A = JSON.parse(A) } catch (e) { A = { topic: A } } }
const topic = A && A.topic
if (!topic) throw new Error('args.topic is required (e.g. {topic: "modular arithmetic"})')
const MAX_DEPTH = (A && A.maxDepth) || 2
const MAX_NODES = (A && A.maxNodes) || 12
const MAX_REPAIRS = 2
const AUDIENCE = 'a curious adult with no domain background'

const CONCEPT_PROPS = {
  slug: { type: 'string' },
  name: { type: 'string' },
  definition: { type: 'string' },
}
const INDEX_SCHEMA = {
  type: 'object',
  properties: {
    concepts: {
      type: 'array',
      items: {
        type: 'object',
        properties: { ...CONCEPT_PROPS, status: { type: 'string' } },
        required: ['slug', 'status', 'definition'],
      },
    },
  },
  required: ['concepts'],
}
const DECOMP_SCHEMA = {
  type: 'object',
  properties: {
    concept: { type: 'object', properties: CONCEPT_PROPS, required: ['slug', 'name', 'definition'] },
    atomic: { type: 'boolean' },
    atomic_reason: { type: 'string' },
    prerequisites: {
      type: 'array',
      items: {
        type: 'object',
        properties: { ...CONCEPT_PROPS, why: { type: 'string' } },
        required: ['slug', 'name', 'definition', 'why'],
      },
    },
    file: { type: 'string' },
    validator_clean: { type: 'boolean' },
  },
  required: ['concept', 'atomic', 'atomic_reason', 'prerequisites', 'file', 'validator_clean'],
}
const FIGURE_SCHEMA = {
  type: 'object',
  properties: {
    figure_dir: { type: 'string' },
    lint_clean: { type: 'boolean' },
    frames: { type: 'number' },
  },
  required: ['figure_dir', 'lint_clean', 'frames'],
}
const VERDICT_SCHEMA = {
  type: 'object',
  properties: {
    pass: { type: 'boolean' },
    summary: { type: 'string' },
    gaps: { type: 'array', items: { type: 'string' } },
  },
  required: ['pass', 'summary', 'gaps'],
}
const REPORT_SCHEMA = {
  type: 'object',
  properties: {
    registered: { type: 'array', items: { type: 'string' } },
    attached: { type: 'array', items: { type: 'string' } },
    collisions: { type: 'array', items: { type: 'string' } },
    graph_check_clean: { type: 'boolean' },
    graph_check_output: { type: 'string' },
  },
  required: ['registered', 'attached', 'collisions', 'graph_check_clean', 'graph_check_output'],
}

// ---- Phase 1: registry snapshot + BFS decomposition -------------------------
phase('Decompose')

const snapshot = await agent(
  'Run `scripts/concept-registry index` from the repo root, then read registry/index.json. ' +
  'Return every concept as {slug, name, definition, status}. If the registry is empty, return an empty list.',
  { label: 'registry-snapshot', phase: 'Decompose', schema: INDEX_SCHEMA })
const covered = {}
for (const c of (snapshot && snapshot.concepts) || []) covered[c.slug] = c

const nodes = {}      // slug -> {name, definition, atomic, prerequisites:[slug], covered}
const frontier = []   // concepts left undone by caps
let rootSlug = null
let graphDir = null
let queue = [{ slug: null, name: topic, definition: (A && A.definition) || null, depth: 0 }]

while (queue.length) {
  const item = queue.shift()
  if (item.slug && nodes[item.slug]) continue
  const isRoot = rootSlug === null

  // Covered → link & stop (spec). Illustrated prerequisites are done; the root always proceeds.
  if (!isRoot && item.slug && covered[item.slug] && covered[item.slug].status === 'illustrated') {
    nodes[item.slug] = { name: item.name, definition: covered[item.slug].definition, atomic: null, prerequisites: [], covered: true }
    log(`${item.slug}: already illustrated — linked, not re-explained`)
    continue
  }
  // Identity: a registered concept keeps its registry definition verbatim.
  if (item.slug && covered[item.slug]) item.definition = covered[item.slug].definition

  if (!isRoot && item.depth > MAX_DEPTH) {
    frontier.push(item.slug || item.name)
    log(`depth cap ${MAX_DEPTH}: '${item.slug || item.name}' left as frontier`)
    continue
  }
  if (Object.keys(nodes).length >= MAX_NODES) {
    frontier.push(item.slug || item.name, ...queue.map(q => q.slug || q.name))
    log(`node cap ${MAX_NODES}: ${frontier.length} concept(s) left as frontier`)
    break
  }

  const d = await agent(
    'Follow the skill at .claude/skills/concept-decompose/SKILL.md exactly. Decompose ONE concept, one level only.\n' +
    `Concept name: ${item.name}\n` +
    (item.slug ? `Use this slug verbatim: ${item.slug}\n` : '') +
    (item.definition ? `Use this definition verbatim (identity rule): ${item.definition}\n` : '') +
    `Audience: ${AUDIENCE}\n` +
    'Reuse covered identities: read registry/index.json — if this concept or any prerequisite matches a covered slug, reuse its slug AND definition exactly.\n' +
    `Write the decomposition to ${graphDir ? graphDir + '/' : 'output/<your-canonical-slug>/graph/'}<slug>.json (create directories as needed).\n` +
    'Then run: python3 .claude/skills/concept-decompose/scripts/validate_decomposition.py <that file> — fix every ERROR until it prints "OK     clean".\n' +
    'Return the decomposition object plus the file path and validator_clean.',
    { label: `decompose:${item.slug || item.name}`, phase: 'Decompose', schema: DECOMP_SCHEMA })
  if (!d) { frontier.push(item.slug || item.name); log(`decompose agent for '${item.name}' returned nothing — frontier`); continue }
  if (!d.validator_clean) throw new Error(`decomposition for '${item.name}' did not pass its validator`)

  const slug = d.concept.slug
  if (isRoot) { rootSlug = slug; graphDir = `output/${slug}/graph` }
  nodes[slug] = {
    name: d.concept.name,
    definition: d.concept.definition,
    atomic: d.atomic,
    prerequisites: d.prerequisites.map(p => p.slug),
    // full prerequisite objects (incl. why) — the compose-from-children
    // contract labels each child with the essence of its why
    prereqMeta: d.prerequisites.map(p => ({ slug: p.slug, name: p.name, definition: p.definition, why: p.why })),
    covered: false,
  }
  for (const p of d.prerequisites) {
    if (!nodes[p.slug]) queue.push({ slug: p.slug, name: p.name, definition: p.definition, depth: item.depth + 1 })
  }
}
log(`graph: ${Object.keys(nodes).length} node(s) under output/${rootSlug}/graph; frontier: ${frontier.length}`)

// ---- Phases 2+3: illustrate + review, pipelined per atomic concept ----------
phase('Illustrate')

const toIllustrate = Object.entries(nodes)
  .filter(([slug, n]) => !n.covered && n.atomic === true &&
    !(covered[slug] && covered[slug].status === 'illustrated'))
  .map(([slug, n]) => ({ slug, name: n.name, definition: n.definition }))
log(`${toIllustrate.length} atomic concept(s) to illustrate`)

function illustrate(c, critique) {
  return agent(
    'Follow the skill at .claude/skills/concept-illustrator/SKILL.md exactly — runbook-first; read its references (design-system, visual-vocabulary, voice-and-metaphor, figure-json).\n' +
    `Concept slug: ${c.slug}\nName: ${c.name}\nDefinition: ${c.definition}\n` +
    `Write the figure directory to registry/${c.slug}/figure (create it; figure.json + frame-NN.svg).\n` +
    (critique ? 'A fresh-eyes review found gaps in the previous attempt. Revise the runbook FIRST, then redraw from it. The gaps:\n' + critique + '\n' : '') +
    `The figure must validate clean: python3 .claude/skills/concept-illustrator/scripts/render.py registry/${c.slug}/figure\n` +
    'Return figure_dir, lint_clean (true only if the validator printed OK/clean), and the frame count.',
    { label: `illustrate:${c.slug}`, phase: 'Illustrate', schema: FIGURE_SCHEMA })
}

async function review(c) {
  const blind = await agent(
    `You are a blind reader. Read ONLY the frame-*.svg files in registry/${c.slug}/figure — ` +
    'do NOT open figure.json or any other file (it contains answer keys that would unblind you).\n' +
    'In plain words: what does this sequence of pictures teach, step by step? What is confusing or unclear? ' +
    'You have no other context — judge the pictures alone. pass = the pictures alone teach a coherent idea.',
    { label: `blind:${c.slug}`, phase: 'Review', schema: VERDICT_SCHEMA })
  const blindSummary = blind ? blind.summary : 'blind reader unavailable'
  const critic = await agent(
    `You are the fidelity critic for the figure in registry/${c.slug}/figure.\n` +
    `The concept: ${c.name} — ${c.definition}\n` +
    'Follow .claude/skills/concept-illustrator/references/review-protocol.md. Read figure.json (runbook, captions, commentary) and every frame SVG. Check:\n' +
    '1. Runbook drift: does each frame match its runbook exactly (values, colours, pointers, what-changed)?\n' +
    `2. Comprehension: a blind reader (who saw only the SVGs) reported: "${blindSummary}". Does that match the commentary's intent? Divergence is a gap.\n` +
    '3. Commentary quality: simple sentences, faithful to the frames, vivid metaphor.\n' +
    '4. Closure: the final frame shows the end state.\n' +
    `Write your verdict to registry/${c.slug}/figure/review.json as {"pass": <bool>, "summary": "<str>", "gaps": ["..."]} and return the same verdict. pass = no real gaps.`,
    { label: `critic:${c.slug}`, phase: 'Review', schema: VERDICT_SCHEMA })
  return critic || { pass: false, summary: 'critic unavailable', gaps: ['review agent failed'] }
}

const reviewed = await pipeline(
  toIllustrate,
  c => illustrate(c, null).then(f => ({ c, f })),
  async (r) => {
    if (!r || !r.f) return { slug: r ? r.c.slug : 'unknown', pass: false, gaps: ['illustrator failed'] }
    const { c } = r
    let verdict = await review(c)
    let repairs = 0
    while (!verdict.pass && repairs < MAX_REPAIRS) {
      repairs += 1
      log(`${c.slug}: review found ${verdict.gaps.length} gap(s) — repair ${repairs}/${MAX_REPAIRS}`)
      await illustrate(c, verdict.gaps.join('\n'))
      verdict = await review(c)
    }
    if (!verdict.pass) log(`${c.slug}: still failing after ${MAX_REPAIRS} repairs — flagged`)
    return { slug: c.slug, pass: verdict.pass, gaps: verdict.gaps, repairs }
  })

// ---- Phase 4: register everything, attach figures, validate the graph -------
phase('Finalize')

const newNodes = Object.entries(nodes)
  .filter(([, n]) => !n.covered)
  .map(([slug, n]) => ({ slug, name: n.name, definition: n.definition, prerequisites: n.prerequisites }))
const figures = (reviewed || []).filter(Boolean)

const report = await agent(
  `Finalize a dummies-notes run from the repo root. Data:\n` +
  `NODES = ${JSON.stringify(newNodes)}\n` +
  `FIGURES = ${JSON.stringify(figures.map(f => f.slug))}\n` +
  `GRAPH_DIR = output/${rootSlug}/graph\n` +
  'Steps, in order:\n' +
  '1. Register every node in NODES without shell-quoting pitfalls: write NODES to a temp JSON file, then run a short python3 heredoc that does: import sys, json; sys.path.insert(0, "scripts"); import concept_registry as reg; for each node call reg.register("registry", node["slug"], node["name"], node["definition"], node.get("prerequisites") or ()) — catching reg.RegistryError per node and recording collisions. Idempotent re-registration updates prerequisites when provided.\n' +
  '2. For each slug in FIGURES: python3 .claude/skills/concept-illustrator/scripts/render.py registry/<slug>/figure ' +
  '(must be clean), then scripts/concept-registry attach-figure <slug> registry/<slug>/figure.\n' +
  '3. scripts/concept-registry index\n' +
  '4. python3 scripts/graph_check.py output/' + rootSlug + '/graph --require-illustrated — capture its full output.\n' +
  'Return registered (slugs), attached (slugs), collisions, graph_check_clean (exit 0), graph_check_output.',
  { label: 'finalize', phase: 'Finalize', schema: REPORT_SCHEMA })

const flagged = figures.filter(f => !f.pass).map(f => f.slug)
log(`done: ${report && report.registered ? report.registered.length : 0} registered, ` +
  `${report && report.attached ? report.attached.length : 0} attached, ${flagged.length} flagged, ` +
  `graph check ${report && report.graph_check_clean ? 'clean' : 'FAILED'}`)

// ---- Phase 5: assemble the deliverable ---------------------------------------
phase('Assemble')

const ASSEMBLE_SCHEMA = {
  type: 'object',
  properties: {
    index_html: { type: 'string' },
    map_html: { type: 'string' },
    sections: { type: 'number' },
    assemble_clean: { type: 'boolean' },
  },
  required: ['index_html', 'map_html', 'sections', 'assemble_clean'],
}

const rootNode = nodes[rootSlug]
if (rootNode && rootNode.atomic === false) {
  const kids = (rootNode.prereqMeta || rootNode.prerequisites.map(s => ({ slug: s }))).map(k => ({
    slug: k.slug,
    name: k.name || (nodes[k.slug] && nodes[k.slug].name) || k.slug,
    definition: k.definition || (nodes[k.slug] && nodes[k.slug].definition) || '',
    why: k.why || '',
  }))
  await agent(
    'Follow .claude/skills/concept-illustrator/SKILL.md — the "Composition figures (compose-from-children)" mode.\n' +
    `Parent concept: ${rootSlug} (${rootNode.name}) — ${rootNode.definition}\n` +
    `Children: ${JSON.stringify(kids)}\n` +
    `Write a single-frame structural composition figure to registry/${rootSlug}/figure (runbook-first; caption + commentary required).\n` +
    `It must validate clean: python3 .claude/skills/concept-illustrator/scripts/render.py registry/${rootSlug}/figure\n` +
    `Then attach it: scripts/concept-registry attach-figure ${rootSlug} registry/${rootSlug}/figure\n` +
    'Return figure_dir, lint_clean, frames.',
    { label: `compose:${rootSlug}`, phase: 'Assemble', schema: FIGURE_SCHEMA })
}

const assembled = await agent(
  `Run from the repo root: python3 scripts/assemble.py output/${rootSlug}/graph --out output/${rootSlug}\n` +
  'It must exit 0 (prints "OK assembled N section(s) ..."). Return index_html and map_html as the generated file paths, ' +
  'sections = N from the OK line, assemble_clean = (exit code was 0).',
  { label: 'assemble', phase: 'Assemble', schema: ASSEMBLE_SCHEMA })
if (!assembled || !assembled.assemble_clean) throw new Error('assembly failed')

// ---- Phase 6: end-to-end chain review (fresh eyes over the whole artifact) ----
phase('ChainReview')

const chain = await agent(
  `You are the chain reviewer for output/${rootSlug}/index.html. Read it top to bottom ` +
  `as a learner would (it is ordered bottom-up: prerequisites first, the target last), ` +
  `plus the graph files in output/${rootSlug}/graph/.\n` +
  'Report graph-level gaps that per-figure reviews cannot see:\n' +
  '1. Leaps: a section assumes an idea no earlier section taught or linked.\n' +
  '2. Unmet prerequisites: a concept referenced but never illustrated, linked, or honestly stubbed.\n' +
  '3. Broken arc: the chain never actually builds up to the target concept.\n' +
  `Write your verdict to output/${rootSlug}/chain-review.json as {"pass": <bool>, "summary": "<str>", "gaps": ["..."]} and return the same verdict. ` +
  'pass = a curious adult could read this start to finish and understand the target.',
  { label: 'chain-review', phase: 'ChainReview', schema: VERDICT_SCHEMA })
if (chain && !chain.pass) log(`chain review found ${chain.gaps.length} gap(s) — see output/${rootSlug}/chain-review.json`)

return {
  root: rootSlug,
  graph_dir: `output/${rootSlug}/graph`,
  nodes: Object.keys(nodes).length,
  illustrated: figures.filter(f => f.pass).map(f => f.slug),
  flagged,
  frontier,
  collisions: (report && report.collisions) || [],
  graph_check_clean: !!(report && report.graph_check_clean),
  index_html: assembled.index_html,
  map_html: assembled.map_html,
  chain_review_pass: !!(chain && chain.pass),
  chain_gaps: (chain && chain.gaps) || [],
}
