"""
CRZ64I Microbenchmarks

Runs workloads and produces CSV report.
"""

import argparse
import csv
import time
import sys
from pathlib import Path

sys.path.insert(0, "../src")
from crz.simulator.simulator import Simulator
from crz.runtime.runtime import Runtime
from crz.config import Config


def run_workload(name: str, ops: list) -> dict:
    """Run a workload and return metrics."""
    config = Config()
    sim = Simulator(config)
    runtime = Runtime(sim)
    start_time = time.time()
    # Convert ops to format expected by runtime
    formatted_ops = [{"op": op["mnemonic"], "args": op["operands"]} for op in ops]
    runtime.run_with_hints(formatted_ops)
    end_time = time.time()
    cycles = len(ops)  # Approximate
    energy = sim.energy_used
    temp = max(sim.thermal_map.values()) if sim.thermal_map else 25.0
    return {"name": name, "cycles": cycles, "energy": energy, "temp": temp}


def main():
    """Run all workloads."""
    parser = argparse.ArgumentParser(description="Run CRZ64I microbenchmarks")
    parser.add_argument("--out", default="bench_results.csv", help="Output CSV file")
    args = parser.parse_args()

    workloads = {
        "ADD": [{"mnemonic": "ADD", "operands": ["r0", "r1", "r2"]}],
        "LOAD": [{"mnemonic": "LOAD", "operands": ["r0", "[r1]"]}],
        "STORE": [{"mnemonic": "STORE", "operands": ["r0", "[r1]"]}],
        "VDOT32": [{"mnemonic": "VDOT32", "operands": ["v0", "v1", "v2"]}],
        "FMA": [{"mnemonic": "FMA", "operands": ["r0", "r1", "r2", "r3"]}],
        "BRANCH": [{"mnemonic": "JMP", "operands": ["10"]}],
    }

    results = []
    for name, ops in workloads.items():
        result = run_workload(name, ops)
        results.append(result)

    # Write CSV
    with open(args.out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "cycles", "energy", "temp"])
        writer.writeheader()
        writer.writerows(results)

    # Assert ranges (example)
    for r in results:
        assert 0 < r["cycles"] < 100, f"Cycles out of range for {r['name']}"
        assert 0 < r["energy"] < 50, f"Energy out of range for {r['name']}"
        assert 20 < r["temp"] < 100, f"Temp out of range for {r['name']}"

    print(f"Benchmarks completed, results in {args.out}")


if __name__ == "__main__":
    main()
