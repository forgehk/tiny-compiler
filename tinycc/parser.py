"""Recursive-descent parser for tiny.

Grammar:
    program     = "program" IDENT ";" var_decls block "."
    var_decls   = ( "var" ident_list ";" )*
    ident_list  = IDENT ( "," IDENT )*
    block       = "begin" stmt ( ";" stmt )* "end"
    stmt        = assign | if_stmt | while_stmt | print_stmt | read_stmt | block | ε
    assign      = IDENT ":=" expr
    if_stmt     = "if" expr "then" stmt ( "else" stmt )?
    while_stmt  = "while" expr "do" stmt
    print_stmt  = "print" "(" expr ")"
    read_stmt   = "read" "(" IDENT ")"
    expr        = rel
    rel         = sum ( ( "=" | "<>" | "<" | "<=" | ">" | ">=" ) sum )?
    sum         = term ( ( "+" | "-" ) term )*
    term        = factor ( ( "*" | "/" ) factor )*
    factor      = INT | IDENT | "(" expr ")" | "-" factor
"""
from __future__ import annotations
from .lexer import Lexer, Token, TokKind
from .ast_nodes import (
    Program, Block, Assign, If, While, Print, Read,
    BinOp, UnaryOp, IntLit, Var, Node,
)


class ParseError(Exception):
    pass


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    @classmethod
    def from_source(cls, src: str) -> "Parser":
        return cls(Lexer(src).tokens())

    # --- helpers ---
    def _peek(self, off: int = 0) -> Token:
        return self.tokens[self.pos + off]

    def _advance(self) -> Token:
        t = self.tokens[self.pos]
        if t.kind is not TokKind.EOF:
            self.pos += 1
        return t

    def _expect(self, kind: TokKind) -> Token:
        t = self._peek()
        if t.kind is not kind:
            raise ParseError(
                f"expected {kind.name} got {t.kind.name} ({t.value!r}) at {t.line}:{t.col}"
            )
        return self._advance()

    def _match(self, *kinds: TokKind) -> bool:
        return self._peek().kind in kinds

    # --- grammar ---
    def parse_program(self) -> Program:
        self._expect(TokKind.PROGRAM)
        name = self._expect(TokKind.IDENT).value
        self._expect(TokKind.SEMI)
        decls: list[str] = []
        while self._match(TokKind.VAR):
            self._advance()
            decls.append(self._expect(TokKind.IDENT).value)
            while self._match(TokKind.COMMA):
                self._advance()
                decls.append(self._expect(TokKind.IDENT).value)
            self._expect(TokKind.SEMI)
        body = self._block().stmts
        if self._match(TokKind.DOT):
            self._advance()
        self._expect(TokKind.EOF)
        return Program(name=name, decls=decls, body=body)

    def _block(self) -> Block:
        self._expect(TokKind.BEGIN)
        stmts: list[Node] = []
        if not self._match(TokKind.END):
            stmts.append(self._stmt())
            while self._match(TokKind.SEMI):
                self._advance()
                if self._match(TokKind.END):
                    break
                stmts.append(self._stmt())
        self._expect(TokKind.END)
        return Block(stmts=stmts)

    def _stmt(self) -> Node:
        t = self._peek()
        if t.kind is TokKind.IDENT:
            name = self._advance().value
            self._expect(TokKind.ASSIGN)
            return Assign(target=name, value=self._expr())
        if t.kind is TokKind.IF:
            self._advance()
            cond = self._expr()
            self._expect(TokKind.THEN)
            then_s = self._stmt_or_block()
            else_s: list[Node] = []
            if self._match(TokKind.ELSE):
                self._advance()
                else_s = self._stmt_or_block()
            return If(cond=cond, then_block=then_s, else_block=else_s)
        if t.kind is TokKind.WHILE:
            self._advance()
            cond = self._expr()
            self._expect(TokKind.DO)
            body = self._stmt_or_block()
            return While(cond=cond, body=body)
        if t.kind is TokKind.PRINT:
            self._advance()
            self._expect(TokKind.LPAREN)
            e = self._expr()
            self._expect(TokKind.RPAREN)
            return Print(expr=e)
        if t.kind is TokKind.READ:
            self._advance()
            self._expect(TokKind.LPAREN)
            n = self._expect(TokKind.IDENT).value
            self._expect(TokKind.RPAREN)
            return Read(target=n)
        if t.kind is TokKind.BEGIN:
            return self._block()
        raise ParseError(f"unexpected token {t.kind.name} ({t.value!r}) at {t.line}:{t.col}")

    def _stmt_or_block(self) -> list[Node]:
        if self._match(TokKind.BEGIN):
            return self._block().stmts
        return [self._stmt()]

    def _expr(self) -> Node:
        return self._rel()

    def _rel(self) -> Node:
        left = self._sum()
        if self._match(TokKind.EQ, TokKind.NEQ, TokKind.LT, TokKind.LE, TokKind.GT, TokKind.GE):
            op = self._advance().value
            right = self._sum()
            return BinOp(op=op, left=left, right=right)
        return left

    def _sum(self) -> Node:
        left = self._term()
        while self._match(TokKind.PLUS, TokKind.MINUS):
            op = self._advance().value
            right = self._term()
            left = BinOp(op=op, left=left, right=right)
        return left

    def _term(self) -> Node:
        left = self._factor()
        while self._match(TokKind.STAR, TokKind.SLASH):
            op = self._advance().value
            right = self._factor()
            left = BinOp(op=op, left=left, right=right)
        return left

    def _factor(self) -> Node:
        t = self._peek()
        if t.kind is TokKind.INT:
            return IntLit(value=int(self._advance().value))
        if t.kind is TokKind.IDENT:
            return Var(name=self._advance().value)
        if t.kind is TokKind.LPAREN:
            self._advance()
            e = self._expr()
            self._expect(TokKind.RPAREN)
            return e
        if t.kind is TokKind.MINUS:
            self._advance()
            return UnaryOp(op="-", operand=self._factor())
        raise ParseError(f"unexpected token {t.kind.name} ({t.value!r}) at {t.line}:{t.col}")
