# CRZ64I Programming Language - Comprehensive Documentation

## Overview

CRZ64I is a custom Instruction Set Architecture (ISA) and intermediate/system-level programming language designed to achieve four core objectives:

1. **Reduce processing cycles per instruction**: Through fusion and compression techniques.
2. **Achieve near-real-time execution**: With minimal latency and deterministic behavior.
3. **Minimize energy consumption**: In processing, data preparation, storage, and communication.
4. **Minimize heat generation**: Through software-oriented and reversible patterns, without relying on cooling mechanisms.

CRZ64I is designed to be compatible with existing hardware architectures (x86, ARM, RISC-V) without requiring new hardware or modifications. Extensions are defined for leveraging specific hardware capabilities.

## Table of Contents

1. [Introduction](#introduction)
2. [Syntax and Grammar](#syntax-and-grammar)
3. [Data Types and Memory Model](#data-types-and-memory-model)
4. [Registers](#registers)
5. [Instruction Set](#instruction-set)
6. [Attributes and Semantics](#attributes-and-semantics)
7. [Compiler Architecture](#compiler-architecture)
8. [Runtime and ABI](#runtime-and-abi)
9. [Standard Library](#standard-library)
10. [Tools](#tools)
11. [Testing and Benchmarking](#testing-and-benchmarking)
12. [Security](#security)
13. [Development and Licensing](#development-and-licensing)
14. [Examples](#examples)
15. [Appendices](#appendices)

## Introduction

CRZ64I aims to push the boundaries of computational efficiency by focusing on software-level optimizations that approach theoretical limits of energy and latency. It incorporates concepts from reversible computing, adiabatic processes, and low-power design patterns.

### Key Principles

- **Fusion**: Combining multiple instructions into single operations.
- **Reversibility**: Avoiding information erasure to minimize thermodynamic dissipation.
- **Energy Awareness**: Runtime decisions based on power consumption models.
- **Real-time Determinism**: Guaranteed worst-case execution times.

## Syntax and Grammar

CRZ64I uses a simple assembly-like syntax with attributes for optimization hints.

### Basic Grammar (EBNF)

```
program ::= { top_level_declaration }
top_level_declaration ::= attribute_list? ( function_declaration | global_instruction )
attribute_list ::= { attribute }
attribute ::= "#[" identifier [ "=" value ] "]"
function_declaration ::= "fn" identifier "(" parameter_list? ")" block
block ::= "{" { statement } "}"
statement ::= attribute_list? ( instruction ";" | local_declaration | return_statement | label )
instruction ::= mnemonic operand_list?
operand ::= register | immediate | memory_reference
memory_reference ::= "[" expression "]"
```

### Example Program

```crz
#[fusion]
#[reversible]
fn matrix_multiply(a: ptr, b: ptr, c: ptr, n: i32) {
    #[power="low"]
    for i in 0..n {
        for j in 0..n {
            sum = 0;
            for k in 0..n {
                LOAD r1, [a + i*n + k];
                LOAD r2, [b + k*n + j];
                MUL r3, r1, r2;
                ADD sum, sum, r3;
            }
            STORE sum, [c + i*n + j];
        }
    }
}
```

## Data Types and Memory Model

### Data Types

- Integer: `i8`, `i16`, `i32`, `i64`, `u8`, `u16`, `u32`, `u64`
- Floating-point: `f32`, `f64`
- Vector: `vec<N, T>` where N is lane count, T is element type
- Pointer: `ptr`
- Void: `void`

### Memory Model

- Sequential consistency by default
- Relaxed memory for performance-critical sections
- 4KB page alignment
- Atomic operations supported
- Memory-mapped I/O regions

## Registers

- **General Purpose**: R0-R31 (64-bit)
- **Vector**: V0-V15 (128/256/512-bit configurable)
- **Special**: PC (Program Counter), SP (Stack Pointer), FP (Frame Pointer), FLAGS

## Instruction Set

CRZ64I defines 64 instructions across 10 categories.

### 1. Control Flow (8 instructions)

1. `NOP` - No operation
2. `BR label` - Unconditional branch
3. `BR_IF cond, label` - Conditional branch
4. `CALL label` - Function call
5. `RET` - Return from function
6. `YIELD` - Cooperative yield
7. `TRAP code` - Exception/trap
8. `HALT` - Program halt

### 2. Integer and Bitwise Operations (10 instructions)

9. `ADD rd, rs1, rs2` - Addition
10. `SUB rd, rs1, rs2` - Subtraction
11. `MUL rd, rs1, rs2` - Multiplication
12. `DIV rd, rs1, rs2` - Division
13. `AND rd, rs1, rs2` - Bitwise AND
14. `OR rd, rs1, rs2` - Bitwise OR
15. `XOR rd, rs1, rs2` - Bitwise XOR
16. `SHL rd, rs1, imm` - Shift left
17. `SHR rd, rs1, imm` - Shift right
18. `POPCNT rd, rs1` - Population count

### 3. Memory and I/O (8 instructions)

19. `LOAD rd, [addr]` - Load from memory
20. `STORE rs, [addr]` - Store to memory
21. `LOADF rd, [addr]` - Load floating-point
22. `STORE_F rs, [addr]` - Store floating-point
23. `ATOMIC_INC [addr]` - Atomic increment
24. `DMA_START src, dst, len` - DMA transfer hint
25. `CACHE_LOCK addr, size` - Cache locking hint
26. `PREFETCH addr` - Prefetch hint

### 4. Vector/SIMD Operations (10 instructions)

27. `VLOAD vd, [addr]` - Vector load
28. `VSTORE vs, [addr]` - Vector store
29. `VADD vd, vs1, vs2` - Vector addition
30. `VSUB vd, vs1, vs2` - Vector subtraction
31. `VMUL vd, vs1, vs2` - Vector multiplication
32. `VDOT32 vd, vs1, vs2` - 32-bit dot product
33. `VSHL vd, imm` - Vector shift left
34. `VSHR vd, imm` - Vector shift right
35. `VFMA vd, vs1, vs2, vs3` - Vector fused multiply-add
36. `VREDUCE_SUM rd, vs` - Vector reduce sum

### 5. Floating-Point Operations (4 instructions)

37. `FADD fd, fa, fb` - Floating-point addition
38. `FSUB fd, fa, fb` - Floating-point subtraction
39. `FMUL fd, fa, fb` - Floating-point multiplication
40. `FMA fd, fa, fb, fc` - Floating-point fused multiply-add

### 6. Atomic and Synchronization (4 instructions)

41. `LOCK addr` - Acquire lock
42. `UNLOCK addr` - Release lock
43. `CMPXCHG [addr], expected, new` - Compare and exchange
44. `FENCE` - Memory fence

### 7. System and Power Management (6 instructions)

45. `SET_PWR_MODE mode` - Set power mode
46. `GET_PWR_STATE rd` - Get power state
47. `THERM_READ rd` - Read thermal sensor
48. `SET_THERM_POLICY policy` - Set thermal policy
49. `SLEEP ms` - Sleep for milliseconds
50. `FAST_PATH_ENTER` - Enter fast path mode

### 8. Reversible Operations (6 instructions)

51. `SAVE_DELTA tmp, target` - Save state delta
52. `RESTORE_DELTA tmp, target` - Restore state delta
53. `REV_ADD rd, ra, rb` - Reversible addition
54. `REV_SWAP a, b` - Reversible swap
55. `ADIABATIC_START` - Start adiabatic mode
56. `ADIABATIC_STOP` - Stop adiabatic mode

### 9. Cryptographic and Hash (4 instructions)

57. `CRC32 rd, rs, len` - CRC32 checksum
58. `HASH_INIT ctx` - Initialize hash context
59. `HASH_UPDATE ctx, addr, len` - Update hash
60. `HASH_FINAL ctx, rd` - Finalize hash

### 10. Miscellaneous (4 instructions)

61. `PROFILE_START id` - Start profiling
62. `PROFILE_STOP id` - Stop profiling
63. `TRACE point` - Trace point
64. `EXTENSION opcode, args` - Extension hook

## Attributes and Semantics

Attributes provide hints and constraints for optimization.

- `#[fusion]`: Allow fusion of adjacent instructions
- `#[reversible]`: Ensure reversibility of operations
- `#[no_erase]`: Prevent information erasure
- `#[power="low"|"med"|"high"]`: Power consumption hint
- `#[realtime]`: Require deterministic execution
- `#[thermal_hint=N]`: Thermal management hint

## Compiler Architecture

The CRZ64I compiler consists of multiple passes:

1. **Frontend**: Parsing and AST generation
2. **Semantic Analysis**: Attribute validation and type checking
3. **Fusion Pass**: Instruction fusion optimization
4. **Reversible Pass**: Reversibility enforcement
5. **Energy-Aware Pass**: Power optimization
6. **Code Generation**: Target code emission

## Runtime and ABI

### Calling Convention

- Arguments: R0-R5
- Return value: R0
- Stack alignment: 16 bytes
- Caller-saved: R0-R5, R16-R31
- Callee-saved: R6-R15

### Runtime Features

- Lightweight threading
- Thermal-aware scheduling
- Zero-copy IPC
- Memory management with reversibility support

## Standard Library

- `crz::math`: Mathematical functions and BLAS operations
- `crz::mem`: Memory management utilities
- `crz::sync`: Synchronization primitives
- `crz::io`: I/O operations
- `crz::crypto`: Cryptographic functions

## Tools

- **Assembler**: `crz-as` - Convert assembly to binary
- **Disassembler**: `crz-objdump` - Convert binary to assembly
- **Simulator**: Cycle-accurate simulation with energy modeling
- **Compiler**: `crz-cc` - Compile CRZ64I to target architectures
- **Profiler**: Performance and energy profiling tools

## Testing and Benchmarking

### Key Metrics

- Cycles per instruction (CPI)
- Energy per operation (Joules/op)
- Latency percentiles (P95, P99)
- Thermal stability

### Benchmark Suite

- Microbenchmarks for individual instructions
- Kernel benchmarks (matrix operations, FFT)
- Application benchmarks (ML inference, real-time processing)

## Security

- Sandboxed execution
- Access control for privileged operations
- Side-channel attack mitigation
- Formal verification support

## Development and Licensing

CRZ64I is developed under the OpenLogic project.

- **License**: MIT License
- **Repository**: https://github.com/openlogicorg/crz64i
- **Contributing**: Pull requests with benchmarks and tests

## Examples

### Vector Addition

```crz
#[fusion]
fn vector_add(a: ptr, b: ptr, c: ptr, n: i32) {
    for i in 0..n step 4 {
        VLOAD v0, [a + i];
        VLOAD v1, [b + i];
        VADD v2, v0, v1;
        VSTORE v2, [c + i];
    }
}
```

### Reversible Computation

```crz
#[reversible]
fn reversible_add(a: i32, b: i32) -> i32 {
    SAVE_DELTA temp, result;
    REV_ADD result, a, b;
    return result;
}
```

## Appendices

### A. Instruction Encoding

Each instruction is encoded in 32 bits:
- Opcode: 8 bits
- Operands: Variable, up to 24 bits

### B. ABI Details

Detailed register usage and stack layout.

### C. Performance Characteristics

Latency and energy tables for all instructions.

### D. Formal Semantics

Mathematical definition of instruction behavior.
