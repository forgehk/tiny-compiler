"""The `mod` operator across every stage: lexer, parser, codegen, interpreter."""
from tinycc.lexer import Lexer, TokKind
from tinycc.parser import Parser
from tinycc.ast_nodes import BinOp, Assign
from tinycc.codegen import CodeGen
from tinycc.interp import Interpreter, RuntimeErr
import pytest


def parse(src):
    return Parser.from_source(src).parse_program()


def run(src, stdin=None):
    return Interpreter(stdin_iter=stdin).run(parse(src))


# --- lexer ---

def test_mod_is_a_keyword_case_insensitive():
    assert [t.kind for t in Lexer("a mod b").tokens()] == [
        TokKind.IDENT, TokKind.MOD, TokKind.IDENT, TokKind.EOF]
    assert Lexer("MOD").tokens()[0].kind is TokKind.MOD


def test_identifiers_containing_mod_stay_identifiers():
    toks = Lexer("modulo module mode").tokens()
    assert [t.kind for t in toks[:3]] == [TokKind.IDENT] * 3


# --- parser ---

def test_mod_binds_like_star_and_slash():
    # 1 + (7 mod 3) — mod is tighter than +
    a = parse("program p; var x; begin x := 1 + 7 mod 3 end.").body[0]
    assert isinstance(a, Assign)
    assert a.value.op == "+"
    assert isinstance(a.value.right, BinOp)
    assert a.value.right.op == "mod"


def test_mod_is_left_associative_with_star():
    # (a mod b) * c — same level as *, left to right
    a = parse("program p; var a, b, c, x; begin x := a mod b * c end.").body[0]
    assert a.value.op == "*"
    assert a.value.left.op == "mod"


def test_uppercase_mod_normalises_to_lowercase_op():
    a = parse("program p; var x; begin x := 7 MOD 3 end.").body[0]
    assert a.value.op == "mod"


# --- codegen ---

def test_codegen_uses_div_and_mfhi():
    asm = CodeGen().generate(parse("program p; var x; begin x := 7 mod 3 end."))
    lines = [l.strip() for l in asm.splitlines()]
    i = lines.index("div $t0, $t1")
    assert lines[i + 1] == "mfhi $t0"
    assert "mflo $t0" not in lines


# --- interpreter ---

@pytest.mark.parametrize("a, b, want", [
    (7, 3, 1),
    (6, 3, 0),
    (3, 7, 3),
    (-7, 3, -1),   # sign follows the dividend, like MIPS mfhi and C's %
    (7, -3, 1),
    (-7, -3, -1),
    (0, 5, 0),
])
def test_mod_semantics_match_mips(a, b, want):
    assert run(f"program p; begin print({a} mod {b}) end.") == [str(want)]


def test_mod_agrees_with_div_identity():
    # a = (a / b) * b + (a mod b) for every combination of signs
    for a in (-13, -7, 0, 7, 13):
        for b in (-4, -3, 3, 4):
            out = run(f"program p; begin print(({a} / {b}) * {b} + ({a} mod {b})) end.")
            assert out == [str(a)]


def test_mod_by_zero_raises():
    with pytest.raises(RuntimeErr):
        run("program p; var x; begin x := 1 mod 0 end.")


def test_fizzbuzz_with_mod():
    src = """program fb; var i;
    begin
        i := 1;
        while i <= 15 do
        begin
            if i mod 15 = 0 then print(0)
            else if i mod 3 = 0 then print(-3)
            else if i mod 5 = 0 then print(-5)
            else print(i);
            i := i + 1
        end
    end."""
    assert run(src) == ["1", "2", "-3", "4", "-5", "-3", "7", "8", "-3",
                        "-5", "11", "-3", "13", "14", "0"]
