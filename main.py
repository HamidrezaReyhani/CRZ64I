# main.py
# CRZ64I Main Driver

import sys
from grammar import CRZParser
from compiler import CRZCompiler
from assembler import CRZAssembler
from simulator import CRZSimulator

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <command> [file]")
        return

    command = sys.argv[1]
    if command == 'test':
        # Run test
        code = """
        ADD R1, R0, 10;
        _loop:
        LOAD R2, [R1];
        VDOT32 R3, R2, R4;
        BR_IF LT R1, 20, _loop;
        HALT;
        """
        parser = CRZParser()
        instructions, labels = parser.parse(code)
        # Resolve labels
        for i, instr in enumerate(instructions):
            if instr['mnemonic'] == 'BR_IF':
                label = instr['operands'][3]
                if label in labels:
                    offset = labels[label] - i
                    instr['operands'][3] = str(offset)
        compiler = CRZCompiler()
        optimized = compiler.compile(instructions)
        simulator = CRZSimulator()
        cycles, energy, temperature = simulator.run(optimized)
        print(f"Simulation: Cycles={cycles}, Energy={energy}, Temperature={temperature}")
    elif command == 'run' and len(sys.argv) > 2:
        file = sys.argv[2]
        with open(file, 'r') as f:
            code = f.read()
        parser = CRZParser()
        instructions, labels = parser.parse(code)
        # Resolve labels
        for i, instr in enumerate(instructions):
            if instr['mnemonic'] == 'BR_IF':
                label = instr['operands'][3]
                if label in labels:
                    offset = labels[label] - i
                    instr['operands'][3] = str(offset)
        compiler = CRZCompiler()
        optimized = compiler.compile(instructions)
        simulator = CRZSimulator()
        cycles, energy, temperature = simulator.run(optimized)
        print(f"Run {file}: Cycles={cycles}, Energy={energy}, Temperature={temperature}")

if __name__ == '__main__':
    main()
