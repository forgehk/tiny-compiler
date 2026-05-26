from tinycc.parser import Parser, ParseError
from tinycc.ast_nodes import Program, Assign, While, If, Print, Read, BinOp, IntLit, Var
import pytest


def parse(src):
    return Parser.from_source(src).parse_program()


def test_minimal_program():
    p = parse("program p; begin end.")
    assert isinstance(p, Program)
    assert p.name == "p"
    assert p.decls == []
    assert p.body == []


def test_var_decls():
    p = parse("program p; var a; var b, c; begin end.")
    assert p.decls == ["a", "b", "c"]


def test_assign_with_arith():
    p = parse("program p; var x; begin x := 1 + 2 * 3 end.")
    a = p.body[0]
    assert isinstance(a, Assign)
    assert a.target == "x"
    # 1 + (2 * 3) — precedence
    assert isinstance(a.value, BinOp)
    assert a.value.op == "+"
    assert isinstance(a.value.right, BinOp)
    assert a.value.right.op == "*"


def test_if_else():
    p = parse("program p; var x; begin if x > 0 then x := 1 else x := -1 end.")
    s = p.body[0]
    assert isinstance(s, If)
    assert isinstance(s.then_block[0], Assign)
    assert isinstance(s.else_block[0], Assign)


def test_while():
    p = parse("program p; var n; begin while n > 0 do n := n - 1 end.")
    assert isinstance(p.body[0], While)


def test_print_read():
    p = parse("program p; var x; begin read(x); print(x + 1) end.")
    assert isinstance(p.body[0], Read)
    assert isinstance(p.body[1], Print)


def test_parse_error_on_missing_semicolon():
    with pytest.raises(ParseError):
        parse("program p var x begin end.")
