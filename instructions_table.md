# CRZ64I Instruction Set Table

This document provides a comprehensive table of all 64 instructions in the CRZ64I ISA.

| Mnemonic | Opcode | Format | Operands | Latency | Energy |
|----------|--------|--------|----------|---------|--------|
| NOP | 0x00 | N | 0 | 1 | 0.1 |
| BR | 0x01 | B | 1 | 1 | 0.2 |
| BR_IF | 0x02 | B | 3 | 1 | 0.3 |
| CALL | 0x03 | B | 1 | 2 | 0.5 |
| RET | 0x04 | N | 0 | 2 | 0.5 |
| YIELD | 0x05 | N | 0 | 3 | 0.8 |
| TRAP | 0x06 | I | 1 | 5 | 1.0 |
| HALT | 0x07 | N | 0 | 1 | 0.1 |
| ADD | 0x08 | R | 3 | 1 | 0.5 |
| SUB | 0x09 | R | 3 | 1 | 0.5 |
| MUL | 0x0A | R | 3 | 2 | 1.0 |
| DIV | 0x0B | R | 3 | 10 | 5.0 |
| AND | 0x0C | R | 3 | 1 | 0.3 |
| OR | 0x0D | R | 3 | 1 | 0.3 |
| XOR | 0x0E | R | 3 | 1 | 0.3 |
| SHL | 0x0F | R | 3 | 1 | 0.4 |
| SHR | 0x10 | R | 3 | 1 | 0.4 |
| POPCNT | 0x11 | R | 2 | 2 | 0.8 |
| LOAD | 0x12 | I | 2 | 2 | 1.0 |
| STORE | 0x13 | I | 2 | 2 | 1.0 |
| LOADF | 0x14 | I | 2 | 2 | 1.0 |
| STOREF | 0x15 | I | 2 | 2 | 1.0 |
| ATOMIC_INC | 0x16 | I | 1 | 3 | 1.5 |
| DMA_START | 0x17 | I | 3 | 1 | 0.5 |
| CACHE_LOCK | 0x18 | I | 2 | 1 | 0.3 |
| PREFETCH | 0x19 | I | 1 | 1 | 0.2 |
| VLOAD | 0x1A | V | 2 | 3 | 1.5 |
| VSTORE | 0x1B | V | 2 | 3 | 1.5 |
| VADD | 0x1C | V | 3 | 2 | 1.0 |
| VSUB | 0x1D | V | 3 | 2 | 1.0 |
| VMUL | 0x1E | V | 3 | 3 | 2.0 |
| VDOT32 | 0x1F | V | 3 | 4 | 2.0 |
| VSHL | 0x20 | V | 2 | 2 | 0.8 |
| VSHR | 0x21 | V | 2 | 2 | 0.8 |
| VFMA | 0x22 | V | 4 | 4 | 2.5 |
| VREDUCE_SUM | 0x23 | V | 2 | 5 | 3.0 |
| FADD | 0x24 | R | 3 | 2 | 1.0 |
| FSUB | 0x25 | R | 3 | 2 | 1.0 |
| FMUL | 0x26 | R | 3 | 3 | 1.5 |
| FMA | 0x27 | R | 4 | 4 | 2.0 |
| LOCK | 0x28 | I | 1 | 5 | 2.0 |
| UNLOCK | 0x29 | I | 1 | 3 | 1.0 |
| CMPXCHG | 0x2A | I | 3 | 4 | 1.8 |
| FENCE | 0x2B | N | 0 | 2 | 0.5 |
| SET_PWR_MODE | 0x2C | I | 1 | 10 | 0.1 |
| GET_PWR_STATE | 0x2D | R | 1 | 2 | 0.3 |
| THERM_READ | 0x2E | R | 1 | 5 | 0.5 |
| SET_THERM_POLICY | 0x2F | I | 1 | 10 | 0.1 |
| SLEEP | 0x30 | I | 1 | 1 | 0.01 |
| FAST_PATH_ENTER | 0x31 | N | 0 | 5 | 1.0 |
| SAVE_DELTA | 0x32 | R | 2 | 1 | 0.5 |
| RESTORE_DELTA | 0x33 | R | 2 | 1 | 0.5 |
| REV_ADD | 0x34 | R | 3 | 1 | 0.4 |
| REV_SWAP | 0x35 | R | 2 | 1 | 0.3 |
| ADIABATIC_START | 0x36 | N | 0 | 5 | 0.1 |
| ADIABATIC_STOP | 0x37 | N | 0 | 5 | 0.1 |
| CRC32 | 0x38 | R | 3 | 10 | 5.0 |
| HASH_INIT | 0x39 | R | 1 | 5 | 2.0 |
| HASH_UPDATE | 0x3A | I | 3 | 8 | 4.0 |
| HASH_FINAL | 0x3B | R | 2 | 5 | 2.0 |
| PROFILE_START | 0x3C | I | 1 | 1 | 0.1 |
| PROFILE_STOP | 0x3D | I | 1 | 1 | 0.1 |
| TRACE | 0x3E | I | 1 | 1 | 0.2 |
| EXTENSION | 0x3F | I | 2 | 1 | 0.5 |

## Notes

- **Format**: R = Register, I = Immediate, V = Vector, B = Branch, N = No operands
- **Operands**: Number of operands
- **Latency**: Cycles for execution
- **Energy**: Arbitrary units for energy consumption

This table is generated from the `instructions.py` file.
