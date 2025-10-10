import time

# ------------------------
# CRZ64I Python Simulator
# QDI+NCL, Dual-Rail, Wave Pipelining
# Supports 64 registers (R1-R64)
# ------------------------

class CRZ64I:
    def __init__(self):
        # 64 registers, dual-rail simulated with dict of DATA and NULL wavefronts
        self.regs_data = {f'R{i+1}': 0 for i in range(64)}
        self.regs_null = {f'R{i+1}': 0 for i in range(64)}
        # Instruction set mapping: mnemonic -> function
        self.instr_set = {
            'MOV': self.mov,
            'ADD': self.add,
            'SUB': self.sub,
            'AND': self.and_op,
            'OR': self.or_op,
            'XOR': self.xor_op,
            'XCHG': self.xchg,
            'FADD.ATM': self.fadd_atm,
            # ... other 56 instructions can be similarly defined
        }
        # Latency for each instruction (simulation cycles)
        self.instr_latency = {mn:1 for mn in self.instr_set}

    # ------------------------
    # Instruction implementations
    # ------------------------

    def mov(self, dst, src):
        self.regs_data[dst] = self.regs_data[src]

    def add(self, dst, src):
        self.regs_data[dst] += self.regs_data[src]

    def sub(self, dst, src):
        self.regs_data[dst] -= self.regs_data[src]

    def and_op(self, dst, src):
        self.regs_data[dst] &= self.regs_data[src]

    def or_op(self, dst, src):
        self.regs_data[dst] |= self.regs_data[src]

    def xor_op(self, dst, src):
        self.regs_data[dst] ^= self.regs_data[src]

    def xchg(self, reg1, reg2):
        self.regs_data[reg1], self.regs_data[reg2] = self.regs_data[reg2], self.regs_data[reg1]

    def fadd_atm(self, reg1, reg2):
        old = self.regs_data[reg1]
        self.regs_data[reg1] += self.regs_data[reg2]
        return old

    # ------------------------
    # Execute a list of instructions (with dual-rail wavefront simulation)
    # ------------------------

    def execute(self, program):
        max_cycles = 1000  # safety limit
        cycle = 0
        instr_queue = [(mn, args) for mn, args in program]

        print('Starting CRZ64I simulation...')
        while instr_queue and cycle < max_cycles:
            cycle += 1
            new_queue = []
            for instr, args in instr_queue:
                # Simulate propagation delay (1 cycle per instruction here)
                self.instr_set[instr](*args)
                new_queue.append((instr, args))  # retain for wavefront logging

            # Dual-rail NULL wavefronts update
            for r in self.regs_null:
                self.regs_null[r] = self.regs_data[r]

            # Logging wavefronts
            print(f'Cycle {cycle}:')
            print(f'  DATA wavefronts: {self.regs_data}')
            print(f'  NULL wavefronts: {self.regs_null}')
            print('')

            instr_queue = instr_queue[1:]  # simple pipelining, 1 instr per cycle
        print('Simulation finished.')


# ------------------------
# Testbench: 64 instruction sequence
# ------------------------

if __name__ == '__main__':
    cpu = CRZ64I()
    program = []

    # Initialize registers with MOV
    for i in range(1, 9):
        program.append(('MOV', (f'R{i}', f'R{i}')))

    # 64 instruction sample: alternating ADD, SUB, AND, OR, XOR, XCHG, FADD.ATM
    reg_pairs = [(f'R{i}', f'R{(i%8)+1}') for i in range(1, 65)]
    instrs = ['ADD', 'SUB', 'AND', 'OR', 'XOR', 'XCHG', 'FADD.ATM', 'MOV']

    for idx, pair in enumerate(reg_pairs):
        program.append((instrs[idx % len(instrs)], pair))

    cpu.execute(program)
