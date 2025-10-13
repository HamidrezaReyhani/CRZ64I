# TODO: Fix MyPy Errors

## Files to Fix
- [ ] src/crz/compiler/ast.py: Handle None in attrs for extend and iter
- [ ] src/crz/compiler/passes.py: Handle None in config unpacking, add type annotations, fix redefinition of apply_fusion_pass_safe
- [ ] src/crz/compiler/semantic.py: Fix meta access for line/column, handle untyped functions
- [ ] src/crz/simulator/simulator.py: Fix dict entry type
- [ ] src/crz/compiler/dataflow.py: Fix list type for current_path
- [ ] src/crz/cli/simulator_cli.py: Handle None iterable, add annotations, fix return
- [ ] src/crz/cli/compiler_cli.py: Fix DataflowAnalyzer arg type, add annotations, handle None iterables

## Steps
1. Fix ast.py: In Program.to_json, check if attrs is None before extend and iter.
2. Fix passes.py: In run_passes, handle config.get returns None, add type for config, remove duplicate function.
3. Fix semantic.py: In log_issue, meta is dict, access .get('line'), .get('column').
4. Fix simulator.py: In thermal_map, ensure values are float.
5. Fix dataflow.py: Change current_path to List[int].
6. Fix simulator_cli.py: Handle None in sim.run, add type for pass_config, fix return type.
7. Fix compiler_cli.py: Filter decl to Function, add type for pass_config, handle None in issues.
