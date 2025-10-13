# CRZ64I Language Reference

## Syntax

CRZ64I programs are written in a C-like syntax with attributes.

### Functions

```crz
#[reversible] fn fibonacci(n: i32) -> i32 {
    let a = 0;
    let b = 1;
    for i in 0..n {
        let tmp = a;
        a = b;
        b = tmp + b;
    }
    return b;
}
```

### Attributes

- `#[fusion]`: Enable instruction fusion
- `#[reversible]`: Enforce reversibility
- `#[no_erase]`: Allow destructive writes
- `#[power="low"]`: Low power mode
- `#[realtime]`: Real-time constraints
- `#[thermal_hint]`: Thermal hints

### Instructions

- Arithmetic: ADD, SUB, MUL, DIV
- Memory: LOAD, STORE
- Vector: VADD, VMUL, VDOT32
- Control: JMP, JZ, CALL, RET
- Special: FMA, CRC32, PROFILE_START

### Operands

- Registers: R0-R31, V0-V15
- Immediates: numbers, strings
- Memory: [expr]
- Labels: label_name

## Grammar

See [crz64i.lark](../src/crz/compiler/crz64i.lark) for the formal grammar.
