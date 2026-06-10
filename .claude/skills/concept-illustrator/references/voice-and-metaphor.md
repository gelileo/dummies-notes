# Voice and metaphor

The style system keeps visuals consistent; voice and metaphor keep the *writing*
consistent. Read this before writing captions or labels.

---

## Voice

Write like a **knowledgeable friend** explaining over coffee — not a textbook, not a
lecture, not documentation.

**Concrete over abstract.** "Binary search cuts the remaining candidates in half each
step" beats "Binary search runs in O(log n) time." The abstract follows from the
concrete; never lead with abstraction.

**Short.** A caption is one or two sentences. A label is two to five words. A figure
that needs a paragraph to make sense has failed — recompose it.

**Metaphor first.** Lead with the spatial metaphor, then add precision. "Think of the
call stack as a pile of plates — you always add and remove from the top, never the
middle" gives the reader a handle before you name the mechanism.

**No jargon without decomposition.** If a term is not common knowledge for a curious
adult with no domain background, do not assume it. Break it out as its own
prerequisite node. A caption that reads "the amortized cost is O(1)" without
explaining amortization is a broken prerequisite, not a concise caption.

**Sentence case everywhere.** Labels, captions, titles — all sentence case. The
linter enforces this; the voice guide repeats it because it matters for tone too.
Title Case reads formal and distancing; sentence case reads conversational.

**One caption per frame.** In a sequence (multi-frame) figure, write **one caption per frame** — each advances the story. A caption says what is happening and why; it does not restate what the picture already shows.

---

## Metaphor bank

Concrete mappings from abstract concepts to physical/spatial metaphors. When
illustrating a concept in this list, start here — these metaphors are proven.
When the concept is not listed, invent a spatial metaphor that makes the mechanism
*visible* and add it.

| Concept | Metaphor |
|---------|----------|
| Recursion | Nested Russian dolls — each doll contains a smaller version of the same shape, down to the one that can't be opened further (the base case) |
| Call stack | A pile of plates — you always add (push) and remove (pop) from the top; the plate at the bottom is the first call, never touched until everything above it is done |
| Hash map | Keys dropped into labeled mailboxes — the hash function is the postal rule that decides which box a key belongs in |
| Pointer / reference | A finger marking a spot in a book — the finger is not the page, it's just pointing at it; move the finger without copying the page |
| Binary search | A shrinking window on a sorted row — each comparison cuts the remaining candidates in half |
| Quicksort pivot | A dividing wall — smaller items end up on the left, larger on the right; the wall is then in its final position forever |
| Linked list | A treasure hunt — each clue (node) tells you where the next clue is; there is no shortcut to clue 5, you must follow the chain |
| Tree traversal | Exploring a cave system — depth-first means you follow one tunnel to its end before backtracking; breadth-first means you walk one step into each tunnel before going deeper |
| Heap | A tournament bracket where the winner (min or max) is always at the root — inserting rebalances the bracket |
| Sorting stability | Two identical playing cards — a stable sort keeps them in their original left-to-right order; an unstable sort may swap them arbitrarily |
| Cache / memoization | A sticky note on your desk — instead of re-deriving the result, you check the sticky note first |
| Graph BFS | Ripples in a pond — the starting node is where the stone drops; nodes are reached in order of distance from the source |
| Mutual exclusion (lock) | A single key to a restroom — whoever holds the key is inside; everyone else waits outside |
| Event loop | A single cashier with a to-do list — tasks are queued; the cashier handles one at a time and never walks away mid-task |
| Gradient descent | A ball rolling down a hilly surface toward the lowest valley — each step follows the steepest downhill direction |
| Modular arithmetic | A clock face — after reaching 12, you wrap back to 1; 14 o'clock is just 2 o'clock |
| Public-key encryption | A padlock anyone can close (public key) but only the keyholder can open (private key) |
| Overflow / wrap-around | An odometer rolling past 999 back to 000 — the number wraps because there are no more digits |

## Commentary

Commentary is the per-frame narration in `figure.json` (`frames[].commentary`). It
is longer than the one-line `caption` — a short narration paragraph — meant to be
read aloud for slides and video. It is not shown in the HTML viewer.

- **Prefer simple sentences.** One idea per sentence. Avoid nested clauses and
  compound-complex sentences. Short sentences, plain words.
- **Vibrant through metaphor and rhythm, not length.** Engagement comes from a
  vivid image and good cadence, never from a long sentence.
- **No unexplained jargon.** An obscure term is a prerequisite to illustrate, not
  an aside to drop.
- **Faithful to the frame.** Narrate what this frame actually shows.
- **Transcript-ready.** It should read naturally when spoken.

Example (a quicksort partition frame):

> Now the real work starts. We walk left to right. The pivot is our yardstick.
> Every value smaller than it slides into a growing zone on the left.
