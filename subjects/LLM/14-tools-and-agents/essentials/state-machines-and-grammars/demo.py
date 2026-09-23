#!/usr/bin/env python3
"""A grammar as a state machine, and why masking logits with one guarantees valid output.
Run: python3 demo.py"""
import random
random.seed(0)

# a tiny JSON-object grammar as a finite-state machine: state -> {token: next_state}
FSM = {
    "start":     {"{": "key?"},
    "key?":      {'"k"': "colon", "}": "done"},
    "colon":     {":": "value"},
    "value":     {'"v"': "after", "1": "after", "true": "after", "{": "key?"},   # nested object allowed
    "after":     {",": "key",  "}": "done"},
    "key":       {'"k"': "colon"},
    "done":      {},
}
VOCAB = ["{", "}", ":", ",", '"k"', '"v"', "1", "true", "banana", "]", "(", "null"]

print("=== a grammar is a set of states and the tokens allowed from each ===")
for st, edges in FSM.items():
    print(f"   {st:<7} -> {list(edges) if edges else 'END'}")

print("\n=== from any state, most of the vocabulary is illegal ===")
for st in ("start", "colon", "value", "after"):
    legal = set(FSM[st]); print(f"   in state {st:<7}: legal {str(sorted(legal)):<32} illegal {len(VOCAB) - len(legal)} of {len(VOCAB)}")

print("\n=== random choices among LEGAL tokens only: every output parses ===")
def walk(max_depth=3):
    stack, st, out = [], "start", []
    for _ in range(40):
        if st == "done" and not stack: break
        choices = list(FSM[st])
        if st == "value" and len(stack) >= max_depth: choices.remove("{")
        # weight the walk toward content: close the object only 1 time in 4 when a key is possible
        weights = [0.25 if (c == "}" and '"k"' in choices) else 1.0 for c in choices]
        tok = random.choices(choices, weights)[0]; out.append(tok)
        if tok == "{" and st != "start": stack.append("after"); st = "key?"; continue
        st = FSM[st][tok]
        if st == "done" and stack: st = stack.pop()
    return "".join(out)
import json
for _ in range(5):
    s = walk(); ok = True
    try: json.loads(s)
    except Exception: ok = False
    print(f"   {s:<50} valid JSON: {ok}")

print("\n=== the same machine as a logit mask ===")
print("   at each decoding step: legal(state) -> mask; logits[illegal] = -inf; softmax; sample; advance state.")
print("   the model still chooses -- but only among tokens the grammar permits. 'banana' can never appear.")
print("   this is constrained decoding (chapter 10). JSON schema -> grammar -> state machine -> mask.")

print("\n=== why this is the right tool ===")
print("   regular expressions and JSON schemas compile to finite automata. an automaton answers 'what may")
print("   come next?' in constant time per step, which is exactly the question decoding asks. real")
print("   tokenizers complicate it (one token can span several grammar symbols), but the idea is this.")
