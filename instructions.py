# instructions.py
# CRZ64I Instruction Set Definition

INSTRUCTIONS = {
    'ADD': {
        'opcode': 0x01,
        'format': 'R',  # Register
        'operands': 3,  # rd, rs1, rs2
        'latency': 1,
        'energy': 0.5,  # arbitrary units
    },
    'LOAD': {
        'opcode': 0x02,
        'format': 'I',  # Immediate
        'operands': 2,  # rd, imm
        'latency': 2,
        'energy': 1.0,
    },
    'VDOT32': {
        'opcode': 0x03,
        'format': 'V',  # Vector
        'operands': 3,  # vd, vs1, vs2
        'latency': 4,
        'energy': 2.0,
    },
    'BR_IF': {
        'opcode': 0x04,
        'format': 'B',  # Branch
        'operands': 3,  # cond, rs1, label
        'latency': 1,
        'energy': 0.3,
    },
    'HALT': {
        'opcode': 0xFF,
        'format': 'N',  # No operands
        'operands': 0,
        'latency': 1,
        'energy': 0.1,
    },
    'FUSED_LOAD_ADD_STORE': {'opcode': 0x40, 'format': 'I', 'operands': 3, 'latency': 5, 'energy': 2.0},
    'FUSED_LOAD_VDOT32': {'opcode': 0x41, 'format': 'I', 'operands': 3, 'latency': 6, 'energy': 3.0},
    'FUSED_ADD_STORE': {'opcode': 0x42, 'format': 'I', 'operands': 3, 'latency': 3, 'energy': 1.5},
    'SAVE_DELTA': {'opcode': 0x43, 'format': 'R', 'operands': 2, 'latency': 1, 'energy': 0.5},
    'RESTORE_DELTA': {'opcode': 0x44, 'format': 'R', 'operands': 2, 'latency': 1, 'energy': 0.5},
    # Add more as needed
}

# Registers: R0-R63, V0-V7
NUM_REGS = 64
NUM_VREGS = 8
