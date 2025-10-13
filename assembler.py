# assembler.py
# CRZ64I Assembler: Converts parsed instructions to bytecode

from instructions import INSTRUCTIONS

class CRZAssembler:
    def __init__(self):
        self.bytecode = []
        self.labels = {}

    def resolve_labels(self, parsed, labels):
        # Resolve branch targets to offsets
        for instr in parsed:
            if instr['mnemonic'] == 'BR_IF':
                if len(instr['operands']) >= 3:
                    cond, rs, label = instr['operands'][0], instr['operands'][1], instr['operands'][2]
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
                imm_str = op[1:].strip()
                if imm_str:
                    imm = int(imm_str)
                else:
                    imm = 0
                encoding.extend([(imm >> 8 * i) & 0xFF for i in range(4)])  # 32-bit imm
            else:
                # Label offset, memory, or condition
                if op.startswith('['):
                    inner = op[1:-1]
                    if inner.startswith('R'):
                        reg_num = int(inner[1:])
                        encoding.append(reg_num & 0xFF | 0x80)  # Memory flag
                    else:
                        try:
                            offset = int(inner)
                            encoding.append(offset & 0xFF)
                        except ValueError:
                            encoding.append(0)
                else:
                    try:
                        offset = int(op)
                        encoding.append(offset & 0xFF)
                    except ValueError:
                        # Condition string like 'LT'
                        encoding.append(0)
        self.bytecode.extend(encoding)

    def assemble(self, parsed, labels):
        self.bytecode = []
        resolved = self.resolve_labels(parsed, labels)
        for instr in resolved:
            self.assemble_instruction(instr)
        return self.bytecode

    def disassemble(self, bytecode):
        # Simple disassembler
        disassembled = []
        i = 0
        while i < len(bytecode):
            opcode = bytecode[i]
            mnemonic = next((k for k, v in INSTRUCTIONS.items() if v['opcode'] == opcode), 'UNKNOWN')
            operands = []
            i += 1
            num_ops = INSTRUCTIONS.get(mnemonic, {'operands': 0})['operands']
            for _ in range(num_ops):
                if i < len(bytecode):
                    op = bytecode[i]
                    if op & 0x80:
                        reg = op & 0x7F
                        operands.append(f"[R{reg}]")
                    else:
                        operands.append(f"R{op}")
                    i += 1
                else:
                    operands.append("0")
            disassembled.append(f"{mnemonic} {' '.join(operands)}")
        return disassembled
