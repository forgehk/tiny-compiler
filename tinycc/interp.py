"""Pure-Python interpreter for tiny. Useful for testing AST + semantics
without needing a MIPS simulator."""
from __future__ import annotations
from .ast_nodes import (
    Program, Assign, If, While, Print, Read,
    BinOp, UnaryOp, IntLit, Var, Node,
)


class RuntimeErr(Exception):
    pass


class Interpreter:
    def __init__(self, stdin_iter=None):
        self.env: dict[str, int] = {}
        self.stdin = iter(stdin_iter or [])
        self.output: list[str] = []

    def run(self, prog: Program) -> list[str]:
        for v in prog.decls:
            self.env[v] = 0
        for s in prog.body:
            self._stmt(s)
        return self.output

    def _stmt(self, n: Node) -> None:
        if isinstance(n, Assign):
            self.env[n.target] = self._eval(n.value)
        elif isinstance(n, Print):
            self.output.append(str(self._eval(n.expr)))
        elif isinstance(n, Read):
            try:
                self.env[n.target] = int(next(self.stdin))
            except StopIteration:
                raise RuntimeErr("read: no more input")
        elif isinstance(n, If):
            target = n.then_block if self._eval(n.cond) else n.else_block
            for s in target:
                self._stmt(s)
        elif isinstance(n, While):
            while self._eval(n.cond):
                for s in n.body:
                    self._stmt(s)
        else:
            raise RuntimeErr(f"bad stmt: {type(n).__name__}")

    def _eval(self, n: Node) -> int:
        if isinstance(n, IntLit):
            return n.value
        if isinstance(n, Var):
            if n.name not in self.env:
                raise RuntimeErr(f"undeclared {n.name}")
            return self.env[n.name]
        if isinstance(n, UnaryOp) and n.op == "-":
            return -self._eval(n.operand)
        if isinstance(n, BinOp):
            a = self._eval(n.left)
            b = self._eval(n.right)
            if n.op == "+": return a + b
            if n.op == "-": return a - b
            if n.op == "*": return a * b
            if n.op == "/":
                if b == 0:
                    raise RuntimeErr("division by zero")
                # truncate toward zero (matches MIPS div)
                q = abs(a) // abs(b)
                return q if (a < 0) == (b < 0) else -q
            if n.op == "=":  return int(a == b)
            if n.op == "<>": return int(a != b)
            if n.op == "<":  return int(a < b)
            if n.op == "<=": return int(a <= b)
            if n.op == ">":  return int(a > b)
            if n.op == ">=": return int(a >= b)
        raise RuntimeErr(f"bad expr: {type(n).__name__}")
