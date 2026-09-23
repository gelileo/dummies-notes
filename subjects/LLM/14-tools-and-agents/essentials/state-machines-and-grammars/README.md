# Essential · State machines and grammars

**Needed for:** *"constrained decoding"*, *"the call must parse"*, *"JSON mode"* in
[chapter 14](../../README.md) and [chapter 10](../../../10-inference-and-decoding/).

## A grammar as states and allowed next tokens

```
   start   -> ['{']
   key?    -> ['"k"', '}']
   colon   -> [':']
   value   -> ['"v"', '1', 'true', '{']
   after   -> [',', '}']
   key     -> ['"k"']
   done    -> END
```

A **finite-state machine** is a set of states and, for each, the tokens that may come next and
where they lead. This one accepts a tiny JSON object. Reading a valid string walks it from `start`
to `done`; an invalid string has nowhere to go.

## Most of the vocabulary is illegal at any moment

```
   in state start  : legal ['{']                            illegal 11 of 12
   in state colon  : legal [':']                            illegal 11 of 12
   in state value  : legal ['"v"', '1', 'true', '{']        illegal 8 of 12
   in state after  : legal [',', '}']                       illegal 10 of 12
```

## Choose only among legal tokens and every output is valid

```
   {"k":1}                                            valid JSON: True
   {"k":1}                                            valid JSON: True
   {"k":{"k":{}}}                                     valid JSON: True
   {"k":true,"k":true}                                valid JSON: True
   {"k":1}                                            valid JSON: True
```

Random choices — no intelligence at all — produce valid JSON every time, because the machine only
ever offers legal moves.

## The same machine as a logit mask

```
   at each decoding step: legal(state) -> mask; logits[illegal] = -inf; softmax; sample; advance state.
   the model still chooses -- but only among tokens the grammar permits. 'banana' can never appear.
   this is constrained decoding (chapter 10). JSON schema -> grammar -> state machine -> mask.
```

At each decoding step: ask the machine what is legal, set every other token's logit to `−∞`
([softmax](../../../02-transformer-forward-pass/essentials/softmax-and-probability/) gives them
exactly zero), sample, advance the state. The model still chooses — but only among tokens the
grammar permits. `banana` can never appear in a tool call.

## Why an automaton is the right tool

```
   regular expressions and JSON schemas compile to finite automata. an automaton answers 'what may
   come next?' in constant time per step, which is exactly the question decoding asks. real
   tokenizers complicate it (one token can span several grammar symbols), but the idea is this.
```

## Run it

```bash
python3 demo.py
```

## Terms

| Term | Meaning |
| --- | --- |
| **grammar** | The rules for which strings are valid. JSON has one; so does every tool-call format. |
| **finite-state machine (FSM / automaton)** | States plus transitions on tokens. Answers "what may come next?" in constant time. |
| **state** | Where you are in the grammar after the tokens so far. |
| **transition** | A legal next token and the state it leads to. |
| **accepting state** | A state where the string so far is complete and valid. |
| **logit mask** | Setting forbidden tokens to `−∞` before softmax. |
| **constrained / structured decoding** | Sampling only among grammar-legal tokens. Guarantees the output parses. |
| **JSON schema → grammar** | Compiling a schema into the automaton that enforces it. |
