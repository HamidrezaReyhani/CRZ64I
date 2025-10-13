# tests.py
# Benchmarks for CRZ64I

import time
from grammar import CRZParser
from compiler import CRZCompiler
from assembler import CRZAssembler
from simulator import CRZSimulator

def benchmark(code):
    parser = CRZParser()
    instructions, labels = parser.parse(code)
    compiler = CRZCompiler()
    optimized = compiler.compile(instructions)
    assembler = CRZAssembler()
    bytecode = assembler.assemble(optimized, labels)
    simulator = CRZSimulator()
    start = time.time()
    cycles, energy, temperature = simulator.run(optimized)  # Run on instructions, not bytecode for simplicity
    end = time.time()
    print(f"Cycles: {cycles}, Energy: {energy}, Temperature: {temperature:.2f}, Time: {end - start:.4f}s")
    return cycles, energy, temperature

if __name__ == '__main__':
    # Microbenchmarks for critical instructions
    microbenchmarks = {
        'ADD': "ADD R1, R0, 10\nHALT",
        'LOAD': "LOAD R1, [R0]\nHALT",
        'STORE': "STORE R0, [R1]\nHALT",
        'VDOT32': "VDOT32 R1, R2, R3\nHALT",
        'FMA': "FMA R1, R2, R3, R4\nHALT",
        'BR_IF': "BR_IF LT R0, 10, _end\nHALT\n_end: NOP",
    }
    
    print("Baseline Microbenchmarks:")
    for instr, code in microbenchmarks.items():
        print(f"\n{instr}:")
        benchmark(code)
    
    # Full Workload: Simple GEMM (Matrix Multiply Accumulate)
    print("\nFull Workload Benchmark: GEMM")
    gemm_code = """
    # Simple GEMM: C += A * B for one element
    LOAD R1, [R0];  # Load A
    LOAD R2, [R1];  # Load B
    FMA R3, R1, R2, R3;  # C += A * B
    STORE R3, [R4];  # Store C
    HALT;
    """
    benchmark(gemm_code)
    
    # Example full benchmark
    print("\nFull Example Benchmark:")
    code = """
    ADD R1, R0, 10;
    _loop:
    LOAD R2, [R1];
    VDOT32 R3, R2, R4;
    BR_IF LT R1, 20, _loop;
    HALT;
    """
    benchmark(code)

    # Test Disassembler
    print("\nTesting Disassembler:")
    test_code = "ADD R1, R0, 10\nHALT"
    parser = CRZParser()
    instructions, labels = parser.parse(test_code)
    compiler = CRZCompiler()
    optimized = compiler.compile(instructions)
    assembler = CRZAssembler()
    bytecode = assembler.assemble(optimized, labels)
    disassembled = assembler.disassemble(bytecode)
    print(f"Original: {test_code}")
    print(f"Disassembled: {'; '.join(disassembled)}")

    # Test Reversible Undo
    print("\nTesting Reversible Undo:")
    rev_code = "ADD R1, R0, 5\nSAVE_DELTA R1, R0\nADD R1, R0, 10\nRESTORE_DELTA R1, R0\nHALT"
    parser = CRZParser()
    instructions, labels = parser.parse(rev_code)
    compiler = CRZCompiler()
    optimized = compiler.compile(instructions)
    simulator = CRZSimulator()
    cycles, energy, temperature = simulator.run(optimized)
    print(f"After reversible ops: R1={simulator.regs[1]}, Cycles: {cycles}")
    simulator.reverse_step()  # Undo last op
    print(f"After undo: R1={simulator.regs[1]}")

    # Test Edge Cases
    print("\nTesting Edge Cases:")
    try:
        invalid_code = "INVALID R1, R0\nHALT"
        parser = CRZParser()
        instructions, labels = parser.parse(invalid_code)
        compiler = CRZCompiler()
        optimized = compiler.compile(instructions)
        simulator = CRZSimulator()
        cycles, energy, temperature = simulator.run(optimized)
        print("Invalid opcode handled.")
    except Exception as e:
        print(f"Invalid opcode error: {e}")

    # Optimization Verification: With and without fusion
    print("\nOptimization Verification:")
    opt_code = "LOAD R1, [R0]\nADD R2, R1, R3\nSTORE R2, [R4]\nHALT"
    # With fusion
    parser = CRZParser()
    instructions, labels = parser.parse(opt_code)
    compiler = CRZCompiler()
    optimized = compiler.compile(instructions)
    simulator = CRZSimulator()
    cycles_with, energy_with, temp_with = simulator.run(optimized)
    print(f"With fusion: Cycles={cycles_with}, Energy={energy_with}")
    # Without fusion
    no_fusion_compiler = CRZCompiler()
    no_fusion_compiler.passes = []  # No passes
    optimized_no = no_fusion_compiler.compile(instructions)
    simulator_no = CRZSimulator()
    cycles_no, energy_no, temp_no = simulator_no.run(optimized_no)
    print(f"Without fusion: Cycles={cycles_no}, Energy={energy_no}")
