# fusion_pass.py
# CRZ64I Fusion Pass Implementation

from instructions import INSTRUCTIONS

class FusionPass:
    def __init__(self):
        self.fused_instructions = {
            'LOAD_ADD_STORE': ['LOAD', 'ADD', 'STORE'],
            'LOAD_VDOT32': ['LOAD', 'VDOT32'],
            'ADD_STORE': ['ADD', 'STORE']
        }

    def apply(self, ast):
        """Apply fusion pass to AST"""
        for node in ast:
            if node['type'] == 'function':
                node['body'] = self.fuse_instructions(node['body'])
        return ast

    def fuse_instructions(self, statements):
        """Fuse adjacent instructions where possible"""
        fused = []
        i = 0
        while i < len(statements):
            stmt = statements[i]
            if stmt['type'] == 'instruction':
                # Try to fuse with next instructions
                fused_stmt = self.try_fuse(statements, i)
                if fused_stmt:
                    fused.append(fused_stmt)
                    i += len(fused_stmt['original_instructions'])
                else:
                    fused.append(stmt)
                    i += 1
            else:
                fused.append(stmt)
                i += 1
        return fused

    def try_fuse(self, statements, start_idx):
        """Try to fuse instructions starting from start_idx"""
        for fused_name, pattern in self.fused_instructions.items():
            if self.match_pattern(statements, start_idx, pattern):
                return self.create_fused_instruction(fused_name, statements[start_idx:start_idx + len(pattern)])

        # Check for attribute-driven fusion
        if start_idx + 1 < len(statements):
            first = statements[start_idx]
            second = statements[start_idx + 1]
            if (first['type'] == 'instruction' and second['type'] == 'instruction' and
                self.has_fusion_attribute(first) and self.can_fuse_pair(first, second)):
                return self.create_fused_instruction('GENERIC_FUSED', [first, second])

        return None

    def match_pattern(self, statements, start_idx, pattern):
        """Check if statements match the fusion pattern"""
        if start_idx + len(pattern) > len(statements):
            return False

        for i, mnemonic in enumerate(pattern):
            stmt = statements[start_idx + i]
            if stmt['type'] != 'instruction' or stmt['mnemonic'] != mnemonic:
                return False
        return True

    def create_fused_instruction(self, fused_name, original_instructions):
        """Create a fused instruction from original instructions"""
        # Combine operands and create new instruction
        operands = []
        for instr in original_instructions:
            operands.extend(instr['operands'])

        return {
            'type': 'instruction',
            'mnemonic': fused_name,
            'operands': operands,
            'original_instructions': original_instructions,
            'fused': True
        }

    def has_fusion_attribute(self, instruction):
        """Check if instruction has fusion attribute"""
        return 'attributes' in instruction and any(attr['name'] == 'fusion' for attr in instruction['attributes'])

    def can_fuse_pair(self, first, second):
        """Check if two instructions can be fused semantically"""
        # Simple semantic checks for fusion
        first_mnemonic = first['mnemonic']
        second_mnemonic = second['mnemonic']

        # Example fusion rules
        if first_mnemonic == 'LOAD' and second_mnemonic in ['ADD', 'SUB', 'MUL']:
            # Check if LOAD destination is used in second instruction
            load_dest = first['operands'][0]['value'] if first['operands'] else None
            second_operands = [op['value'] for op in second['operands'] if 'value' in op]
            return load_dest in second_operands

        elif first_mnemonic in ['ADD', 'SUB'] and second_mnemonic == 'STORE':
            # Check if ADD result is stored
            add_dest = first['operands'][0]['value'] if first['operands'] else None
            store_src = second['operands'][0]['value'] if second['operands'] else None
            return add_dest == store_src

        return False

    def optimize_fused(self, fused_instruction):
        """Apply optimizations to fused instructions"""
        # Latency and energy optimizations for fused ops
        mnemonic = fused_instruction['mnemonic']
        if mnemonic in INSTRUCTIONS:
            # Adjust latency/energy based on fusion
            info = INSTRUCTIONS[mnemonic]
            fused_instruction['latency'] = info['latency'] * 0.8  # Example reduction
            fused_instruction['energy'] = info['energy'] * 0.9
        return fused_instruction


# Example usage
if __name__ == "__main__":
    from grammar import CRZParser
    from semantic_checker import SemanticChecker

    sample_code = """
    #[fusion]
    fn fused_example(a: ptr, b: ptr, c: ptr) {
        LOAD R1, [a];
        ADD R2, R1, R3;
        STORE R2, [c];
    }
    """

    parser = CRZParser()
    ast = parser.parse(sample_code)

    checker = SemanticChecker()
    checker.check(ast)

    fusion_pass = FusionPass()
    fused_ast = fusion_pass.apply(ast)

    print("Original AST:", ast)
    print("Fused AST:", fused_ast)
