#!/usr/bin/env python3
"""Matrices as functions that move vectors. Run: python3 matrix_demo.py"""
import math
def mm(A, B):
    return [[sum(A[i][k]*B[k][j] for k in range(len(B))) for j in range(len(B[0]))]
            for i in range(len(A))]
def show(name, M):
    print(f"   {name}")
    for row in M: print("      [" + "  ".join(f"{v:>7.3f}" for v in row) + "]")

print("=== a matrix is a function: hand it a vector, get a vector back ===")
v = [[1.0, 0.0]]
STRETCH = [[2.0, 0.0], [0.0, 1.0]]
ROT90   = [[0.0, 1.0], [-1.0, 0.0]]
print(f"   input           {v[0]}")
print(f"   @ stretch-x     {mm(v, STRETCH)[0]}   (x doubled)")
print(f"   @ rotate 90°    {mm(v, ROT90)[0]}   (pointing a new way)")

print("\n=== shapes: [n,k] @ [k,m] -> [n,m]. the inner numbers must match, and they vanish ===")
A = [[1,2,3],[4,5,6]]          # [2,3]
B = [[1,0],[0,1],[1,1]]        # [3,2]
print(f"   A is [{len(A)},{len(A[0])}]   B is [{len(B)},{len(B[0])}]   A@B is "
      f"[{len(mm(A,B))},{len(mm(A,B)[0])}]")
show("A @ B =", mm(A, B))

print("\n=== one output number is one dot product ===")
print(f"   row 0 of A = {A[0]},  column 0 of B = {[B[r][0] for r in range(3)]}")
print(f"   their dot product = {sum(A[0][r]*B[r][0] for r in range(3))} = A@B at [0][0]")

print("\n=== composing: doing two matrices in a row IS one matrix ===")
both = mm(STRETCH, ROT90)
print(f"   v @ STRETCH @ ROT90 = {mm(mm(v, STRETCH), ROT90)[0]}")
print(f"   v @ (STRETCH@ROT90) = {mm(v, both)[0]}   <- same answer")
