"""
CRZ64I Codegen for RISC-V

Generates RISC-V assembly from AST.
"""

from typing import List, Dict
from .ast import Function, Instr, Statement, If, Loop, Label


class RISCVCodegen:
    """Code generator for RISC-V."""

    def __init__(self):
        self.op_map = {
            "ADD": "add",
            "SUB": "sub",
            "MUL": "mul",
            "DIV": "div",
            "JMP": "j",
            "JZ": "beqz",
            "JNZ": "bnez",
            "CALL": "call",
            "RET": "ret",
            "FUSED_ADD_MUL": "fmadd.s",  # Example fused
        }

    def generate_function(self, func: Function) -> str:
        """Generate RISC-V code for a function."""
        code = f"{func.name}:\n"
        for stmt in func.body:
            code += self.generate_statement(stmt)
        return code

    def generate_statement(self, stmt: Statement) -> str:
        """Generate code for a statement."""
        if isinstance(stmt, Instr):
            return self.generate_instr(stmt)
        elif isinstance(stmt, If):
            code = f"    {self.generate_condition(stmt.condition)}\n"
            code += f"then_{id(stmt)}:\n"
            for s in stmt.then_block:
                code += self.generate_statement(s)
            if stmt.else_block:
                code += f"    j end_{id(stmt)}\n"
                code += f"else_{id(stmt)}:\n"
                for s in stmt.else_block:
                    code += self.generate_statement(s)
            code += f"end_{id(stmt)}:\n"
            return code
        elif isinstance(stmt, Loop):
            code = f"loop_{id(stmt)}:\n"
            code += f"    li t0, {stmt.start}\n"
            code += f"    li t1, {stmt.end}\n"
            code += f"    bge t0, t1, end_loop_{id(stmt)}\n"
            code += f"    # loop body\n"
            for s in stmt.body:
                code += self.generate_statement(s)
            code += f"    addi t0, t0, 1\n"
            code += f"    j loop_{id(stmt)}\n"
            code += f"end_loop_{id(stmt)}:\n"
            return code
        elif isinstance(stmt, Label):
            return f"{stmt.name}:\n"
        else:
            return f"    # unknown\n"

    def generate_instr(self, instr: Instr) -> str:
        """Generate RISC-V instr."""
        op = self.op_map.get(instr.mnemonic, instr.mnemonic.lower())
        if instr.mnemonic in ["ADD", "SUB", "MUL", "DIV"]:
            rd, rs1, rs2 = instr.operands[:3]
            return f"    {op} {rd}, {rs1}, {rs2}\n"
        elif instr.mnemonic == "JMP":
            target = instr.operands[0]
            return f"    j {target}\n"
        elif instr.mnemonic == "JZ":
            rs, target = instr.operands[:2]
            return f"    beqz {rs}, {target}\n"
        elif instr.mnemonic == "JNZ":
            rs, target = instr.operands[:2]
            return f"    bnez {rs}, {target}\n"
        elif instr.mnemonic == "CALL":
            target = instr.operands[0]
            return f"    call {target}\n"
        elif instr.mnemonic == "RET":
            return "    ret\n"
        else:
            return f"    # {instr.mnemonic} {', '.join(instr.operands)}\n"

    def generate_condition(self, condition: str) -> str:
        """Generate condition check."""
        # Assume condition is a register or flag
        return f"    bnez {condition}, then_{id(self)}"

    def generate_program(self, program: List[Function]) -> str:
        """Generate full RISC-V program."""
        code = ".text\n"
        for func in program:
            code += f".global {func.name}\n"
            code += self.generate_function(func) + "\n"
        return code


def generate_riscv_code(program: List[Function]) -> str:
    """Generate RISC-V assembly from program AST."""
    codegen = RISCVCodegen()
    return codegen.generate_program(program)
