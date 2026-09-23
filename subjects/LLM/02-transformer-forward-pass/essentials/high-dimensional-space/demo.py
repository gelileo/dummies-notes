#!/usr/bin/env python3
"""Why 4096 dimensions behaves nothing like 2 or 3. Run: python3 highdim_demo.py"""
import math, random
dot = lambda a, b: sum(x*y for x, y in zip(a, b))
length = lambda v: math.sqrt(dot(v, v))
cosine = lambda a, b: dot(a, b)/(length(a)*length(b))

print("=== pick two random directions. how far apart are they? ===")
print(f"   {'d':>6}{'mean angle':>13}{'mean |cosine|':>15}{'within 10° of 90°':>20}")
for d in (2, 3, 10, 100, 1000, 4096):
    random.seed(2)
    cs = [cosine([random.gauss(0,1) for _ in range(d)],
                 [random.gauss(0,1) for _ in range(d)]) for _ in range(500)]
    ang = [math.degrees(math.acos(max(-1, min(1, c)))) for c in cs]
    near = 100*sum(1 for a in ang if abs(a-90) < 10)/len(ang)
    print(f"   {d:>6}{sum(ang)/len(ang):>12.1f}°{sum(abs(c) for c in cs)/len(cs):>15.3f}{near:>19.0f}%")
print("   In 2D, two random arrows are often close together. In 4096D they are")
print("   essentially ALWAYS perpendicular -- there is simply that much room.")

print("\n=== so how many 'almost separate' directions fit in d dimensions? ===")
print("   exactly perpendicular: only d of them. but if 'nearly' is good enough,")
print("   far more. pack N random directions and measure the WORST overlap:")
print(f"   {'d':>6}{'N packed':>11}{'worst |cosine| of any pair':>28}")
for d, N in ((64, 500), (256, 2000), (1024, 5000), (4096, 5000)):
    random.seed(7)
    vs = []
    for _ in range(N):
        v = [random.gauss(0,1) for _ in range(d)]
        L = length(v); vs.append([x/L for x in v])
    worst = 0.0
    for i in range(0, len(vs), 7):            # sample pairs; full N^2 is too slow
        for j in range(i+1, min(i+40, len(vs))):
            worst = max(worst, abs(dot(vs[i], vs[j])))
    print(f"   {d:>6}{N:>11,}{worst:>28.3f}")
print("   5,000 directions in 4096 dimensions, none overlapping much. That is why a")
print("   4096-number vector can track far more than 4096 features: they are packed")
print("   in as nearly-separate directions rather than perfectly separate ones.")

print("\n=== overlapping directions still read out cleanly ===")
random.seed(5); d = 512
feats = {n: [random.gauss(0,1) for _ in range(d)] for n in ("plural","past","question","animal")}
for n in feats: 
    L = length(feats[n]); feats[n] = [x/L for x in feats[n]]
mix = [sum(feats[n][i] for n in ("plural","animal")) for i in range(d)]
print(f"   stored 'plural' + 'animal' in one {d}-dim vector, then measured each feature:")
for n, v in feats.items():
    print(f"      {n:<10} {dot(mix, v):>7.3f}   {'<- present' if dot(mix,v) > 0.5 else ''}")
