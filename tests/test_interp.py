from tinycc.parser import Parser
from tinycc.interp import Interpreter, RuntimeErr
import pytest


def run(src, stdin=None):
    prog = Parser.from_source(src).parse_program()
    return Interpreter(stdin_iter=stdin).run(prog)


def test_print_literal():
    assert run("program p; begin print(42) end.") == ["42"]


def test_arithmetic_precedence():
    assert run("program p; begin print(2 + 3 * 4) end.") == ["14"]


def test_factorial_5():
    src = """program f; var n, r;
    begin
        n := 5; r := 1;
        while n > 1 do begin r := r * n; n := n - 1 end;
        print(r)
    end."""
    assert run(src) == ["120"]


def test_gcd_via_subtract():
    src = """program g; var a, b, t;
    begin
        a := 48; b := 18;
        while b <> 0 do begin
            t := b;
            b := a - (a / b) * b;
            a := t
        end;
        print(a)
    end."""
    assert run(src) == ["6"]


def test_if_else_branches():
    src = """program p; var x;
    begin
        x := 5;
        if x > 0 then print(1) else print(-1)
    end."""
    assert run(src) == ["1"]


def test_read_input():
    src = "program p; var x; begin read(x); print(x * 2) end."
    assert run(src, stdin=["21"]) == ["42"]


def test_division_by_zero_raises():
    src = "program p; var x; begin x := 10 / 0; print(x) end."
    with pytest.raises(RuntimeErr):
        run(src)
