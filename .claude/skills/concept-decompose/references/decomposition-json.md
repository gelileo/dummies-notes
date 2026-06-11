# decomposition.json

The machine-readable output of one `concept-decompose` run: ONE concept, one level down. The skill never recurses — recursion belongs to the dummies-notes Workflow (Phase 3).

## Top-level fields

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `concept` | object | yes | the concept being decomposed (see Concept object) |
| `audience` | string | yes | who this is for; default: "a curious adult with no domain background" |
| `atomic` | bool | yes | the atomicity verdict (see Atomicity) |
| `mechanism_figurable` | bool | yes | can THIS concept's own mechanism be taught self-sufficiently in one figure, regardless of prerequisites? Independent of `atomic`. |
| `atomic_reason` | string | yes | one or two plain sentences justifying the verdict |
| `prerequisites` | array | yes | direct prerequisites, one level only; `[]` when atomic |

## Concept object (used for `concept` and each prerequisite)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `slug` | string | yes | canonical kebab-case identity (registry key) |
| `name` | string | yes | human-readable name |
| `definition` | string | yes | one or two plain sentences; no unexplained jargon |
| `why` | string | prerequisites only | why the parent can't be understood without it |

## Atomicity

A concept is **atomic** when (a) one figure of ≤ ~6 frames explains its mechanism without needing a sub-figure, and (b) its remaining prerequisites are common knowledge for the audience. Non-atomic ⇒ at least one prerequisite. **Jargon is a decomposition signal:** a term the audience wouldn't know must become a prerequisite, never an aside.

## Two axes: atomic vs mechanism_figurable

`atomic` and `mechanism_figurable` are independent. `atomic` answers "should we
stop decomposing?" (are the remaining prerequisites common knowledge).
`mechanism_figurable` answers "is this concept's own mechanism one self-sufficient
figure?" — judged *assuming* the prerequisites are understood elsewhere. A concept
can be non-atomic (it has prerequisites worth their own figures) yet figurable (its
own mechanism is one figure) — e.g. a network protocol's connection lifecycle. Such
a concept gets its own self-sufficient figure AND its prerequisites get theirs.

## Slug rules

Kebab-case (`^[a-z0-9]+(-[a-z0-9]+)*$`). On a meaning collision, qualify the slug (`mean-average` vs `mean-unkind`) — definitions disambiguate.

## Example

This block illustrates the *shape* only. For canonical wording — including the
authoritative definitions for these slugs (identity = slug + definition) — the
`examples/*/decomposition.json` files are the source of truth.

```json
{
  "concept": {
    "slug": "rsa-encryption",
    "name": "RSA encryption",
    "definition": "A way to send secret messages using two keys: a public one anyone can use to lock, and a private one only the owner can use to unlock."
  },
  "audience": "a curious adult with no domain background",
  "atomic": false,
  "atomic_reason": "Understanding RSA needs ideas that each deserve their own picture, like clock-style arithmetic and the two-key idea.",
  "prerequisites": [
    {
      "slug": "modular-arithmetic",
      "name": "Modular arithmetic",
      "definition": "Arithmetic that wraps around at a fixed number, like clock hands wrapping past 12.",
      "why": "RSA's locking and unlocking are both wrap-around calculations."
    }
  ]
}
```
