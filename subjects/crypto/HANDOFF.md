# Handoff — Illustrate the Crypto & Network-Security study guide with `dummies-notes`

**For a fresh session.** Goal: use the `dummies-notes` workflow/skills built in this repo to produce intuitive **illustrations** for the topics in `subjects/crypto/crypto-netsec-study-guide.md` (Tiers 0–6, ~55 topics). This doc is a self-contained kickoff brief — you shouldn't need the prior conversation.

## First action (what to do in the new session)

Don't start running yet — **plan first**. Use `superpowers:brainstorming` → `superpowers:writing-plans` to decide scope, ordering, and per-topic settings (see "Planning decisions" below), then execute foundations-first. The work is a *sequence of `dummies-notes` workflow runs*, not new code.

## The input

`subjects/crypto/crypto-netsec-study-guide.md` — a tiered curriculum, each topic already paired with a one-line "draw-a-picture" metaphor (these are ready-made `definition` strings for the workflow):

- **Tier 0 — Mathematical Foundations**: modular arithmetic, GCD/Euclid, primes & primality, modular exponentiation & discrete log, groups/rings/finite fields (GF(2ⁿ)), entropy/information theory, one-way functions.
- **Tier 1 — Classical / Historical**: Caesar & substitution, Vigenère, frequency analysis, one-time pad & perfect secrecy, Kerckhoffs's principle, Enigma.
- **Tier 2 — Symmetric-Key**: stream vs block ciphers, Feistel networks, DES/3DES, AES (Rijndael), modes of operation + the ECB penguin, ChaCha20, padding-oracle attacks.
- **Tier 3 — Integrity/Hashing/Auth**: hash functions, avalanche effect, collisions (MD5/SHA-1 death), Merkle–Damgård & length-extension, MACs/HMAC, AEAD, Merkle trees, password hashing & salt.
- **Tier 4 — Public-Key**: key-distribution problem, Diffie–Hellman, RSA, ECC, digital signatures & non-repudiation, PKI & certificates, forward secrecy.
- **Tier 5 — Protocols & Network Security**: CIA triad, threat modeling, TLS/SSL handshake, OSI/TCP-IP model, MITM, ARP/DNS spoofing, VPN/IPsec, firewalls/NAT/IDS/IPS, OWASP Top 10, OAuth/JWT/Kerberos, DNSSEC/HTTPS/HSTS/CT.
- **Tier 6 — Advanced & Modern Frontiers**: zero-knowledge proofs, homomorphic encryption, secure multiparty computation, Shamir's secret sharing, the quantum threat & Shor's algorithm, post-quantum (lattice) crypto, quantum key distribution (BB84), blockchain primitives in concert.

## The tool (already built, shipped, tested on `main`)

The `dummies-notes` Workflow + three skills + a registry. One run, given a topic:
1. **Decompose** (registry-aware BFS) — break the topic into a prerequisite concept graph.
2. **Illustrate** — every *figurable* node gets a **self-sufficient** SVG figure (light/dark, one archetype, frame-consistent; multi-frame slideshows for processes). Each figure teaches its own concept standalone; commentary adds "go deeper" pointers to prerequisite figures.
3. **Review** — blind-reader + fidelity critic, ≤2 repairs.
4. **Finalize** — register concepts, attach figures, `graph_check`.
5. **Assemble** — `output/<topic>/index.html` (bottom-up explainer, prerequisites first) + `map.html` (concept map with thumbnails) + `chain-review.json`.
6. **(opt) Video** — `makeVideo:true` builds `output/<topic>/video/` (narrated animated slideshow; `videoFormat` html|mp4|both; `tts` say|kokoro|neutts).

**Reuse is the point**: figures are content-addressed in `registry/`. A concept that appears in many chains is **drawn once and referenced everywhere**. Crypto topics share heavy prerequisites (modular arithmetic, primes, hashing, keys), so *ordering runs to build shared foundations first* avoids redrawing them.

### Already in the registry (REUSE these — don't redraw)
`modular-arithmetic`, `prime-numbers`, `asymmetric-cryptography`, `rsa-encryption` are already illustrated (from earlier dev), plus networking concepts (`tcp-connection-lifecycle`, `data-packets`, `communication-protocol`, `unreliable-delivery`, `delivery-acknowledgement`) and `quicksort`. So Tier 0 (modular arithmetic, primes) and Tier 4 (RSA, asymmetric crypto) have a head start; later runs that decompose onto them will link rather than re-illustrate.

## How to invoke a run

Via the **Workflow tool**. The workflow is `dummies-notes`; invoke by scriptPath (most reliable across sessions):
```
Workflow({ scriptPath: ".claude/workflows/dummies-notes.js",
           args: { topic: "AES (Rijndael)",
                   definition: "<paste the one-liner from the study guide>",
                   maxDepth: 2, maxNodes: 12 } })
```
- `topic` (required), `definition?` (use the guide's metaphor sentence — it steers decomposition + illustration), `maxDepth?` (default 2), `maxNodes?` (default 12), `makeVideo?`/`videoFormat?`/`tts?` (default off / html / say).
- Output lands at `output/<slug>/index.html` + `map.html` + `chain-review.json`. Open `index.html` to review.
- A run spawns ~16 subagents and takes minutes — **run topics one at a time**, review the chain-review, then proceed. (Don't fan out dozens of workflow runs blindly; it's expensive.)

## Planning decisions to make (this is what to brainstorm)

1. **Scope & batching**: all ~55 topics, or tier-by-tier? Recommend tiers in order (0→6); within a tier, batch a handful, review, continue.
2. **Foundations-first ordering** (key efficiency lever): run Tier 0 math concepts *before* Tiers 2/4 so RSA/DH/AES decompose onto already-registered prerequisites instead of re-illustrating them.
3. **Topic granularity vs. auto-decomposition**: the workflow auto-pulls prerequisites, so you usually feed the *headline* topic and let decomposition + the registry handle shared sub-concepts — feeding every single study-guide line risks duplicate work. Decide which entries are "headline topics" vs. prerequisites that will be covered automatically.
4. **`maxDepth`/`maxNodes` per topic**: defaults (2/12) suit most; bump for sprawling ones (TLS, OWASP), lower for atomic ones (Caesar cipher).
5. **Deliverable**: figures + concept map (HTML) is the target for a study guide. Video/TTS is optional and much heavier — defer unless you want narrated lessons (TTS setup is in `docs/tts-and-ffmpeg-notes.md`).
6. **A combined index**: consider, after per-topic runs, a small step to link all `output/<topic>/index.html` pages into one crypto study-guide landing page (mirrors the study guide's tiers). Not built yet — a nice optional finisher.

## Gotchas / constraints

- **No figure invalidation yet**: re-running a topic to pick up changed/new figures needs a manual reset — `rm -rf output/<slug>` and remove/relevant `registry/<slug>` entries — or it reuses the cached figure. Plan ordering to avoid needing re-runs.
- **Cost/time**: ~16 agents per run. Sequence, don't blast in parallel.
- **`chain-review.json`** is the honesty check per topic — read it; `pass:false` lists graph-level gaps (missing prerequisite, leap, broken arc) to address (often by running a prerequisite topic first).
- **Style/quality bar** lives in `.claude/skills/concept-illustrator/references/` + the golden `examples/quicksort/` and `examples/tcp-handshake-reveal/`. The methodology + living-doc rules are in `CLAUDE.md`; concept docs in `knowledge/concepts/dummies-notes/`.

## Repo state
On `main`, all phases shipped + pushed (`github.com/gelileo/dummies-notes`). Test suites green:
`python3 -m unittest discover -s scripts/tests -p 'test_*.py'` (+ the two skill test dirs). The study guide (this folder) is the task input; this `HANDOFF.md` is the brief.

## Suggested opening line for the new session
> "Read `subjects/crypto/HANDOFF.md` and `subjects/crypto/crypto-netsec-study-guide.md`, then plan illustrating the crypto curriculum with the dummies-notes workflow — foundations (Tier 0) first, reusing the registry. Brainstorm scope/ordering before running anything."
