#!/usr/bin/env python3
"""Generates agent-loop.md from agent_loop.py's output. Run: python3 agents.py"""
import io, subprocess
o = io.StringIO(); W = o.write
out = subprocess.run(['python3', 'agent_loop.py'], capture_output=True, text=True).stdout
def sect(start):
    i = out.index(start); return out[i:].split(chr(10), 1)[1].split('===')[0].rstrip()

W(f"""# The agent loop, traced

Every trace here is produced by `agent_loop.py`. Run `python3 agents.py` to regenerate.

**One honest caveat up front:** the "model" in this script is a scripted rule set standing in for
a language model. That is deliberate. Every mechanism in this chapter — schemas, the loop,
parsing, compounding error, prompt injection, context growth — is a property of the *harness*,
not of the model, and swapping the model for rules lets each be measured exactly. Where a real
model would behave differently, the text says so.

---

## 1. Tools are advertised as schemas

```
{sect('=== 1. tools are advertised')}
```

The runtime describes each tool — name, what it does, what arguments it takes — as JSON, and
that JSON goes into the prompt. A real model has been fine-tuned ([chapter 07](../07-supervised-fine-tuning/))
to emit a call in a fixed format when a tool fits the task. This is also the shape of the Model
Context Protocol: a server advertises tools and schemas; any client can call them; a system is
integrated once rather than once per AI product.

**The description is prompt engineering.** A vague description gets a tool called at the wrong
times; a precise one is most of what makes tool use work.

---

## 2. The loop

```
{sect('=== 2. the loop')}
```

Observe → decide → act → observe. The model emits a call; the runtime executes it and appends the
result to the conversation; the model sees the result and decides again. Five steps for a task
that needed three lookups and one calculation. **The model never runs anything** — it writes a
request, and a program the user controls decides whether and how to honour it.

Every coding agent, browsing agent and computer-use agent is this loop, plus a tool set and a
system prompt.

---

## 3. The call must parse

```
{sect('=== 3. the call must parse')}
```

A model emitting free text will eventually emit almost-JSON. Constrained decoding
([chapter 10](../10-inference-and-decoding/)) sets the logits of every grammar-illegal token to
`−∞`, so the call *cannot* fail to parse — the runtime can then trust its structure and validate
only its content. → [essentials: state machines](essentials/state-machines-and-grammars/)

---

## 4. Compounding error, and what the loop can see

```
{sect('=== 4. compounding error')}
```

This table is the chapter's central measurement. **A mistake the loop can observe is nearly
free** — a wrong lookup returns "not found", the model sees it and retries, and a 90%-reliable
step still completes 99.6% of tasks. **A mistake that looks fine compounds as `pᵏ`** — a confident
wrong answer, a plausible wrong file edit — and 90% per step loses most five-step tasks.

The value of the loop is exactly the errors it can see. Design tools so mistakes surface: return
errors, run the tests, show the diff. → [chapter 09's compounding](../09-reasoning-training/essentials/compounding-probabilities/)

---

## 5. Prompt injection through a tool result

```
{sect('=== 5. prompt injection')}
```

The wiki entry the agent looked up contained text shaped like an instruction. The naive agent,
which treats whatever appears in its context as something to obey, calls `delete_file` — and keeps
calling it until the step budget runs out. The careful agent treats tool output as **data**: the
same discipline as any input handling.

Two defences, and you need both. First, the model: trained to distinguish the user's instructions
from content it retrieved. Second — because no model is perfectly reliable — the runtime:
irreversible tools sandboxed and gated behind confirmation, regardless of what the model
"decides". The injected text arrived through a channel the user does not control; that is the
threat model for every agent that reads the web.

---

## 6. Context grows every step

```
{sect('=== 6. context grows')}
```

Each step re-reads the entire history — schemas, every call, every result. After a hundred steps
the context is sixteen thousand tokens and eight hundred thousand have been processed in total.
Prefix caching ([chapter 10](../10-inference-and-decoding/)) removes the recomputation but not the
attention cost or the window limit. Long sessions **must** summarise or truncate old tool results,
and deciding what to keep is [chapter 12](../12-context-and-knowledge/)'s problem inside the loop.

---

## 7. Training for agency, briefly

SFT on trajectories teaches the format. RL where **the environment is the reward** —
tests pass, task verified — is [chapter 09](../09-reasoning-training/) with tools in the loop:
sample a trajectory, check the outcome, reinforce. Long-horizon RL is the current frontier
precisely because of section 4: credit has to travel back across many steps, and the
unrecoverable errors are the ones that matter.

---

## 8. Evaluating an agent

```
{sect('=== 7. evaluating')}
```

Task success over many tasks *and* many runs (variance is high), cost per task, steps per task,
and the rate of irreversible actions. SWE-bench-style evaluations do this for coding.
→ [chapter 15](../15-evaluation/)

---

## 9. Invariants

1. **The model writes requests; the runtime executes them.** Tool use is a convention, not a capability.
2. **Schemas are prompt engineering.** The description decides when a tool gets called.
3. **Constrained decoding makes calls parse.** Validate content, not structure.
4. **Recoverable errors are cheap; invisible ones compound.** Design tools so mistakes surface.
5. **Tool output is untrusted input.** Gate irreversible actions in the runtime, whatever the model decides.
6. **Context grows every step.** Summarise, or drown.
7. **What is learned vs what is scaffolding** — know which is which for any agent behaviour you see.
""")
open('agent-loop.md', 'w').write(o.getvalue())
print("wrote agent-loop.md", len(o.getvalue()), "chars")
