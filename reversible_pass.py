# reversible_pass.py
# CRZ64I Reversible Emulation Pass

from instructions import INSTRUCTIONS

class ReversiblePass:
    def __init__(self):
        self.reversible_instructions = ['SAVE_DELTA', 'RESTORE_DELTA', 'REV_ADD', 'REV_SWAP']
        self.erasing_instructions = ['STORE', 'STOREF', 'ADD', 'SUB', 'MUL', 'DIV']  # Instructions that may erase information

    def apply(self, ast):
        """Apply reversible emulation pass to AST"""
        for node in ast:
            if node['type'] == 'function':
                if self.is_reversible_function(node):
                    node['body'] = self.emulate_reversibility(node['body'])
        return ast

    def is_reversible_function(self, node):
        """Check if function is marked as reversible"""
        attributes = node.get('attributes', [])
        return any(attr['name'] == 'reversible' for attr in attributes)

    def emulate_reversibility(self, statements):
        """Insert SAVE_DELTA and RESTORE_DELTA around erasing operations"""
        emulated = []
        delta_stack = []  # Track nested reversible sections

        for stmt in statements:
            if stmt['type'] == 'instruction':
                mnemonic = stmt['mnemonic']
                if mnemonic in self.erasing_instructions:
                    # Insert SAVE_DELTA before erasing operation
                    save_delta = self.create_save_delta(stmt)
                    emulated.append(save_delta)
                    delta_stack.append(len(emulated) - 1)  # Track position

                    # Add the original instruction
                    emulated.append(stmt)

                    # Insert RESTORE_DELTA after (for simple case)
                    restore_delta = self.create_restore_delta(stmt)
                    emulated.append(restore_delta)
                else:
                    emulated.append(stmt)
            else:
                emulated.append(stmt)

        return emulated

    def create_save_delta(self, original_stmt):
        """Create SAVE_DELTA instruction"""
        # Use a temporary register for delta storage
        return {
            'type': 'instruction',
            'mnemonic': 'SAVE_DELTA',
            'operands': [
                {'type': 'register', 'value': 'R_temp_delta'},
                {'type': 'register', 'value': original_stmt['operands'][0]['value'] if original_stmt['operands'] else 'R0'}
            ],
            'reversible_emulation': True
        }

    def create_restore_delta(self, original_stmt):
        """Create RESTORE_DELTA instruction"""
        return {
            'type': 'instruction',
            'mnemonic': 'RESTORE_DELTA',
            'operands': [
                {'type': 'register', 'value': original_stmt['operands'][0]['value'] if original_stmt['operands'] else 'R0'},
                {'type': 'register', 'value': 'R_temp_delta'}
            ],
            'reversible_emulation': True
        }

    def analyze_dataflow(self, statements):
        """Analyze dataflow to determine precise delta points"""
        # Simple dataflow analysis to find live variables and erasure points
        live_vars = set()
        for stmt in reversed(statements):
            if stmt['type'] == 'instruction':
                # Track definitions and uses
                pass  # Implementation for precise analysis
        return live_vars

    def optimize_deltas(self, statements):
        """Optimize delta insertions (remove redundant SAVE/RESTORE pairs)"""
        optimized = []
        saved_deltas = []
        for stmt in statements:
            if stmt['type'] == 'instruction' and stmt.get('reversible_emulation'):
                if stmt['mnemonic'] == 'SAVE_DELTA':
                    saved_deltas.append(stmt)
                elif stmt['mnemonic'] == 'RESTORE_DELTA':
                    if saved_deltas:
                        # Check if matching SAVE exists
                        optimized.append(saved_deltas.pop())
                        optimized.append(stmt)
                    else:
                        # Orphaned restore - remove
                        pass
                else:
                    optimized.append(stmt)
            else:
                optimized.append(stmt)
        return optimized

    def check_reversibility_constraints(self, node):
        """Verify that reversible emulation maintains correctness"""
        # Check that all erasing operations are properly wrapped
        # Verify that delta registers don't conflict
        pass


# Example usage
if __name__ == "__main__":
    from grammar import CRZParser
    from semantic_checker import SemanticChecker

    sample_code = """
    #[reversible]
    fn reversible_example(a: i32, b: i32) -> i32 {
        let result = a + b;
        STORE result, [mem];
        return result;
    }
    """

    parser = CRZParser()
    ast = parser.parse(sample_code)

    checker = SemanticChecker()
    check_result = checker.check(ast)
    print("Pre-reversible check:", check_result['valid'])

    reversible_pass = ReversiblePass()
    reversible_ast = reversible_pass.apply(ast)

    print("Reversible AST applied")
    print("Example body after emulation:", reversible_ast[0]['body'] if reversible_ast else "No body")
