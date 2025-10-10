# assembler.py
# CRZ64I Assembler: Converts parsed instructions to bytecode

from instructions import INSTRUCTIONS

class CRZAssembler:
    def __init__(self):
        self.bytecode = []
        self.labels = {}
        # Reverse mapping for disassembly
        self.opcode_to_mnemonic = {info['opcode']: mnemonic for mnemonic, info in INSTRUCTIONS.items()}

    def resolve_labels(self, parsed, labels):
        # Resolve branch targets to offsets
        for instr in parsed:
            if instr['mnemonic'] == 'BR_IF':
                cond, rs, label = instr['operands']
                if label in labels:
                    target = labels[label]
                    instr['operands'][2] = str(target)  # Replace label with offset
        return parsed

    def assemble_instruction(self, instr):
        mnemonic = instr['mnemonic']
        if mnemonic not in INSTRUCTIONS:
            raise ValueError(f"Unknown instruction: {mnemonic}")
        instr_info = INSTRUCTIONS[mnemonic]
        opcode = instr_info['opcode']
        # Simple encoding: opcode (8 bits) + operands (variable)
        encoding = [opcode]
        for op in instr['operands']:
            if op.startswith('R') or op.startswith('V'):
                # Register encoding: e.g., R1 -> 1
                reg_num = int(op[1:])
                encoding.append(reg_num & 0xFF)
            elif op.startswith('#'):
                # Immediate
                imm = int(op[1:])
                encoding.extend([(imm >> 8 * i) & 0xFF for i in range(4)])  # 32-bit imm
            else:
                # Label offset or memory
                offset = int(op)
                encoding.append(offset & 0xFF)
        self.bytecode.extend(encoding)

    def assemble(self, parsed, labels):
        self.bytecode = []
        resolved = self.resolve_labels(parsed, labels)
        for instr in resolved:
            self.assemble_instruction(instr)
        return self.bytecode

    def disassemble(self, bytecode):
        """Disassembler for CRZ64I bytecode"""
        instructions = []
        i = 0
        while i < len(bytecode):
            opcode = bytecode[i]
            mnemonic = self.opcode_to_mnemonic.get(opcode, 'UNKNOWN')
            i += 1
            operands = []
            num_ops = INSTRUCTIONS[mnemonic]['operands'] if mnemonic in INSTRUCTIONS else 0
            for _ in range(num_ops):
                if i < len(bytecode):
                    op_val = bytecode[i]
                    operands.append(f"R{op_val}")
                    i += 1
            instructions.append(f"{mnemonic} {' '.join(operands)}")
        return instructions
