from tinycc.lexer import Lexer, TokKind, LexError
import pytest


def kinds(src):
    return [t.kind for t in Lexer(src).tokens()]


def test_keywords():
    ks = kinds("program p; var x; begin end .")
    assert TokKind.PROGRAM in ks
    assert TokKind.VAR in ks
    assert TokKind.BEGIN in ks
    assert TokKind.END in ks


def test_multichar_operators():
    ks = kinds("x := 1; if x <= 2 then x := x <> 3")
    assert TokKind.ASSIGN in ks
    assert TokKind.LE in ks
    assert TokKind.NEQ in ks


def test_comments_skipped():
    toks = Lexer("{ this is a comment } var x").tokens()
    # only VAR, IDENT, EOF
    assert [t.kind for t in toks] == [TokKind.VAR, TokKind.IDENT, TokKind.EOF]


def test_bad_char_raises():
    with pytest.raises(LexError):
        Lexer("@").tokens()


def test_int_literal():
    toks = Lexer("12345").tokens()
    assert toks[0].kind is TokKind.INT
    assert toks[0].value == "12345"
