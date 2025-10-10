# compiler.py
# CRZ64I Compiler with Optimization Passes

class CRZCompiler:
    def __init__(self):
        self.passes = [self.fusion_pass, self.reversible_pass]

    def fusion_pass(self, instructions):
        # Enhanced fusion: Detect LOAD + ADD + STORE, LOAD + VDOT32, ADD + STORE
        fused = []
        i = 0
        while i < len(instructions):
            if i + 2 < len(instructions):
                load = instructions[i]
                add = instructions[i+1]
                store = instructions[i+2]
                if (load['mnemonic'] == 'LOAD' and
                    add['mnemonic'] == 'ADD' and
                    store['mnemonic'] == 'STORE' and
                    load['operands'][0] == add['operands'][1] and
                    add['operands'][0] == store['operands'][0]):
                    # Fuse to FUSED_LOAD_ADD_STORE
                    fused_instr = {
                        'mnemonic': 'FUSED_LOAD_ADD_STORE',
                        'operands': [load['operands'][1], add['operands'][2], store['operands'][1]]
                    }
                    fused.append(fused_instr)
                    i += 3
                    continue
            if i + 1 < len(instructions):
                load = instructions[i]
                vdot = instructions[i+1]
                if (load['mnemonic'] == 'LOAD' and
                    vdot['mnemonic'] == 'VDOT32' and
                    load['operands'][0] == vdot['operands'][1]):
                    # Fuse to FUSED_LOAD_VDOT32
                    fused_instr = {
                        'mnemonic': 'FUSED_LOAD_VDOT32',
                        'operands': [load['operands'][1], vdot['operands'][0], vdot['operands'][2]]
                    }
                    fused.append(fused_instr)
                    i += 2
                    continue
                add = instructions[i]
                store = instructions[i+1]
                if (add['mnemonic'] == 'ADD' and
                    store['mnemonic'] == 'STORE' and
                    add['operands'][0] == store['operands'][0]):
                    # Fuse to FUSED_ADD_STORE
                    fused_instr = {
                        'mnemonic': 'FUSED_ADD_STORE',
                        'operands': [add['operands'][1], add['operands'][2], store['operands'][1]]
                    }
                    fused.append(fused_instr)
                    i += 2
                    continue
            fused.append(instructions[i])
            i += 1
        return fused

    def reversible_pass(self, instructions):
        # Enhanced reversible emulation: Insert SAVE_DELTA before reversible writes
        reversible_ops = ['ADD', 'SUB', 'XOR', 'REV_ADD', 'REV_SWAP']
        new_instructions = []
        for instr in instructions:
            mnemonic = instr['mnemonic']
            if mnemonic in reversible_ops and len(instr['operands']) > 0:
                rd = instr['operands'][0]
                if rd.startswith('R'):
                    # Insert SAVE_DELTA before the instruction
                    save_instr = {
                        'mnemonic': 'SAVE_DELTA',
                        'operands': ['R31', rd]  # Use R31 as temp
                    }
                    new_instructions.append(save_instr)
            new_instructions.append(instr)
            instr['reversible'] = mnemonic in reversible_ops
        return new_instructions

    def compile(self, instructions):
        for pass_func in self.passes:
            instructions = pass_func(instructions)
        return instructions
