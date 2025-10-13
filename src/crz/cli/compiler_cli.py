#!/usr/bin/env python3
"""CLI entrypoint for CRZ64I compiler."""


import argparse
import sys
import json
import csv
from pathlib import Path
from typing import Dict, Any
from crz.compiler.ast import Function
from rich.console import Console
from rich.progress import Progress
from crz.compiler.parser import parse
from crz.compiler.semantic import SemanticAnalyzer
from crz.compiler.dataflow import DataflowAnalyzer
from crz.compiler.passes import run_passes
from crz.compiler.codegen_sim import codegen as codegen_sim
from crz.simulator.simulator import Simulator
from crz.config import load_config

console = Console()


def main() -> int:
    from crz.config import load_config

    config = load_config("config.json")
    parser = argparse.ArgumentParser(description="CRZ64I Compiler")
    subparsers = parser.add_subparsers(dest="command")

    compile_parser = subparsers.add_parser("compile", help="Compile to IR")
    compile_parser.add_argument("input", help="Input CRZ64I file")
    compile_parser.add_argument("-o", "--output", help="Output IR JSON file")

    run_parser = subparsers.add_parser("run", help="Compile and run simulation")
    run_parser.add_argument("input", help="Input CRZ64I file")
    run_parser.add_argument(
        "-n", "--iterations", type=int, default=1, help="Iterations"
    )

    bench_parser = subparsers.add_parser("bench", help="Run benchmarks")
    bench_parser.add_argument("dir", help="Directory with .crz files")
    bench_parser.add_argument(
        "--out", help="Output CSV file", default="bench_results.csv"
    )

    args = parser.parse_args()

    if args.command == "compile":
        try:
            code = Path(args.input).read_text()
            program = parse(code)
            # Semantic check
            analyzer = SemanticAnalyzer()
            issues = analyzer.analyze(program)
            if any(i["type"] == "error" for i in issues):
                for issue in issues:
                    console.print(f"[red]{issue['type']}: {issue['message']}[/red]")
                return 1
            # Dataflow check
            for decl in program.declarations:
                if isinstance(decl, Function):
                    df_analyzer = DataflowAnalyzer(decl)
                    df_issues = df_analyzer.analyze()
                    issues.extend(df_issues)
            if any(i["type"] == "error" for i in issues):
                for issue in issues:
                    console.print(f"[red]{issue['type']}: {issue['message']}[/red]")
                return 1
            # Passes
            compile_pass_config: Dict[str, Any] = {}
            optimized = run_passes(
                program,
                ["fusion", "reversible_emulation", "energy_profile"],
                compile_pass_config,
            )
            ir = codegen_sim(optimized)
            ir_json = [
                {
                    "op": op.op,
                    "args": op.args,
                    "fused": op.fused,
                    "metadata": op.metadata,
                }
                for op in ir
            ]
            output = args.output or "out.ir.json"
            with open(output, "w") as f:
                json.dump(ir_json, f, indent=2)
            console.print(f"[green]Compiled to {output}[/green]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            return 1

    elif args.command == "run":
        try:
            run_config = load_config("config.json")
            code = Path(args.input).read_text()
            program = parse(code)
            run_pass_config: Dict[str, Any] = {}
            optimized = run_passes(
                program, ["fusion", "energy_profile"], run_pass_config
            )
            sim_ir = codegen_sim(optimized)
            sim = Simulator(run_config)
            with Progress() as progress:
                task = progress.add_task("Simulating...", total=args.iterations)
                total_cycles = 0
                total_energy = 0.0
                max_temp = 0.0
                for _ in range(args.iterations):
                    result = sim.run(sim_ir, metrics=True)
                    if result is not None:
                        cycles, energy, temp = result
                        total_cycles += cycles
                        total_energy += energy
                        max_temp = max(max_temp, temp)
                    progress.advance(task)
            console.print(
                f"Cycles: {total_cycles}, Energy: {total_energy:.2f}, Max Temp: {max_temp:.2f}"
            )
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            return 1

    elif args.command == "bench":
        try:
            bench_config = load_config("config.json")
            dir_path = Path(args.dir)
            files = list(dir_path.glob("*.crz"))
            results = []
            with Progress() as progress:
                task = progress.add_task("Benchmarking...", total=len(files))
                for file in files:
                    code = file.read_text()
                    program = parse(code)
                    bench_pass_config: Dict[str, Any] = {}
                    optimized = run_passes(
                        program, ["fusion", "energy_profile"], bench_pass_config
                    )
                    sim_ir = codegen_sim(optimized)
                    sim = Simulator(bench_config)
                    result = sim.run(sim_ir, metrics=True)
                    if result is not None:
                        cycles, energy, temp = result
                    else:
                        cycles, energy, temp = 0, 0.0, 25.0
                    results.append(
                        {
                            "name": file.stem,
                            "cycles": cycles,
                            "energy": energy,
                            "temp": temp,
                        }
                    )
                    progress.advance(task)
            with open(args.out, "w", newline="") as f:
                writer = csv.DictWriter(
                    f, fieldnames=["name", "cycles", "energy", "temp"]
                )
                writer.writeheader()
                writer.writerows(results)
            console.print(f"[green]Benchmarks written to {args.out}[/green]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            return 1

    else:
        parser.print_help()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
