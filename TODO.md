# TODO: Fix FUSED_LOAD_ADD Semantics Preservation

## Information Gathered
- **Problem**: Current fusion bypasses LOAD destination (r1), causing semantic mismatch between uncompiled and compiled versions. Uncompiled writes to r1, compiled does not.
- **Files Involved**:
  - `src/crz/compiler/passes.py`: Contains fusion logic in `apply_fusion_pass_safe`. Currently builds fused_args as [add_dst, load_addr, imm] for LOAD+ADD.
  - `src/crz/simulator/simulator.py`: Handles FUSED_LOAD_ADD with 3 operands (rd, addr, imm), setting rd = memory[addr] + imm.
  - `examples/micro_add.crz`: Test case with LOAD r1, [a+i]; ADD r2, r1, 5; fusion should preserve r1 write.
  - `tests/test_semantic_equivalence.py`: Checks state equivalence; currently fails due to r1 difference.
  - `tools/measure_micro_add.py`: Benchmark script; needs to pass after fix.
- **Current Behavior**: Fused instruction only writes to ADD destination, losing LOAD destination.
- **Required Fix**: Change fused args to [load_dst, add_dst, load_addr, imm]; simulator loads into load_dst and adds into add_dst.

## Plan
1. **Backup Files**: Create backups of passes.py and simulator.py.
2. **Edit passes.py**: Update `apply_fusion_pass_safe` to build 4-arg fused_args for LOAD+ADD: [load_dst, add_dst, load_addr, imm].
3. **Edit simulator.py**: Update `execute_op` for FUSED_LOAD_ADD to handle 4 operands (load_dst, add_dst, mem_ref, imm), loading into load_dst and adding into add_dst. Maintain backward compatibility for 3 operands.
4. **Test Diagnostic Script**: Run the provided Python script to check uncompiled vs compiled states.
5. **Run Semantic Test**: Execute `tests/test_semantic_equivalence.py` to verify equivalence.
6. **Run Benchmark**: Execute `tools/measure_micro_add.py` with N=10000, runs=5, verbose, out=bench/result_fixed2.csv.

## Dependent Files to Edit
- `src/crz/compiler/passes.py`
- `src/crz/simulator/simulator.py`

## Followup Steps
- After edits, run diagnostic script.
- If semantic test passes, run benchmark.
- If issues, debug and re-edit.
- Ensure no regressions in other tests.
