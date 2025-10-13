import random
from crz.compiler.parser import parse
from crz.compiler.codegen_sim import codegen
from crz.simulator.simulator import Simulator


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


def fuzz_simulator(iterations=100, max_len=50):
    """Fuzz the simulator with random programs."""
    sim = Simulator()
    crashes = 0
    for i in range(iterations):
        prog = generate_random_program(max_len)
        try:
            ast = parse(prog)
            ir = codegen(ast)
            sim.run_program(ir)
        except Exception as e:
            print(f"Crash on iteration {i}: {e}")
            crashes += 1
            if crashes > 10:
                break
    if crashes == 0:
        print("No crashes found.")
    else:
        print(f"Found {crashes} crashes.")


if __name__ == "__main__":
    fuzz_simulator()
