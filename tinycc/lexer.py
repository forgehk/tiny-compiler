"""Lexer for tiny — emits typed tokens with line/col positions."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto


class TokKind(Enum):
    # literals
    INT = auto()
    IDENT = auto()
    # keywords
    VAR = auto()
    BEGIN = auto()
    END = auto()
    IF = auto()
    THEN = auto()
    ELSE = auto()
    WHILE = auto()
    DO = auto()
    PRINT = auto()
    READ = auto()
    PROGRAM = auto()
    # punctuation
    SEMI = auto()
    ASSIGN = auto()
    LPAREN = auto()
    RPAREN = auto()
    COMMA = auto()
    COLON = auto()
    # operators
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    EQ = auto()
    NEQ = auto()
    LT = auto()
    LE = auto()
    GT = auto()
    GE = auto()
    DOT = auto()
    EOF = auto()


KEYWORDS = {
    "var": TokKind.VAR,
    "begin": TokKind.BEGIN,
    "end": TokKind.END,
    "if": TokKind.IF,
    "then": TokKind.THEN,
    "else": TokKind.ELSE,
    "while": TokKind.WHILE,
    "do": TokKind.DO,
    "print": TokKind.PRINT,
    "read": TokKind.READ,
    "program": TokKind.PROGRAM,
}


@dataclass
class Token:
    kind: TokKind
    value: str
    line: int
    col: int


class LexError(Exception):
    pass


class Lexer:
    def __init__(self, src: str):
        self.src = src
        self.i = 0
        self.line = 1
        self.col = 1

    def _peek(self, off: int = 0) -> str:
        j = self.i + off
        return self.src[j] if j < len(self.src) else ""

    def _advance(self) -> str:
        ch = self.src[self.i]
        self.i += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def _skip_ws_and_comments(self) -> None:
        while self.i < len(self.src):
            ch = self._peek()
            if ch in " \t\r\n":
                self._advance()
            elif ch == "{":  # Pascal-style comment
                while self.i < len(self.src) and self._peek() != "}":
                    self._advance()
                if self.i < len(self.src):
                    self._advance()
            else:
                break

    def tokens(self) -> list[Token]:
        toks: list[Token] = []
        while True:
            self._skip_ws_and_comments()
            if self.i >= len(self.src):
                toks.append(Token(TokKind.EOF, "", self.line, self.col))
                return toks
            line, col = self.line, self.col
            ch = self._peek()
            if ch.isdigit():
                start = self.i
                while self._peek().isdigit():
                    self._advance()
                toks.append(Token(TokKind.INT, self.src[start:self.i], line, col))
            elif ch.isalpha() or ch == "_":
                start = self.i
                while self._peek().isalnum() or self._peek() == "_":
                    self._advance()
                word = self.src[start:self.i]
                kind = KEYWORDS.get(word.lower(), TokKind.IDENT)
                toks.append(Token(kind, word, line, col))
            elif ch == ":" and self._peek(1) == "=":
                self._advance(); self._advance()
                toks.append(Token(TokKind.ASSIGN, ":=", line, col))
            elif ch == "<" and self._peek(1) == "=":
                self._advance(); self._advance()
                toks.append(Token(TokKind.LE, "<=", line, col))
            elif ch == ">" and self._peek(1) == "=":
                self._advance(); self._advance()
                toks.append(Token(TokKind.GE, ">=", line, col))
            elif ch == "<" and self._peek(1) == ">":
                self._advance(); self._advance()
                toks.append(Token(TokKind.NEQ, "<>", line, col))
            elif ch in "+-*/();,:=<>.":
                self._advance()
                mapping = {
                    "+": TokKind.PLUS, "-": TokKind.MINUS,
                    "*": TokKind.STAR, "/": TokKind.SLASH,
                    "(": TokKind.LPAREN, ")": TokKind.RPAREN,
                    ";": TokKind.SEMI, ",": TokKind.COMMA,
                    ":": TokKind.COLON, "=": TokKind.EQ,
                    "<": TokKind.LT, ">": TokKind.GT,
                    ".": TokKind.DOT,
                }
                toks.append(Token(mapping[ch], ch, line, col))
            else:
                raise LexError(f"unexpected character {ch!r} at {line}:{col}")
