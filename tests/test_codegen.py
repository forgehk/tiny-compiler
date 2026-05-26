from tinycc.parser import Parser
from tinycc.codegen import CodeGen, CodegenError
import pytest


def asm(src):
    prog = Parser.from_source(src).parse_program()
    return CodeGen().generate(prog)


def test_emits_data_section_for_decls():
    a = asm("program p; var x, y; begin end.")
    assert "x: .word 0" in a
    assert "y: .word 0" in a
    assert ".text" in a
    assert "main:" in a


def test_exit_syscall_emitted():
    a = asm("program p; begin end.")
    assert "li $v0, 10" in a
    assert "syscall" in a


def test_print_uses_syscall_1_and_11():
    a = asm("program p; var x; begin x := 7; print(x) end.")
    assert "li $v0, 1" in a   # print_int
    assert "li $v0, 11" in a  # print_char (newline)


def test_assign_uses_sw():
    a = asm("program p; var x; begin x := 42 end.")
    assert "li $t0, 42" in a
    assert "sw $t0, x" in a


def test_while_has_loop_labels():
    a = asm("program p; var n; begin while n > 0 do n := n - 1 end.")
    assert "while_top_1:" in a
    assert "while_end_2:" in a


def test_undeclared_variable_raises():
    with pytest.raises(CodegenError):
        asm("program p; begin x := 1 end.")
