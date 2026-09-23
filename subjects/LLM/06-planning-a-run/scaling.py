#!/usr/bin/env python3
"""Planning a training run: FLOPs, scaling laws, compute-optimal allocation, and what
a smooth loss curve does and does not predict. numpy. Run: python3 scaling.py

The loss-vs-scale function used below is Chinchilla's PUBLISHED fit (Hoffmann et al. 2022):
    L(N, D) = E + A / N^alpha + B / D^beta
with E=1.69, A=406.4, B=410.7, alpha=0.34, beta=0.28. Those are reported constants, not
measured here; everything computed FROM them is exact arithmetic.
"""
import numpy as np

E, A, B, ALPHA, BETA = 1.69, 406.4, 410.7, 0.34, 0.28
def L(N, D): return E + A / N**ALPHA + B / D**BETA

def flops_train(N, D): return 6.0 * N * D
def gpu_hours(flops, peak=990e12, mfu=0.40): return flops / (peak * mfu) / 3600

if __name__ == "__main__":
    print("=== 1. where 6ND comes from ===")
    print("   a matrix multiply [n,k]@[k,m] costs 2*n*k*m FLOPs (one multiply + one add per term).")
    print("   for one token through one weight matrix with k*m = P parameters: 2P FLOPs forward.")
    print("   backward needs two such products (grad wrt input, grad wrt weights): 4P.")
    print("   so one token, all N parameters, forward+backward = 6N.  D tokens: 6ND.")
    N8, D8 = 8.03e9, 15e12
    C8 = flops_train(N8, D8)
    print(f"   Llama-3-8B: 6 * {N8:.2e} * {D8:.1e} = {C8:.2e} FLOPs")
    print(f"   at 40% of an H100's 990 TFLOP/s bf16 peak: {gpu_hours(C8):,.0f} GPU-hours "
          f"= {gpu_hours(C8)/24/1000:.0f}k GPU-days... /1000 GPUs = {gpu_hours(C8)/24/1000:.0f} days")
    print("   (meta reported ~1.3M GPU-hours -- reported, not measured; the gap is attention")
    print("    FLOPs that 6ND omits, plus real utilisation being below 40%.)")

    print("\n=== 2. the scaling law: loss vs parameters at fixed data, and vice versa ===")
    print(f"   {'N (params)':>12}{'L at D=1e11':>13}{'L at D=1e12':>13}{'L at D=1e13':>13}")
    for N in (1e8, 1e9, 1e10, 1e11):
        print(f"   {N:>12.0e}" + "".join(f"{L(N, D):>13.3f}" for D in (1e11, 1e12, 1e13)))
    print(f"   every entry -> {E} as N,D -> inf. that is the irreducible loss (chapter 03).")

    print("\n=== 3. straight lines on log-log axes -- if you subtract the WHOLE floor ===")
    Ns = np.logspace(8, 11, 7); D = 1e13
    ex1 = L(Ns, D) - E                            # subtract only the irreducible loss
    ex2 = L(Ns, D) - E - B / D**BETA              # also subtract the data term (a second 'floor' at fixed D)
    s1, _ = np.polyfit(np.log10(Ns), np.log10(ex1), 1)
    s2, _ = np.polyfit(np.log10(Ns), np.log10(ex2), 1)
    print(f"   {'log10 N':>9}{'log10(L - E)':>14}{'log10(L - E - B/D^b)':>22}")
    for n, a_, b_ in zip(Ns, ex1, ex2): print(f"   {np.log10(n):>9.2f}{np.log10(a_):>14.3f}{np.log10(b_):>22.3f}")
    print(f"   fitted slope: {s1:.3f} vs {s2:.3f}   (the law's exponent is -alpha = {-ALPHA})")
    print("   at fixed data the B/D^beta term is a constant offset you did not remove, and it")
    print("   BENDS the line: slope -0.24 instead of -0.34. subtract every floor, then fit.")
    print("   a plot that is 'roughly straight' on log-log is a hypothesis; the residuals decide.")

    print("\n=== 4. compute-optimal: given C FLOPs, how big a model, how much data? ===")
    print(f"   {'budget C':>10}{'best N':>10}{'best D':>10}{'D/N':>7}{'loss':>8}   vs GPT-3 shape (175B) at same C")
    for C in (1e21, 1e22, 1e23, 1e24):
        Ns = np.logspace(7, 13, 2000); Ds = C / (6*Ns)
        losses = L(Ns, Ds); i = losses.argmin()
        Ngpt = 175e9; Dgpt = C / (6*Ngpt)
        print(f"   {C:>10.0e}{Ns[i]:>10.2e}{Ds[i]:>10.2e}{Ds[i]/Ns[i]:>7.0f}{losses[i]:>8.3f}"
              f"   175B model gets D={Dgpt:.1e}, loss {L(Ngpt, Dgpt):.3f}")
    print("   this parametric fit says 50-100 tokens per parameter, rising with budget.")
    print("   Chinchilla's other two estimation methods gave the famous ~20:1 at ~1e23 FLOPs.")
    print("   the methods disagree on the number; all three agree on the direction: GPT-3's")
    print("   300B tokens on 175B params (1.7 per param) was far too big a model for its data,")
    print("   and the right-hand column shows what that costs at every budget.")

    print("\n=== 5. but inference cost is N, not D: why production models over-train ===")
    N = 8e9
    print(f"   an 8B model. training longer keeps helping, and serving cost does not change:")
    print(f"   {'D (tokens)':>12}{'D/N':>7}{'loss':>8}{'train FLOPs':>14}")
    for D in (1.6e11, 4e11, 1e12, 4e12, 15e12):
        print(f"   {D:>12.1e}{D/N:>7.0f}{L(N, D):>8.3f}{flops_train(N, D):>14.1e}")
    print("   Llama-3-8B trained on 15T tokens = ~1900 tokens/param, 90x past compute-optimal.")
    print("   deliberately: training is paid once, inference forever. small-and-overtrained wins.")

    print("\n=== 6. the point of a scaling law: predict before you spend ===")
    ladder_N = np.array([1e8, 3e8, 1e9, 3e9])
    ladder_D = 20 * ladder_N
    ladder_L = L(ladder_N, ladder_D) + np.random.default_rng(0).normal(0, 0.01, 4)  # small run noise
    C_ladder = flops_train(ladder_N, ladder_D)
    m, c = np.polyfit(np.log10(C_ladder), np.log10(ladder_L - E), 1)
    target_N = 70e9; target_D = 20 * target_N; target_C = flops_train(target_N, target_D)
    pred = E + 10**(m*np.log10(target_C) + c)
    print(f"   fit on four small runs (1e8..3e9 params, compute-optimal), extrapolate 20x+:")
    for n_, c_, l_ in zip(ladder_N, C_ladder, ladder_L): print(f"      N={n_:.0e}  C={c_:.1e}  loss {l_:.3f}")
    print(f"   predicted loss for a 70B model at {target_C:.1e} FLOPs: {pred:.3f}")
    print(f"   the law evaluated there:                              {L(target_N, target_D):.3f}")
    print("   this demonstrates the PROCEDURE on a known law, not the law's truth -- the ladder")
    print("   is generated by the same equation it predicts. in a real lab the small runs are")
    print("   real training runs, and the extrapolation is the bet. GPT-4's report describes")
    print("   predicting its final loss from runs with 1,000-10,000x less compute (reported).")

    print("\n=== 7. emergence: a smooth loss can hide a sharp capability ===")
    print("   suppose per-token accuracy p rises smoothly with scale. a task needs k tokens ALL right:")
    print(f"   {'p':>6}" + "".join(f"{f'k={k}':>9}" for k in (1, 5, 10, 20)))
    for p in (0.80, 0.85, 0.90, 0.95, 0.98, 0.99):
        print(f"   {p:>6.2f}" + "".join(f"{p**k:>9.3f}" for k in (1, 5, 10, 20)))
    print("   p moves smoothly 0.80 -> 0.99; the k=20 column jumps 0.01 -> 0.82. the 'sudden'")
    print("   ability is the metric's threshold, not a discontinuity in the model.")
