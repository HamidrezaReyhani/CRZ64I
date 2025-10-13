import random
import argparse
import time
from lark import Lark
from lark.exceptions import LarkError
from crz.compiler.parser import parse
from crz.compiler.codegen_sim import codegen


def fuzz_parser(grammar_file, iterations=1000, timeout=0.1):
    """Fuzz the parser with random inputs."""
    with open(grammar_file, "r") as f:
        grammar = f.read()
    parser = Lark(
        grammar,
        start="program",
        parser="earley",
        lexer="dynamic",
        propagate_positions=True,
        cache=False,
    )
    crashes = 0
    for i in range(iterations):
        # Generate random string
        length = random.randint(1, 100)
        txt = "".join(
            random.choice(
                "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 \n\t{}();[],."
            )
            for _ in range(length)
        )
        try:
            parser.parse(txt)
        except LarkError:
            pass  # Expected
        except Exception as e:
            print(f"Crash on iteration {i}: {e}")
            crashes += 1
            if crashes > 10:  # Stop after too many crashes
                break
    if crashes == 0:
        print("No crashes found.")
    else:
        print(f"Found {crashes} crashes.")


def generate_random_program(max_len=50):
    """Generate a random CRZ program."""
    ops = ["ADD", "SUB", "MUL", "DIV", "MOV", "CMP", "JMP", "JZ", "JNZ", "CALL", "RET"]
    regs = [f"R{i}" for i in range(8)]
    labels = [f"label{i}" for i in range(5)]

    program = []
    program.append("#[fusion]")
    program.append("fn fuzz_func() {")

    for _ in range(random.randint(1, max_len)):
        op = random.choice(ops)
        if op in ["ADD", "SUB", "MUL", "DIV"]:
            args = [random.choice(regs), random.choice(regs), random.choice(regs)]
        elif op == "MOV":
            args = [random.choice(regs), random.choice(regs)]
        elif op == "CMP":
            args = [random.choice(regs), random.choice(regs)]
        elif op in ["JMP", "JZ", "JNZ", "CALL"]:
            args = [random.choice(labels)]
        elif op == "RET":
            args = []
        program.append(f"    {op} {', '.join(args)};")

    program.append("}")
    return "\n".join(program)


def main():
    parser = argparse.ArgumentParser(
        description="Fuzz CRZ compiler with random programs."
    )
    parser.add_argument(
        "--count", type=int, default=10, help="Number of programs to generate"
    )
    parser.add_argument(
        "--max_len", type=int, default=50, help="Max operations per program"
    )
    args = parser.parse_args()

    for i in range(args.count):
        prog = generate_random_program(args.max_len)
        print(f"Generated program {i+1}:")
        print(prog)
        print()
        try:
            # Try to parse and compile
            ast = parse(prog)
            ir = codegen(ast)
            print(f"Program {i+1} parsed and compiled successfully, IR len: {len(ir)}")
        except Exception as e:
            print(f"Program {i+1} failed: {e}")
        print("-" * 50)


if __name__ == "__main__":
    main()
