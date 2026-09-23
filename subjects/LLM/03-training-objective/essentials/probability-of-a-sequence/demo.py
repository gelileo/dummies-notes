#!/usr/bin/env python3
"""Conditional probability and the chain rule: why a language model predicts
one token at a time. Run: python3 demo.py"""
import math

# a tiny world: what follows what, as probabilities we simply declare
p_first = {"the": 0.6, "a": 0.4}
p_next  = {("the",): {"cat": 0.5, "dog": 0.5},
           ("a",):   {"cat": 0.3, "dog": 0.7},
           ("the","cat"): {"sat": 0.8, "ran": 0.2}, ("the","dog"): {"sat": 0.4, "ran": 0.6},
           ("a","cat"):   {"sat": 0.9, "ran": 0.1}, ("a","dog"):   {"sat": 0.5, "ran": 0.5}}

print("=== conditional probability: p(B | A) = 'probability of B, given A happened' ===")
print(f"   p(cat | the) = {p_next[('the',)]['cat']}      p(cat | a) = {p_next[('a',)]['cat']}")
print("   Same word, different probability, because the context differs.")

print("\n=== the chain rule: a whole sequence is a product of one-step conditionals ===")
seq = ["the", "cat", "sat"]
p1 = p_first[seq[0]]
p2 = p_next[(seq[0],)][seq[1]]
p3 = p_next[(seq[0], seq[1])][seq[2]]
print(f"   p({' '.join(seq)})")
print(f"     = p({seq[0]}) * p({seq[1]} | {seq[0]}) * p({seq[2]} | {seq[0]} {seq[1]})")
print(f"     = {p1} * {p2} * {p3}")
print(f"     = {p1*p2*p3:.3f}")
print("   Every step conditions on EVERYTHING before it. Nothing is assumed independent.")

print("\n=== this is exactly what a language model computes ===")
print("   forward pass at position t returns p(token_t | tokens_<t) -- one factor.")
print("   the loss adds up -log of each factor (see logarithms-and-bits):")
tot = 0
for name, p in (("p(the)", p1), ("p(cat|the)", p2), ("p(sat|the cat)", p3)):
    tot += -math.log(p)
    print(f"   {name:<18} = {p:<5}  -> -log = {-math.log(p):.3f}")
print(f"   sum = {tot:.3f} = -log p(sequence) = -log({p1*p2*p3:.3f}) = {-math.log(p1*p2*p3):.3f}  (same thing)")

print("\n=== all sequences' probabilities add to 1 ===")
total = 0
for w1, q1 in p_first.items():
    for w2, q2 in p_next[(w1,)].items():
        for w3, q3 in p_next[(w1, w2)].items():
            total += q1*q2*q3
print(f"   sum over all 8 possible three-word sequences = {total:.3f}")
print("   Because every conditional sums to 1, the product does too. A language")
print("   model is a probability distribution over ALL possible texts.")

print("\n=== independence is the special case where context does not matter ===")
print("   if p(cat | the) == p(cat | a) == p(cat), the words are independent and")
print("   the chain rule collapses to p(w1)*p(w2)*p(w3) -- a 'bag of words'.")
print("   Real language is nothing like that, which is the whole point of context.")
