"""AST node types for tiny."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Node:
    pass


@dataclass
class IntLit(Node):
    value: int


@dataclass
class Var(Node):
    name: str


@dataclass
class BinOp(Node):
    op: str  # +, -, *, /, =, <>, <, <=, >, >=
    left: Node
    right: Node


@dataclass
class UnaryOp(Node):
    op: str  # -
    operand: Node


@dataclass
class Assign(Node):
    target: str
    value: Node


@dataclass
class Print(Node):
    expr: Node


@dataclass
class Read(Node):
    target: str


@dataclass
class If(Node):
    cond: Node
    then_block: list[Node]
    else_block: list[Node] = field(default_factory=list)


@dataclass
class While(Node):
    cond: Node
    body: list[Node]


@dataclass
class Block(Node):
    stmts: list[Node]


@dataclass
class Program(Node):
    name: str
    decls: list[str]      # variable names
    body: list[Node]
