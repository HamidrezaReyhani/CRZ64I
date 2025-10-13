# harness.py
# CRZ64I Microbenchmark Harness

import time
import subprocess
import psutil
import os
from instructions import INSTRUCTIONS

class BenchmarkHarness:
    def __init__(self):
        self.results = {}
        self.rapl_available = self.check_rapl_support()

    def check_rapl_support(self):
        """Check if RAPL (Running Average Power Limit) is available"""
        try:
            with open('/sys/class/powercap/intel-rapl/intel-rapl:0/energy_uj', 'r') as f:
                return True
        except (FileNotFoundError, PermissionError):
            return False

    def measure_energy(self, func, *args, **kwargs):
        """Measure energy consumption using RAPL"""
        if not self.rapl_available:
            return 0.0

        energy_file = '/sys/class/powercap/intel-rapl/intel-rapl:0/energy_uj'
        with open(energy_file, 'r') as f:
            start_energy = int(f.read().strip())

        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()

        with open(energy_file, 'r') as f:
            end_energy = int(f.read().strip())

        energy_used = (end_energy - start_energy) / 1e6  # Convert to Joules
        time_taken = end_time - start_time

        return {
            'energy_joules': energy_used,
            'time_seconds': time_taken,
            'power_watts': energy_used / time_taken if time_taken > 0 else 0,
            'result': result
        }

    def measure_perf(self, func, *args, **kwargs):
        """Measure performance using perf"""
        try:
            # Use perf stat to measure cycles, instructions, etc.
            cmd = ['perf', 'stat', '-e', 'cycles,instructions,cache-misses', '--', 'python3', '-c', f'from harness import *; {func.__name__}(*args, **kwargs)']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return self.parse_perf_output(result.stdout)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return {'cycles': 0, 'instructions': 0, 'cache_misses': 0}

    def parse_perf_output(self, output):
        """Parse perf stat output"""
        lines = output.split('\n')
        results = {}
        for line in lines:
            if 'cycles' in line:
                results['cycles'] = int(line.split()[0].replace(',', ''))
            elif 'instructions' in line:
                results['instructions'] = int(line.split()[0].replace(',', ''))
            elif 'cache-misses' in line:
                results['cache_misses'] = int(line.split()[0].replace(',', ''))
        return results

    def run_microbenchmark(self, instruction, iterations=1000000):
        """Run microbenchmark for a specific instruction"""
        print(f"Running microbenchmark for {instruction}")

        # Generate test code for the instruction
        test_code = self.generate_test_code(instruction, iterations)

        # Execute and measure
        energy_data = self.measure_energy(self.execute_code, test_code)
        perf_data = self.measure_perf(self.execute_code, test_code)

        result = {
            'instruction': instruction,
            'iterations': iterations,
            'energy': energy_data,
            'performance': perf_data,
            'cpi': perf_data.get('cycles', 0) / perf_data.get('instructions', 1),
            'ipc': perf_data.get('instructions', 0) / perf_data.get('cycles', 1)
        }

        self.results[instruction] = result
        return result

    def generate_test_code(self, instruction, iterations):
        """Generate test assembly code for benchmarking"""
        if instruction not in INSTRUCTIONS:
            return ""

        info = INSTRUCTIONS[instruction]
        operands = info['operands']

        # Generate simple loop with the instruction
        code = f"""
#[realtime]
fn benchmark_{instruction.lower()}() {{
    let iterations = {iterations};
    let counter = 0;
    for i in 0..iterations {{
"""

        # Add the instruction with dummy operands
        if operands >= 1:
            code += f"        {instruction} R0"
        if operands >= 2:
            code += ", R1"
        if operands >= 3:
            code += ", R2"
        if operands >= 4:
            code += ", R3"
        code += ";\n"

        code += """
        counter = counter + 1;
    }
}
"""
        return code

    def execute_code(self, code):
        """Execute the generated code (placeholder for actual execution)"""
        # In real implementation, this would compile and run the code
        # For now, simulate execution time
        time.sleep(0.001)  # Simulate some execution time
        return "executed"

    def run_baseline(self, critical_instructions=None):
        """Run baseline benchmarks for critical instructions"""
        if critical_instructions is None:
            critical_instructions = ['ADD', 'LOAD', 'STORE', 'VDOT32', 'FMA', 'BR_IF']

        baseline_results = {}
        for instr in critical_instructions:
            baseline_results[instr] = self.run_microbenchmark(instr)

        return baseline_results

    def compare_with_baseline(self, new_results):
        """Compare new results with baseline"""
        if not hasattr(self, 'baseline'):
            print("No baseline available for comparison")
            return

        comparison = {}
        for instr, result in new_results.items():
            if instr in self.baseline:
                baseline = self.baseline[instr]
                comparison[instr] = {
                    'energy_improvement': (baseline['energy']['energy_joules'] - result['energy']['energy_joules']) / baseline['energy']['energy_joules'] * 100,
                    'latency_improvement': (baseline['performance']['cycles'] - result['performance']['cycles']) / baseline['performance']['cycles'] * 100,
                    'cpi_change': result['cpi'] - baseline['cpi']
                }

        return comparison

    def generate_report(self):
        """Generate benchmark report"""
        report = "# CRZ64I Benchmark Report\n\n"
        report += "| Instruction | CPI | Energy (J) | Power (W) | Cache Misses |\n"
        report += "|-------------|-----|-------------|-----------|---------------|\n"

        for instr, result in self.results.items():
            energy = result['energy']
            perf = result['performance']
            report += f"| {instr} | {result['cpi']:.2f} | {energy['energy_joules']:.4f} | {energy['power_watts']:.2f} | {perf.get('cache_misses', 0)} |\n"

        return report

    def save_results(self, filename='benchmark_results.json'):
        """Save results to file"""
        import json
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)


# Example usage
if __name__ == "__main__":
    harness = BenchmarkHarness()

    print("Running baseline benchmarks...")
    baseline = harness.run_baseline()
    harness.baseline = baseline

    print("Running optimized benchmarks...")
    # Simulate optimized results
    optimized = harness.run_baseline(['ADD', 'LOAD'])  # Example

    comparison = harness.compare_with_baseline(optimized)
    print("Comparison:", comparison)

    report = harness.generate_report()
    print(report)

    harness.save_results()
