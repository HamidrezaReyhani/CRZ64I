# CRZ64I

A Python implementation of the CRZ64I specification, an energy-efficient instruction set architecture with attributes for fusion, reversibility, and thermal management.

## Quickstart

Install from source:
```bash
pip install -e .
```

Compile and run a CRZ64I program:
```bash
crzc compile examples/fibonacci.crz -o fib.ir.json
crzsim run fib.ir.json --report results.csv
```

## Installation

### From Source
```bash
git clone https://github.com/your-repo/crz64i.git
cd crz64i
pip install -e .
```

### From PyPI (future)
```bash
pip install crz64i
```

## Usage

### Compiler CLI (crzc)
- Compile CRZ64I source to simulator IR:
  ```bash
  crzc compile input.crz -o output.ir.json
  ```
- Run end-to-end (compile + simulate):
  ```bash
  crzc run input.crz
  ```
- Benchmark examples:
  ```bash
  crzc bench examples/ --out benchmark.csv
  ```

### Simulator CLI (crzsim)
- Simulate IR with metrics:
  ```bash
  crzsim run input.ir.json --report out.csv
  ```
- Limit cycles:
  ```bash
  crzsim run input.ir.json --n 1000
  ```

## Architecture

CRZ64I supports attributes like `#[fusion]`, `#[reversible]`, `#[no_erase]`, `#[power="low"]`, `#[realtime]`, `#[thermal_hint]` for energy-aware programming.

Pipeline: Source -> Parse -> AST -> Semantic Analysis -> Dataflow (CFG) -> Optimization Passes (Fusion, Reversible Emulation, Energy Profiling) -> Codegen (Simulator IR or RISC-V Text) -> Runtime/Simulator (Cycle/Energy/Thermal Models).

```mermaid
graph TD
    A[CRZ64I Source] --> B[Parser (Lark)]
    B --> C[AST]
    C --> D[Semantic Analyzer]
    D --> E[Dataflow Analyzer]
    E --> F[Optimization Passes]
    F --> G[Codegen]
    G --> H[Simulator/Runtime]
    H --> I[Metrics: Cycles, Joules, Temp]
```

## Examples

- `examples/fibonacci.crz`: Computes Fibonacci(10)=55 iteratively.
- `examples/gemm.crz`: Matrix multiplication with vector ops.
- `examples/micro_add.crz`: Simple ADD loop.

## Development

### Setup
```bash
pip install -e .[dev]  # Includes mypy, black
```

### Run Tests
```bash
pytest
```

### Lint and Type Check
```bash
black .
mypy src
```

### Benchmarks
```bash
python -m bench.microbench
```

To run the micro_add benchmark comparing uncompiled vs compiled modes:
```bash
python tools/measure_micro_add.py --n 10000 --runs 5 --out results.csv
```

## Contributing

1. Fork the repo.
2. Create a feature branch.
3. Make changes, add tests.
4. Run `pytest`, `black --check .`, `mypy src`.
5. Submit PR.

See `CONTRIBUTING.md` for details.

## License

OpenLogic Permissive License. See `LICENSE`.
# CRZ64I
