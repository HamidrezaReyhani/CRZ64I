from ..compiler.parser import parse_text
from ..compiler.passes import run_passes
from ..compiler.codegen_sim import codegen
from ..simulator.simulator import Simulator


def run_roundtrip(filename):
    with open(filename, "r") as f:
        code = f.read()
    ast = parse_text(code)
    ir = codegen(ast)
    simulator = Simulator()
    simulator.run_program(ir)
    original_regs = simulator.regs.copy()

    fused_ast = run_passes(ast, ["fusion"], {})
    fused_ir = codegen(fused_ast)
    simulator2 = Simulator()
    simulator2.run_program(fused_ir)
    fused_regs = simulator2.regs.copy()

    return original_regs == fused_regs
