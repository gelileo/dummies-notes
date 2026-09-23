#!/usr/bin/env python3
"""Rotation, and how RoPE turns position into an angle. Run: python3 rotation_demo.py"""
import math
def rotate(x, y, angle):
    c, s = math.cos(angle), math.sin(angle)
    return x*c - y*s, x*s + y*c

print("=== rotating a point, using nothing but sin and cos ===")
print(f"   {'angle':>7}{'point':>22}")
for deg in (0, 45, 90, 180, 270):
    x, y = rotate(1.0, 0.0, math.radians(deg))
    print(f"   {deg:>5}°   ({x:>6.3f}, {y:>6.3f})")

print("\n=== rotation preserves length - it turns, it does not stretch ===")
for deg in (0, 37, 90, 211):
    x, y = rotate(3.0, 4.0, math.radians(deg))
    print(f"   {deg:>5}°   ({x:>6.2f}, {y:>6.2f})   length {math.sqrt(x*x+y*y):.3f}")

print("\n=== the property RoPE is built on ===")
print("   rotate BOTH vectors by the same amount and their dot product is unchanged;")
print("   rotate them by DIFFERENT amounts and it depends only on the difference.")
a, b = (1.0, 0.0), (0.8, 0.6)
for pa, pb in ((0,0), (1,1), (5,5), (0,1), (0,2), (3,5)):
    ra = rotate(*a, pa*0.5); rb = rotate(*b, pb*0.5)
    print(f"   positions ({pa},{pb})  gap {pb-pa:>2}   dot = {ra[0]*rb[0]+ra[1]*rb[1]:>7.4f}")
print("   Same gap -> same dot product, wherever the pair sits in the sequence.")
print("   That is relative position, for free.")

print("\n=== RoPE uses many speeds at once ===")
print(f"   {'d_head':>8}{'pairs':>8}{'fastest rad/pos':>18}{'slowest rad/pos':>18}")
for d in (4, 64, 128):
    th = [1/(10000**(i/d)) for i in range(0, d, 2)]
    print(f"   {d:>8}{len(th):>8}{th[0]:>18.4f}{th[-1]:>18.6f}")
print("   Fast pairs encode 'near or far'. Slow pairs barely move, so they carry")
print("   meaning across long distances untouched. A d_head of 4 has no slow pairs,")
print("   which is why the toy model in this chapter exaggerates RoPE's effect.")
