# Implementation Plan

## Overview
Fix the remaining parsing, semantic, and runtime issues in the CRZ64I implementation to resolve test failures and ensure all components work correctly. The issues include incorrect indexing in parser transformers, improper passing of saved_targets in semantic analysis, incorrect hints handling in runtime, and mismatched function signatures in passes. This will make the parser handle attributes and range expressions correctly, semantic analyzer properly track reversible variables, runtime interpret hints as a dictionary, and passes accept the correct arguments. Changes are targeted fixes without major refactoring, ensuring the codebase passes all tests.

The implementation is needed to complete the bug fixes started earlier and achieve full functionality. High-level approach: Fix parser indexing errors, update semantic recursion, correct runtime data structures, adjust pass calls, and verify with tests.

## Types
No new types required. Existing types suffice with minor adjustments:
- Runtime hints: Change from List[Dict] to Dict[str, Any] for direct key access.
- Semantic saved_targets: Ensure Set[str] is passed recursively in visit_block.

Relationships: Hints in Runtime used for energy/thermal modes; saved_targets in SemanticAnalyzer for reversible checks.

## Files
New files to be created: None.

Existing files to be modified:
- src/crz/compiler/parser.py: Fix attribute and range_expression indexing.
- src/crz/compiler/semantic.py: Pass saved_targets recursively in visit_block.
- src/crz/runtime/runtime.py: Interpret hints as dict.
- Test files: Update calls to run_passes to match signature.

Files to be deleted or moved: None.

Configuration file updates: None.

## Functions
New functions: None.

Modified functions:
- parser.py: attribute (change value_token = children[4]; value = value_token.value).
- parser.py: range_expression (change end = self.transform(children[1])).
- semantic.py: visit_block (add saved_targets parameter; pass recursively to sub-blocks).
- semantic.py: visit_function (pass set() to visit_block).
- runtime.py: interpret_hints (change self.hints = {h["name"]: h["value"] for h in hints}).
- Test files: run_passes calls remove config argument.

Removed functions: None.

## Classes
New classes: None.

Modified classes:
- CRZTransformer (parser.py): Update attribute and range_expression methods.
- SemanticAnalyzer (semantic.py): Update visit_block and visit_function signatures.
- Runtime (runtime.py): Update interpret_hints.

Removed classes: None.

## Dependencies
No changes.

## Testing
Testing approach: Run full pytest suite after fixes; verify specific failing tests pass. No new tests needed beyond existing.

## Implementation Order
1. Fix parser indexing in attribute and range_expression.
2. Update semantic visit_block to pass saved_targets recursively.
3. Correct runtime interpret_hints to use dict.
4. Adjust run_passes calls in tests.
5. Run full test suite and verify.
