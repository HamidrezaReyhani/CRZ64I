#!/usr/bin/env python3
"""
Measurement harness for CRZ64I micro_add benchmark.

Runs the micro_add program in uncompiled and compiled modes,
collecting metrics: cycles, energy, wall-clock time, temperature.
"""

import sys
import argparse
import time
import statistics
import csv
import os

# Add src to path
sys.path.insert(0, 'src')

# Robust imports with fallbacks
try:
    from crz.compiler.parser import Parser, parse_text
except ImportError:
    try:
        from crz.compiler import parser as crzparser
        Parser = crzparser.Parser
        parse_text = crzparser.parse_text
    except ImportError:
        try:
            from parser import Parser, parse_text
        except ImportError:
            raise ImportError("Could not import Parser")





try:
    from crz.compiler.codegen_sim import codegen
except ImportError:
    # Minimal lowering fallback
    def codegen(program):
        from crz.compiler.ast import Instr
        ops = []
        for decl in program.declarations:
            if hasattr(decl, 'body'):
                for stmt in decl.body:
                    if isinstance(stmt, Instr):
                        ops.append({'op': stmt.mnemonic, 'args': stmt.operands, 'fused': False})
        return ops

# Import Simulator
try:
    from crz.simulator.simulator import Simulator
except ImportError:
    try:
        from simulator import Simulator
    except ImportError:
        raise ImportError("Could not import Simulator")


def load_and_substitute(path, n):
    """Load CRZ source and substitute N with the given value."""
    import re
    with open(path, 'r') as f:
        lines = f.readlines()
    # Remove lines starting with # and containing =
    lines = [line for line in lines if not (line.strip().startswith('#') and '=' in line.strip())]
    code = ''.join(lines)
    # Replace N in the code
    code = code.replace('N', str(n))
    # Replace uppercase R with lowercase r for registers (e.g., R1 -> r1)
    code = re.sub(r'\bR(\d+)\b', r'r\1', code)
    return code


def run_uncompiled(code, runs, verbose=False):
    """Run uncompiled mode: parse -> codegen -> simulate."""
    try:
        program = parse_text(code)
        # For uncompiled, do NOT apply fusion
        ops = codegen(program, apply_fusion=False)
    except Exception as e:
        print(f"Error in uncompiled parsing/codegen: {e}")
        raise

    results = []
    states = []
    for run_id in range(runs):
        sim = Simulator()
        start = time.perf_counter()
        try:
            cycles, energy, temp = sim.run(ops)
        except Exception as e:
            print(f"Error in uncompiled simulation run {run_id}: {e}")
            raise
        wall = time.perf_counter() - start
        results.append((cycles, energy, temp, wall))
        states.append(sim.get_state())
        if verbose:
            print(f"Uncompiled run {run_id}: op_counts={sim._op_counts}, energy_breakdown={ {op: count * sim.config.energy.get(op, 1.0) for op, count in sim._op_counts.items()} }")
    return results, states


def run_compiled(code, runs, verbose=False):
    """Run compiled mode: CRZCompiler.compile -> simulate."""
    try:
        program = parse_text(code)
        from crz.compiler.passes import run_passes
        compiled_program = run_passes(program, ['fusion'])
        ops = codegen(compiled_program)
    except Exception as e:
        print(f"Error in compiled compilation: {e}")
        raise

    results = []
    states = []
    for run_id in range(runs):
        sim = Simulator()
        start = time.perf_counter()
        try:
            cycles, energy, temp = sim.run(ops)
        except Exception as e:
            print(f"Error in compiled simulation run {run_id}: {e}")
            raise
        wall = time.perf_counter() - start
        results.append((cycles, energy, temp, wall))
        states.append(sim.get_state())
        if verbose:
            print(f"Compiled run {run_id}: op_counts={sim._op_counts}, energy_breakdown={ {op: count * sim.config.energy.get(op, 1.0) for op, count in sim._op_counts.items()} }")
    return results, states


def main():
    parser = argparse.ArgumentParser(description="Measure CRZ64I micro_add benchmark")
    parser.add_argument('--n', type=int, default=100000, help='Number of iterations')
    parser.add_argument('--runs', type=int, default=5, help='Number of runs per mode')
    parser.add_argument('--out', type=str, default='results_micro_add.csv', help='Output CSV path')
    parser.add_argument('--verbose', action='store_true', help='Print detailed op counts and energy breakdown')
    args = parser.parse_args()

    code = load_and_substitute('examples/micro_add.crz', args.n)

    uncompiled_results, uncompiled_states = run_uncompiled(code, args.runs, args.verbose)
    compiled_results, compiled_states = run_compiled(code, args.runs, args.verbose)

    # Compute means and stddevs
    uncompiled_means = [statistics.mean([r[i] for r in uncompiled_results]) for i in range(4)]
    compiled_means = [statistics.mean([r[i] for r in compiled_results]) for i in range(4)]

    # Semantic equivalence check
    uc_state = uncompiled_states[0]
    c_state = compiled_states[0]
    diffs = []
    for r in sorted(set(list(uc_state['regs'].keys()) + list(c_state['regs'].keys()))):
        a = uc_state['regs'].get(r, 0)
        b = c_state['regs'].get(r, 0)
        if isinstance(a, float) or isinstance(b, float):
            if abs(a - b) > 1e-9:
                diffs.append(f"R{r}: {a} != {b}")
        else:
            if a != b:
                diffs.append(f"R{r}: {a} != {b}")
    for addr in sorted(set(list(uc_state['memory'].keys()) + list(c_state['memory'].keys()))):
        a = uc_state['memory'].get(addr, 0)
        b = c_state['memory'].get(addr, 0)
        if a != b:
            diffs.append(f"MEM[{addr}]: {a} != {b}")
    if diffs:
        print("SEMANTIC MISMATCH between uncompiled and compiled:")
        for d in diffs[:200]:
            print(d)
        raise SystemExit(2)
    else:
        print("Semantic match: states identical.")

    # Improvements: (compiled - uncompiled) / uncompiled * 100
    improvements = [
        (compiled_means[i] - uncompiled_means[i]) / uncompiled_means[i] * 100 if uncompiled_means[i] != 0 else 0
        for i in range(4)
    ]

    # Print human-readable summary
    print(f"Microbench: micro_add N={args.n} runs={args.runs}")
    print(f"UNCOMPILED mean cycles={uncompiled_means[0]:.0f}, energy={uncompiled_means[1]:.2f}J, temp={uncompiled_means[2]:.1f}, wall={uncompiled_means[3]:.3f}s")
    print(f"COMPILED mean cycles={compiled_means[0]:.0f}, energy={compiled_means[1]:.2f}J, temp={compiled_means[2]:.1f}, wall={compiled_means[3]:.3f}s")
    print(f"Improvement (compiled vs uncompiled): cycles {improvements[0]:.1f}%, energy {improvements[1]:.1f}%, temp {improvements[2]:.1f}%, wall {improvements[3]:.1f}%")

    # Save CSV
    with open(args.out, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['mode', 'run_id', 'cycles', 'energy', 'temp', 'wall_clock_s'])
        for i, r in enumerate(uncompiled_results):
            writer.writerow(['uncompiled', i+1] + list(r))
        for i, r in enumerate(compiled_results):
            writer.writerow(['compiled', i+1] + list(r))

    print(f"CSV saved to {args.out}")


if __name__ == '__main__':
    main()




