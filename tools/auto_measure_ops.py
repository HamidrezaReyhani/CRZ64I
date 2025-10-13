#!/usr/bin/env python3
"""
Automated measurement script for all CRZ64I opcodes.

Generates C benchmarks for each opcode, compiles, runs with HW measurement,
collects energy and cycles, outputs JSON.
"""

import os
import sys
import json
import subprocess
import tempfile
import shutil

# Add src to path
sys.path.insert(0, "src")

# Mapping opcode to C body for benchmarking
OP_BENCH = {
    # Arithmetic
    "ADD": "c = a + b; a = c;",
    "SUB": "c = a - b; a = c;",
    "MUL": "c = a * b; a = c;",
    "DIV": "c = a / (b + 1); a = c;",  # avoid div by zero
    "AND": "c = a & b; a = c;",
    "OR": "c = a | b; a = c;",
    "XOR": "c = a ^ b; a = c;",
    "SHL": "c = a << (b % 32); a = c;",
    "SHR": "c = a >> (b % 32); a = c;",
    "POPCNT": "c = __builtin_popcount(a); a = c;",
    # Memory
    "LOAD": "c = A[i % size]; a += c;",
    "STORE": "A[i % size] = a; a = c;",
    # Floating point (if supported, else skip)
    "FADD": "c = a + b; a = c;",  # assume float
    "FSUB": "c = a - b; a = c;",
    "FMUL": "c = a * b; a = c;",
    "FMA": "c = a * b + c; a = c;",
    # Vector (simulate with arrays)
    "VADD": "for(int j=0;j<4;j++) C[j] = A[j] + B[j]; a = C[0];",
    "VMUL": "for(int j=0;j<4;j++) C[j] = A[j] * B[j]; a = C[0];",
    # Control flow - harder, use simple if
    "BR_IF": "if (a > 0) { c = b; } else { c = a; } a = c;",
    # Others - use nop equivalent
    "NOP": "a = a;",
    "HALT": "a = a;",
    "JMP": "a = a;",
    "CALL": "a = a;",
    "RET": "a = a;",
    "BR": "a = a;",
    "YIELD": "a = a;",
    "TRAP": "a = a;",
    # Memory ops
    "LOADF": "c = A[i % size]; a += c;",  # assume float
    "STOREF": "A[i % size] = a; a = c;",
    "ATOMIC_INC": "A[i % size]++; a = A[0];",
    "DMA_START": "a = a;",  # hard to bench
    "CACHE_LOCK": "a = a;",
    "PREFETCH": "a = a;",
    # Vector more
    "VSTORE": "for(int j=0;j<4;j++) C[j] = A[j]; a = C[0];",
    "VLOAD": "for(int j=0;j<4;j++) C[j] = A[j]; a = C[0];",
    "VSUB": "for(int j=0;j<4;j++) C[j] = A[j] - B[j]; a = C[0];",
    "VDOT32": "c = 0; for(int j=0;j<4;j++) c += A[j] * B[j]; a = c;",
    "VSHL": "for(int j=0;j<4;j++) C[j] = A[j] << 1; a = C[0];",
    "VSHR": "for(int j=0;j<4;j++) C[j] = A[j] >> 1; a = C[0];",
    "VFMA": "for(int j=0;j<4;j++) C[j] = A[j] * B[j] + C[j]; a = C[0];",
    "VREDUCE_SUM": "c = 0; for(int j=0;j<4;j++) c += A[j]; a = c;",
    # Atomic
    "LOCK": "a = a;",
    "UNLOCK": "a = a;",
    "CMPXCHG": "a = a;",
    "FENCE": "a = a;",
    # System
    "SET_PWR_MODE": "a = a;",
    "GET_PWR_STATE": "a = a;",
    "THERM_READ": "a = a;",
    "SET_THERM_POLICY": "a = a;",
    "SLEEP": "a = a;",
    "FAST_PATH_ENTER": "a = a;",
    # Reversible
    "SAVE_DELTA": "a = a;",
    "RESTORE_DELTA": "a = a;",
    "REV_ADD": "c = a + b; a = c;",
    "REV_SWAP": "c = a; a = b; b = c;",
    "ADIABATIC_START": "a = a;",
    "ADIABATIC_STOP": "a = a;",
    # Crypto
    "CRC32": "c = a ^ b; a = c;",  # simple
    "HASH_INIT": "a = a;",
    "HASH_UPDATE": "a = a;",
    "HASH_FINAL": "a = a;",
    # Misc
    "PROFILE_START": "a = a;",
    "PROFILE_STOP": "a = a;",
    "TRACE": "a = a;",
    "EXTENSION": "a = a;",
}

C_TEMPLATE = """#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
int main(int argc, char **argv){
    long N = argc>1 ? atol(argv[1]) : 100000000;
    long size = argc>2 ? atol(argv[2]) : 1000000;
    int *A = NULL;
    float *Af = NULL;
    int *B = NULL;
    int *C = NULL;
    if (size > 0) {
        A = malloc(size * sizeof(int));
        Af = malloc(size * sizeof(float));
        B = malloc(size * sizeof(int));
        C = malloc(size * sizeof(int));
        for(long i=0;i<size;i++) {
            A[i]=i;
            Af[i]=(float)i;
            B[i]=i+1;
            C[i]=0;
        }
    }
    volatile int a=1, b=2, c=0;
    for(long i=0;i<N;i++){
        {body}
    }
    printf("%d\\n", c);
    if (A) free(A);
    if (Af) free(Af);
    if (B) free(B);
    if (C) free(C);
    return 0;
}
"""


def generate_c_bench(op, body):
    code = C_TEMPLATE.replace("{body}", body)
    return code


def compile_and_measure(op, body, N=10000000, size=1000000):
    code = generate_c_bench(op, body)
    with tempfile.TemporaryDirectory() as tmpdir:
        cfile = os.path.join(tmpdir, f"{op}.c")
        exe = os.path.join(tmpdir, op)
        with open(cfile, "w") as f:
            f.write(code)
        # Compile
        subprocess.run(["gcc", "-O2", cfile, "-o", exe], check=True)
        # Measure
        result = subprocess.run(
            [sys.executable, "tools/measure_hw.py", exe, str(N), str(size)],
            capture_output=True,
            text=True,
        )
        lines = result.stdout.strip().split("\n")
        energy = None
        cycles = None
        for line in lines:
            if "energy_J:" in line:
                energy = float(line.split("energy_J:")[1].strip())
            if "cycles:" in line:
                cycles = int(line.split("cycles:")[1].strip())
        return energy, cycles


def main():
    results = {}
    for op, body in OP_BENCH.items():
        print(f"Measuring {op}...")
        try:
            energy, cycles = compile_and_measure(op, body)
            results[op] = {"energy_J": energy, "cycles": cycles}
        except Exception as e:
            print(f"Failed {op}: {e}")
            results[op] = {"energy_J": None, "cycles": None}
    with open("bench/op_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Results saved to bench/op_results.json")


if __name__ == "__main__":
    main()
