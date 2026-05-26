"""MIPS-32 code generator for tiny.

Calling convention: stack-based expressions, $t0 = lhs, $t1 = rhs.
Variables live in .data as 4-byte words.
Syscalls used:
   1  print_int  ($a0)
   5  read_int   (returns $v0)
  10  exit

The output is plain MIPS assembly suitable for SPIM/MARS.
"""
from __future__ import annotations
from .ast_nodes import (
    Program, Assign, If, While, Print, Read,
    BinOp, UnaryOp, IntLit, Var, Node,
)


class CodegenError(Exception):
    pass


class CodeGen:
    def __init__(self) -> None:
        self.lines: list[str] = []
        self.label_n = 0
        self.declared: set[str] = set()

    def _emit(self, line: str) -> None:
        self.lines.append(line)

    def _new_label(self, prefix: str) -> str:
        self.label_n += 1
        return f"{prefix}_{self.label_n}"

    def _check_var(self, name: str) -> None:
        if name not in self.declared:
            raise CodegenError(f"undeclared variable {name!r}")

    def generate(self, prog: Program) -> str:
        self.declared = set(prog.decls)
        # .data
        self._emit("# tiny-compiler generated MIPS")
        self._emit("    .data")
        for v in prog.decls:
            self._emit(f"{v}: .word 0")
        self._emit("    .text")
        self._emit("    .globl main")
        self._emit("main:")
        for stmt in prog.body:
            self._gen_stmt(stmt)
        # exit syscall
        self._emit("    li $v0, 10")
        self._emit("    syscall")
        return "\n".join(self.lines) + "\n"

    # --- statements ---
    def _gen_stmt(self, n: Node) -> None:
        if isinstance(n, Assign):
            self._check_var(n.target)
            self._gen_expr(n.value)              # result in $t0
            self._emit(f"    sw $t0, {n.target}")
        elif isinstance(n, Print):
            self._gen_expr(n.expr)
            self._emit("    move $a0, $t0")
            self._emit("    li $v0, 1")
            self._emit("    syscall")
            # newline
            self._emit("    li $a0, 10")
            self._emit("    li $v0, 11")
            self._emit("    syscall")
        elif isinstance(n, Read):
            self._check_var(n.target)
            self._emit("    li $v0, 5")
            self._emit("    syscall")
            self._emit(f"    sw $v0, {n.target}")
        elif isinstance(n, If):
            else_lbl = self._new_label("else")
            end_lbl = self._new_label("endif")
            self._gen_expr(n.cond)
            self._emit(f"    beq $t0, $zero, {else_lbl}")
            for s in n.then_block:
                self._gen_stmt(s)
            self._emit(f"    j {end_lbl}")
            self._emit(f"{else_lbl}:")
            for s in n.else_block:
                self._gen_stmt(s)
            self._emit(f"{end_lbl}:")
        elif isinstance(n, While):
            top_lbl = self._new_label("while_top")
            end_lbl = self._new_label("while_end")
            self._emit(f"{top_lbl}:")
            self._gen_expr(n.cond)
            self._emit(f"    beq $t0, $zero, {end_lbl}")
            for s in n.body:
                self._gen_stmt(s)
            self._emit(f"    j {top_lbl}")
            self._emit(f"{end_lbl}:")
        else:
            raise CodegenError(f"unsupported stmt: {type(n).__name__}")

    # --- expressions: result always lands in $t0 ---
    def _gen_expr(self, n: Node) -> None:
        if isinstance(n, IntLit):
            self._emit(f"    li $t0, {n.value}")
            return
        if isinstance(n, Var):
            self._check_var(n.name)
            self._emit(f"    lw $t0, {n.name}")
            return
        if isinstance(n, UnaryOp) and n.op == "-":
            self._gen_expr(n.operand)
            self._emit("    sub $t0, $zero, $t0")
            return
        if isinstance(n, BinOp):
            # eval left, push, eval right, pop into $t1
            self._gen_expr(n.left)
            self._emit("    addi $sp, $sp, -4")
            self._emit("    sw $t0, 0($sp)")
            self._gen_expr(n.right)
            self._emit("    move $t1, $t0")
            self._emit("    lw $t0, 0($sp)")
            self._emit("    addi $sp, $sp, 4")
            if n.op == "+":
                self._emit("    add $t0, $t0, $t1")
            elif n.op == "-":
                self._emit("    sub $t0, $t0, $t1")
            elif n.op == "*":
                self._emit("    mul $t0, $t0, $t1")
            elif n.op == "/":
                self._emit("    div $t0, $t1")
                self._emit("    mflo $t0")
            elif n.op in ("=", "<>", "<", "<=", ">", ">="):
                self._gen_cmp(n.op)
            else:
                raise CodegenError(f"unsupported op {n.op!r}")
            return
        raise CodegenError(f"unsupported expr: {type(n).__name__}")

    def _gen_cmp(self, op: str) -> None:
        """Result is 1 or 0 in $t0. Inputs in $t0 (lhs), $t1 (rhs)."""
        if op == "=":
            self._emit("    sub $t0, $t0, $t1")
            self._emit("    sltiu $t0, $t0, 1")
        elif op == "<>":
            self._emit("    sub $t0, $t0, $t1")
            self._emit("    sltu $t0, $zero, $t0")
        elif op == "<":
            self._emit("    slt $t0, $t0, $t1")
        elif op == ">":
            self._emit("    slt $t0, $t1, $t0")
        elif op == "<=":
            self._emit("    slt $t0, $t1, $t0")
            self._emit("    xori $t0, $t0, 1")
        elif op == ">=":
            self._emit("    slt $t0, $t0, $t1")
            self._emit("    xori $t0, $t0, 1")
