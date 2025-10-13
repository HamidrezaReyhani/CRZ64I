# CRZ64I Compiler

## Pipeline

1. **Parsing**: Lark-based parser converts source to AST
2. **Semantic Analysis**: Validates attributes and constraints
3. **Dataflow Analysis**: Path-sensitive reversible checks
4. **Optimization Passes**: Fusion, reversible emulation, energy profiling
5. **Codegen**: Generates simulator IR or RISC-V text

## Passes

- **Fusion Pass**: Combines LOAD; ADD into FUSED_LOAD_ADD
- **Reversible Emulation**: Inserts SAVE_DELTA/RESTORE_DELTA
- **Energy Profile**: Annotates instructions with energy estimates

## API

```python
from crz.compiler.parser import parse
from crz.compiler.passes import run_passes
from crz.compiler.codegen_sim import codegen_sim

program = parse(code)
optimized = run_passes(program, ["fusion"], {})
ir = codegen_sim(optimized)
```

## Error Handling

Compiler reports errors with line/column info using rich console.
