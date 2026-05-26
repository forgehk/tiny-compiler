"""tiny-compiler command-line interface.

Examples:
    tinycc compile examples/factorial.tiny -o out.s
    tinycc run examples/factorial.tiny           # interpret
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

from .parser import Parser, ParseError
from .lexer import LexError
from .codegen import CodeGen, CodegenError
from .interp import Interpreter, RuntimeErr


def cmd_compile(args: argparse.Namespace) -> int:
    src = Path(args.input).read_text()
    try:
        prog = Parser.from_source(src).parse_program()
        asm = CodeGen().generate(prog)
    except (LexError, ParseError, CodegenError) as e:
        print(f"compile error: {e}", file=sys.stderr)
        return 2
    out = Path(args.output) if args.output else Path(args.input).with_suffix(".s")
    out.write_text(asm)
    print(f"wrote {out}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    src = Path(args.input).read_text()
    try:
        prog = Parser.from_source(src).parse_program()
    except (LexError, ParseError) as e:
        print(f"parse error: {e}", file=sys.stderr)
        return 2
    inputs = sys.stdin.read().split() if not sys.stdin.isatty() else []
    try:
        out = Interpreter(stdin_iter=inputs).run(prog)
    except RuntimeErr as e:
        print(f"runtime error: {e}", file=sys.stderr)
        return 3
    for line in out:
        print(line)
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="tinycc", description="tiny → MIPS compiler")
    sp = p.add_subparsers(dest="cmd", required=True)

    pc = sp.add_parser("compile", help="compile .tiny → MIPS assembly")
    pc.add_argument("input")
    pc.add_argument("-o", "--output", help="output .s file")
    pc.set_defaults(func=cmd_compile)

    pr = sp.add_parser("run", help="interpret .tiny directly (no MIPS needed)")
    pr.add_argument("input")
    pr.set_defaults(func=cmd_run)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
