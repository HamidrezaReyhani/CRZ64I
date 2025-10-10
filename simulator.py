# simulator.py
# CRZ64I Simulator: Cycle-accurate execution with energy model and reversible support

from instructions import INSTRUCTIONS, NUM_REGS, NUM_VREGS

class CRZSimulator:
    def __init__(self):
        self.regs = [0] * NUM_REGS
        self.vregs = [[0]*32 for _ in range(NUM_VREGS)]  # Vector regs, 32 elements each
        self.memory = [0] * 1024  # Simple memory
        self.pc = 0
        self.cycles = 0
        self.energy = 0.0
        self.temperature = 0.0  # Thermal model
        self.halted = False
        self.reversible_log = []  # For reversible execution

    def execute_instruction(self, instr):
        mnemonic = instr['mnemonic']
        operands = instr['operands']
        info = INSTRUCTIONS[mnemonic]
        latency = info['latency']
        energy = info['energy']

        if mnemonic == 'ADD':
            rd = int(operands[0][1:])
            rs1 = int(operands[1][1:])
            op2 = operands[2]
            if op2.startswith('R'):
                rs2 = int(op2[1:])
                self.regs[rd] = self.regs[rs1] + self.regs[rs2]
            else:
                imm = int(op2)
                self.regs[rd] = self.regs[rs1] + imm
        elif mnemonic == 'LOAD':
            rd = int(operands[0][1:])
            addr_str = operands[1]
            if addr_str.startswith('[') and addr_str.endswith(']'):
                base_str = addr_str[1:-1]
                if base_str.startswith('R'):
                    base = int(base_str[1:])
                    addr = self.regs[base]
                else:
                    addr = int(base_str)
                self.regs[rd] = self.memory[addr]
        elif mnemonic == 'STORE':
            rs = int(operands[0][1:])
            addr_str = operands[1]
            if addr_str.startswith('[') and addr_str.endswith(']'):
                base_str = addr_str[1:-1]
                if base_str.startswith('R'):
                    base = int(base_str[1:])
                    addr = self.regs[base]
                else:
                    addr = int(base_str)
                self.memory[addr] = self.regs[rs]
        elif mnemonic == 'VDOT32':
            vd = int(operands[0][1:])
            vs1 = int(operands[1][1:])
            vs2 = int(operands[2][1:])
            # Assume scalar for now
            dot = self.regs[vs1] * self.regs[vs2]
            self.vregs[vd][0] = dot
        elif mnemonic == 'FMA':
            rd = int(operands[0][1:])
            rs1 = int(operands[1][1:])
            rs2 = int(operands[2][1:])
            rs3 = int(operands[3][1:])
            self.regs[rd] = self.regs[rs1] * self.regs[rs2] + self.regs[rs3]
        elif mnemonic == 'BR_IF':
            cond = operands[0]
            rs = int(operands[1][1:])
            label = operands[2]
            # Assume offset is calculated elsewhere
            if cond == 'LT' and self.regs[rs] < 20:
                self.pc = int(label) - 1  # Simple offset
        elif mnemonic == 'SAVE_DELTA':
            temp = int(operands[0][1:])
            rd = operands[1]
            self.regs[temp] = self.regs[int(rd[1:])]  # Save copy
        elif mnemonic == 'RESTORE_DELTA':
            temp = int(operands[0][1:])
            rd = operands[1]
            self.regs[int(rd[1:])] = self.regs[temp]  # Restore
        elif mnemonic == 'FUSED_LOAD_ADD_STORE':
            addr = operands[0]
            rs2 = operands[1]
            store_addr = operands[2]
            # Simulate fused: load, add, store
            if addr.startswith('['):
                base = int(addr[2:-1][1:])
                val = self.memory[self.regs[base]]
            else:
                val = int(addr)
            result = val + int(rs2)
            if store_addr.startswith('['):
                base = int(store_addr[2:-1][1:])
                self.memory[self.regs[base]] = result
        elif mnemonic == 'FUSED_LOAD_VDOT32':
            addr = operands[0]
            vd = int(operands[1][1:])
            vs2 = int(operands[2][1:])
            # Load and dot
            if addr.startswith('['):
                base = int(addr[2:-1][1:])
                val = self.memory[self.regs[base]]
            else:
                val = int(addr)
            dot = val * self.regs[vs2]
            self.vregs[vd][0] = dot
        elif mnemonic == 'FUSED_ADD_STORE':
            rs1 = int(operands[0][1:])
            rs2 = int(operands[1][1:])
            store_addr = operands[2]
            result = self.regs[rs1] + self.regs[rs2]
            if store_addr.startswith('['):
                base = int(store_addr[2:-1][1:])
                self.memory[self.regs[base]] = result
        elif mnemonic == 'HALT':
            self.halted = True

        # Reversible support: log state for undo
        if 'reversible' in instr and instr['reversible']:
            self.reversible_log.append((self.pc, self.regs.copy(), self.vregs.copy()))

        self.cycles += latency
        self.energy += energy
        self.temperature += energy * 0.1  # Simple thermal model

    def run(self, instructions):
        self.pc = 0
        self.cycles = 0
        self.energy = 0.0
        self.temperature = 0.0
        self.halted = False
        max_cycles = 1000  # Prevent infinite loops
        cycle_count = 0
        while self.pc < len(instructions) and not self.halted and cycle_count < max_cycles:
            instr = instructions[self.pc]
            self.execute_instruction(instr)
            self.pc += 1
            cycle_count += 1
        return self.cycles, self.energy, self.temperature

    def reverse_step(self):
        if self.reversible_log:
            self.pc, self.regs, self.vregs = self.reversible_log.pop()
            # Adjust cycles/energy if needed
