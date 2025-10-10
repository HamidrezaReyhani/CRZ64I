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
        'ADD': "ADD R1, R0, 10; HALT;",
        'LOAD': "LOAD R1, [R0]; HALT;",
        'STORE': "STORE R0, [R1]; HALT;",
        'VDOT32': "VDOT32 R1, R2, R3; HALT;",
        'FMA': "FMA R1, R2, R3, R4; HALT;",
        'BR_IF': "BR_IF LT R0, 10, _end; HALT; _end: NOP;",
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
