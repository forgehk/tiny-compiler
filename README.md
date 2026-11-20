# tiny-compiler

> A compiler for a small Pascal-style language. It emits MIPS-32 assembly, and it ships an interpreter over the same syntax tree as a reference for what a program should do.

[![CI](https://github.com/forgehk/tiny-compiler/actions/workflows/ci.yml/badge.svg)](https://github.com/forgehk/tiny-compiler/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Status:** a complete teaching compiler for a deliberately small language: integers, assignment, `if`, `while`, `read` and `print`. There are no procedures, arrays or strings, and the generated assembly is not yet run by any test. [Limits](#limits) has the details.

## Source, assembly, output

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

```console
$ tinycc compile examples/factorial.tiny -o factorial.s
wrote factorial.s
$ head -12 factorial.s
# tiny-compiler generated MIPS
    .data
n: .word 0
result: .word 0
    .text
    .globl main
main:
    li $v0, 5
    syscall
    sw $v0, n
    li $t0, 1
    sw $t0, result
$ echo 5 | tinycc run examples/factorial.tiny
120
```

```text
 source ──▶ lexer ──▶ parser ──▶ syntax tree ──┬──▶ code generator ──▶ MIPS-32 assembly
            lexer.py  parser.py  ast_nodes.py  │    codegen.py
                                               └──▶ interpreter ──▶ the program's output
                                                    interp.py
```

## Quick start

Needs Python 3.11 or newer.

```bash
git clone https://github.com/forgehk/tiny-compiler.git
cd tiny-compiler
pip install -e ".[dev]"

echo 5 | tinycc run examples/factorial.tiny              # interpret: prints 120
tinycc compile examples/factorial.tiny -o factorial.s    # compile to assembly
pytest -q                                                # 41 tests
```

## The language

Supported: variable declarations, `:=` assignment, `if/then/else`, `while/do`, `read(x)` / `print(expr)`, full arithmetic (`+ - * /` and `mod`, which truncates toward zero and takes the sign of the dividend, like MIPS `div`/`mfhi`), relational ops (`= <> < <= > >=`), parenthesized expressions, unary minus, and `{ pascal-style comments }`.

## How it works

| Stage | File | What it does |
|---|---|---|
| Lexer | `tinycc/lexer.py` | Hand-written scanner: keywords, multi-char ops (`:=`, `<=`, `<>`), comments, position tracking |
| Parser | `tinycc/parser.py` | Recursive-descent, builds typed AST nodes |
| AST | `tinycc/ast_nodes.py` | Dataclass nodes: `Program`, `If`, `While`, `BinOp`, etc. |
| Codegen | `tinycc/codegen.py` | Emits MIPS-32: stack-allocated temporaries, label generation, syscall conventions |
| Interpreter | `tinycc/interp.py` | Reference implementation against the same AST |

Expression evaluation uses the classic stack discipline: evaluate left into `$t0`, push, evaluate right, pop into `$t1`, do the op. `/` and `mod` both issue one `div` and read the quotient from LO or the remainder from HI. The data segment holds variables as `.word`s. Syscalls 1/5/10/11 handle print_int / read_int / exit / newline.

## Tests

The suite covers the lexer (keywords, multi-char ops, comments, errors), the parser (precedence, control flow, error reporting), the codegen (data section, syscalls, labels, undeclared-variable detection), the interpreter (factorial, GCD, division-by-zero, stdin handling), and the `mod` operator through every stage, with its sign behaviour checked against the identity `(a / b) * b + (a mod b) = a`.

## Limits

- **A small language on purpose.** Integers only. No procedures or functions, no arrays, no strings, no types to declare.
- **The assembly is checked for structure, not by running it.** The tests assert on what the code generator emits, and the interpreter is what establishes a program's behaviour. Nothing in CI assembles the output and executes it.
- **It follows SPIM and MARS conventions:** a `.data` segment for variables and their system calls for reading, printing and exiting.
- **It does not run on [mips-emulator](https://github.com/forgehk/mips-emulator) yet.** That emulator has no data segment and no system calls, so it stops at the first `.data` line. Teaching it those, and then running every example through it in CI, is the next piece of work here.
- **No optimisation.** Every expression is evaluated through the stack, so the output is longer than it needs to be.

## Examples

- `examples/factorial.tiny`: iterative factorial
- `examples/fizzbuzz.tiny`: fizzbuzz with `mod`
- `examples/gcd.tiny`: Euclidean GCD

## License

MIT. See [LICENSE](LICENSE).
