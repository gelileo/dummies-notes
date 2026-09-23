#!/usr/bin/env python3
"""A scalar automatic-differentiation engine in ~80 lines (micrograd-style), standard
library only. This is backpropagation with nothing hidden: every node remembers how it
was made, and .backward() walks the graph in reverse applying the chain rule.

Run: python3 autograd.py
"""
import math

class Value:
    """One number, plus the recipe for its gradient."""
    def __init__(self, data, children=(), op=''):
        self.data, self.grad = float(data), 0.0
        self._children, self._op = children, op
        self._backward = lambda: None          # how to push my gradient to my children

    def __add__(self, o):
        o = o if isinstance(o, Value) else Value(o)
        out = Value(self.data + o.data, (self, o), '+')
        def _backward():                        # d(a+b)/da = 1, d(a+b)/db = 1
            self.grad += out.grad
            o.grad    += out.grad
        out._backward = _backward
        return out

    def __mul__(self, o):
        o = o if isinstance(o, Value) else Value(o)
        out = Value(self.data * o.data, (self, o), '*')
        def _backward():                        # d(a*b)/da = b, d(a*b)/db = a
            self.grad += o.data * out.grad
            o.grad    += self.data * out.grad
        out._backward = _backward
        return out

    def tanh(self):
        t = math.tanh(self.data)
        out = Value(t, (self,), 'tanh')
        def _backward():                        # d tanh(x)/dx = 1 - tanh(x)^2
            self.grad += (1 - t*t) * out.grad
        out._backward = _backward
        return out

    def exp(self):
        e = math.exp(self.data)
        out = Value(e, (self,), 'exp')
        def _backward():                        # d exp(x)/dx = exp(x)
            self.grad += e * out.grad
        out._backward = _backward
        return out

    def log(self):
        out = Value(math.log(self.data), (self,), 'log')
        def _backward():                        # d log(x)/dx = 1/x
            self.grad += (1.0 / self.data) * out.grad
        out._backward = _backward
        return out

    def __neg__(self):        return self * -1
    def __sub__(self, o):     return self + (-o)
    def __radd__(self, o):    return self + o
    def __rmul__(self, o):    return self * o
    def __truediv__(self, o): return self * (o ** -1 if isinstance(o, Value) else 1.0/o)
    def __pow__(self, k):
        out = Value(self.data ** k, (self,), f'**{k}')
        def _backward():                        # d x^k/dx = k x^(k-1)
            self.grad += k * self.data ** (k-1) * out.grad
        out._backward = _backward
        return out

    def backward(self):
        """Reverse-mode: visit every node after all the nodes that depend on it."""
        order, seen = [], set()
        def visit(v):
            if v not in seen:
                seen.add(v)
                for c in v._children: visit(c)
                order.append(v)
        visit(self)
        self.grad = 1.0                         # d(self)/d(self) = 1
        for v in reversed(order):
            v._backward()

    def __repr__(self): return f"Value({self.data:.4f}, grad={self.grad:.4f})"


if __name__ == "__main__":
    print("=== 1. forward builds a graph; backward walks it in reverse ===")
    x, y = Value(2.0), Value(-3.0)
    a = x * y            # -6
    b = a + x            # -4
    L = b.tanh()         # tanh(-4)
    L.backward()
    print(f"   L = tanh(x*y + x) at x=2, y=-3  ->  L = {L.data:.6f}")
    print(f"   dL/dx = {x.grad:.6f}     dL/dy = {y.grad:.6f}")

    print("\n=== 2. check against finite differences (the definition of a derivative) ===")
    def f(xv, yv): return math.tanh(xv*yv + xv)
    h = 1e-6
    print(f"   numeric dL/dx = {(f(2+h,-3)-f(2-h,-3))/(2*h):.6f}   autograd {x.grad:.6f}")
    print(f"   numeric dL/dy = {(f(2,-3+h)-f(2,-3-h))/(2*h):.6f}   autograd {y.grad:.6f}")
    print("   They agree. The engine is doing calculus, not guessing.")

    print("\n=== 3. why the chain rule: a 3-deep composition, by hand and by engine ===")
    x = Value(0.5)
    u = x * x            # u = x^2        du/dx = 2x   = 1.0
    v = u * 3 + 1        # v = 3u + 1     dv/du = 3
    w = v.exp()          # w = e^v        dw/dv = e^v
    w.backward()
    hand = math.exp(3*0.25+1) * 3 * (2*0.5)
    print(f"   w = exp(3x^2 + 1) at x=0.5")
    print(f"   by hand:  dw/dv * dv/du * du/dx = {math.exp(1.75):.4f} * 3 * 1.0 = {hand:.4f}")
    print(f"   by engine: {x.grad:.4f}")
    print("   Multiply the local slopes along the path. That is all backprop is.")

    print("\n=== 4. 'define a loss, take its gradient, step downhill, repeat' ===")
    # fit y = m*x + c to noisy points, using nothing but this engine
    pts = [(0, 1.1), (1, 2.9), (2, 5.2), (3, 6.8), (4, 9.1)]      # roughly y = 2x + 1
    m, c = Value(0.0), Value(0.0)
    lr = 0.02
    for step in range(301):
        loss = sum(((m * xv + c) - yv) ** 2 for xv, yv in pts) * (1.0/len(pts))
        m.grad = c.grad = 0.0            # gradients ACCUMULATE; zero them every step
        loss.backward()
        m.data -= lr * m.grad            # the update: a step against the gradient
        c.data -= lr * c.grad
        if step in (0, 1, 5, 20, 100, 300):
            print(f"   step {step:>3}: loss {loss.data:8.4f}   m {m.data:6.3f}   c {c.data:6.3f}"
                  f"   dL/dm {m.grad:8.3f}")
    print("   Converging on m~2, c~1. Every model in this curriculum trains this way;")
    print("   only the loss function and the number of parameters change.")
