#!/usr/bin/env python3
"""Vectors, dot products, cosine similarity. Run: python3 vectors_demo.py"""
import math
dot = lambda a, b: sum(x*y for x, y in zip(a, b))
length = lambda v: math.sqrt(dot(v, v))
cosine = lambda a, b: dot(a, b) / (length(a)*length(b))

print("=== the dot product tracks the angle between two directions ===")
print(f"   {'angle':>7}{'a . b':>9}{'cosine':>9}   meaning")
for deg, meaning in [(0,"same direction"), (30,""), (60,""), (90,"perpendicular - unrelated"),
                     (120,""), (180,"opposite")]:
    r = math.radians(deg); a = [1, 0]; b = [math.cos(r), math.sin(r)]
    print(f"   {deg:>5}°{dot(a,b):>9.3f}{cosine(a,b):>9.3f}   {meaning}")

print("   Every value above is just cos(angle). Here is why:")
print("   a is fixed at [1, 0]; b is built as [cos(angle), sin(angle)], so")
print("   a . b = 1*cos + 0*sin = cos(angle). The second term is always zeroed out.")
print(f"   {'angle':>7}{'b = [cos, sin]':>24}{'a . b term by term':>34}")
for deg in (0, 30, 60, 90, 120, 180):
    r = math.radians(deg); b = [math.cos(r), math.sin(r)]
    print(f"   {deg:>5}°   [{b[0]:>7.3f}, {b[1]:>7.3f}]"
          f"      1*{b[0]:>7.3f} + 0*{b[1]:>7.3f} = {dot([1,0],b):>7.3f}")

print("\n=== the identity underneath: a . b = |a| * |b| * cos(angle) ===")
c30, s30 = math.cos(math.radians(30)), math.sin(math.radians(30))
print(f"   {'vectors':>34}{'a . b':>9}{'cosine':>9}{'equal?':>9}   note")
for a2, b2, note in ([[1,0], [c30,s30], 'both length 1'],
                     [[3,0], [c30,s30], 'a is 3x longer'],
                     [[3,0], [10*c30,10*s30], 'both longer']):
    d, k = dot(a2,b2), cosine(a2,b2)
    lab = f"[{a2[0]:g},{a2[1]:g}] . [{b2[0]:.3f},{b2[1]:.3f}]"
    print(f"   {lab:>34}{d:>9.3f}{k:>9.3f}{'yes' if abs(d-k) < 1e-9 else 'no':>9}   {note}")
print("   The angle is 30° in all three rows. Only the cosine column knows that.")

print("\n=== length vs direction ===")
a, b, c = [3, 4], [6, 8], [4, 3]
for name, v in [("a = [3,4]", a), ("b = [6,8]  (a doubled)", b), ("c = [4,3]", c)]:
    print(f"   {name:<24} length {length(v):.2f}")
print(f"   a.b = {dot(a,b):.1f} but cosine(a,b) = {cosine(a,b):.3f}  -> same direction, different size")
print(f"   a.c = {dot(a,c):.1f} and cosine(a,c) = {cosine(a,c):.3f}  -> same size, different direction")

print("\n=== a dot product is one line of code ===")
print("   dot(a, b) = sum(x*y for x, y in zip(a, b))")
print(f"   dot([1,2,3], [4,5,6]) = 1*4 + 2*5 + 3*6 = {dot([1,2,3],[4,5,6])}")
