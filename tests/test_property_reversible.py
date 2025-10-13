import pytest
from crz.compiler.parser import parse_text
from crz.compiler.passes import apply_reversible_pass
from crz.compiler.codegen_sim import codegen
from crz.simulator.simulator import Simulator


def generate_random_small_program():
    """Generate a random small reversible program."""
    import random
    ops = ["ADD", "SUB", "MUL", "DIV"]
    regs = ["R0", "R1", "R2", "R3"]
    program = "#[reversible]\nfn test_func() {\n"
    for _ in range(random.randint(1, 5)):
        op = random.choice(ops)
        rd = random.choice(regs)
        rs1 = random.choice(regs)
        rs2 = random.choice(regs)
        program += f"    {op} {rd}, {rs1}, {rs2};\n"
    program += "}\n"
    return program


@pytest.mark.parametrize("i", range(100))
def test_reversible_emulation(i):
    """Test that reversible emulation restores initial state."""
    program_text = generate_random_small_program()
    ast = parse_text(program_text)
    func = ast.declarations[0]
    optimized_func = apply_reversible_pass(func)
    # Replace the func in ast
    ast.declarations[0] = optimized_func
    ir = codegen(ast)

    simulator = Simulator()
    initial_regs = simulator.regs.copy()
    simulator.run_program(ir)
    final_regs = simulator.regs.copy()

    assert final_regs == initial_regs, f"State not restored for program {i}"
