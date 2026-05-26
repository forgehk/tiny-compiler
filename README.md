# tiny-compiler

> A small Pascal-like language that compiles to **MIPS-32 assembly** — pairs with [mips-emulator](https://github.com/forgehk/mips-emulator) so you can compile your code and then run it.

[![Tests](https://img.shields.io/badge/tests-25%2F25%20passing-success.svg)]()
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A full compiler front-to-back: **lexer → parser → AST → codegen → MIPS assembly**. Also ships an interpreter so you can run programs without a MIPS simulator.

## Why

Most "build your own compiler" projects either stop at parsing or hand-wave the backend. `tiny` actually emits assembly that runs in SPIM / MARS. The whole pipeline lives in ~700 lines of straightforward Python.

## The language

Pascal-style syntax, integers only, with the usual control flow:

```pascal
program factorial;
var n, result;
begin
    read(n);
    result := 1;
    while n > 1 do
    begin
        result := result * n;
        n := n - 1
    end;
    print(result)
end.
```

Supported: variable declarations, `:=` assignment, `if/then/else`, `while/do`, `read(x)` / `print(expr)`, full arithmetic (`+ - * /`), relational ops (`= <> < <= > >=`), parenthesized expressions, unary minus, and `{ pascal-style comments }`.

## Install

```bash
git clone https://github.com/forgehk/tiny-compiler.git
cd tiny-compiler
pip install -e ".[dev]"
```

## Use it

**Compile to MIPS assembly:**

```bash
tinycc compile examples/factorial.tiny -o factorial.s
```

Open `factorial.s` in MARS or SPIM, hit run, and enter an integer when prompted.

**Interpret directly (no MIPS simulator needed):**

```bash
echo 5 | tinycc run examples/factorial.tiny
# 120
```

## How it works

The pipeline is exactly the four phases every compiler textbook describes:

| Stage | File | What it does |
|---|---|---|
| Lexer | `tinycc/lexer.py` | Hand-written scanner — keywords, multi-char ops (`:=`, `<=`, `<>`), comments, position tracking |
| Parser | `tinycc/parser.py` | Recursive-descent, builds typed AST nodes |
| AST | `tinycc/ast_nodes.py` | Dataclass nodes — `Program`, `If`, `While`, `BinOp`, etc. |
| Codegen | `tinycc/codegen.py` | Emits MIPS-32 — stack-allocated temporaries, label generation, syscall conventions |
| Interpreter | `tinycc/interp.py` | Reference implementation against the same AST |

Expression evaluation uses the classic stack discipline: evaluate left into `$t0`, push, evaluate right, pop into `$t1`, do the op. The data segment holds variables as `.word`s. Syscalls 1/5/10/11 handle print_int / read_int / exit / newline.

## Tests

```bash
pytest -q
# 25 passed
```

The suite covers the lexer (keywords, multi-char ops, comments, errors), the parser (precedence, control flow, error reporting), the codegen (data section, syscalls, labels, undeclared-variable detection), and the interpreter (factorial, GCD, division-by-zero, stdin handling).

## Examples

- `examples/factorial.tiny` — iterative factorial
- `examples/fizzbuzz.tiny` — fizzbuzz via integer division (no modulo operator in the language, so `(i/n)*n = i` substitutes)
- `examples/gcd.tiny` — Euclidean GCD

## Companion: run on the emulator

This pairs with [mips-emulator](https://github.com/forgehk/mips-emulator) — same author, same MIPS-32 dialect. Compile here, run there.

## License

MIT — see [LICENSE](LICENSE).
