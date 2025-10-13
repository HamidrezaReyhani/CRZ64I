"""
from .passes import run_passes

Generates Python code for the simulator from AST.
"""

from typing import List, Dict
from .ast import Function, Instr, Statement, If, Loop, Label, LocalDecl, Assign, Return


class SimulatorCodegen:
    """Code generator for simulator."""

    def __init__(self):
        self.op_map = {
            "ADD": "add",
            "SUB": "sub",
            "MUL": "mul",
            "DIV": "div",
            "JMP": "jmp",
            "JZ": "jz",
            "JNZ": "jnz",
            "CALL": "call",
            "RET": "ret",
            "FUSED_ADD_MUL": "fused_add_mul",  # For fused ops
        }

    def generate_function(self, func: Function) -> str:
        """Generate simulator code for a function."""
        code = f"def {func.name}(simulator):\n"
        for stmt in func.body:
            code += self.generate_statement(stmt)
        return code

    def generate_statement(self, stmt: Statement) -> str:
        """Generate code for a statement."""
        if isinstance(stmt, Instr):
            return self.generate_instr(stmt)
        elif isinstance(stmt, If):
            code = f"    if simulator.get_flag('{stmt.condition}'):\n"
            for s in stmt.then_block:
                code += "    " + self.generate_statement(s)
            if stmt.else_block:
                code += "    else:\n"
                for s in stmt.else_block:
                    code += "    " + self.generate_statement(s)
            return code
        elif isinstance(stmt, Loop):
            code = f"    for i in range({stmt.start}, {stmt.end}):\n"
            code += f"        simulator.set_reg('{stmt.var}', i)\n"
            for s in stmt.body:
                code += "    " + self.generate_statement(s)
            return code
        elif isinstance(stmt, Label):
            return f"    # label {stmt.name}\n"
        else:
            return f"    # unknown statement\n"

    def generate_instr(self, instr: Instr) -> str:
        """Generate code for an instruction."""
        op = self.op_map.get(instr.mnemonic, instr.mnemonic.lower())
        args = ", ".join(
            f"'{op}'" if isinstance(op, str) else str(op) for op in instr.operands
        )
        return f"    simulator.{op}({args})\n"

    def generate_program(self, program: List[Function]) -> str:
        """Generate full simulator program."""
        code = "from simulator import Simulator\n\n"
        code += "sim = Simulator()\n\n"
        for func in program:
            code += self.generate_function(func) + "\n"
        code += f"{program[0].name}(sim)\n"  # Call main
        return code


def generate_simulator_code(program: List[Function]) -> str:
    """Generate simulator Python code from program AST."""
    codegen = SimulatorCodegen()
    return codegen.generate_program(program)


def lower_statement(stmt, config):
    if isinstance(stmt, Instr):
        op = stmt.mnemonic
        args = stmt.operands
        fused = "FUSED" in op
        energy_est = config.energy.get(op, 0.0)
        return [{"op": op, "args": args, "fused": fused, "energy_est": energy_est}]
    elif isinstance(stmt, Loop):
        return lower_loop(stmt, config)
    elif isinstance(stmt, If):
        return lower_if(stmt, config)
    elif isinstance(stmt, Label):
        return [{"op": "LABEL", "args": [stmt.name]}]
    elif isinstance(stmt, LocalDecl):
        return lower_expr_assign(stmt.name, stmt.expr, config)
    elif isinstance(stmt, Assign):
        return lower_expr_assign(stmt.target, stmt.expr, config)
    elif isinstance(stmt, Return):
        if stmt.expr:
            return [{"op": "ADD", "args": ["r0", stmt.expr, "r0"]}]
        return []
    else:
        return []


def lower_expr_assign(target, expr, config):
    """Lower assignment expr to instructions."""
    if "+" in expr:
        left, right = expr.split("+", 1)
        left = left.strip()
        right = right.strip()
        return [
            {
                "op": "ADD",
                "args": [target, left, right],
                "fused": False,
                "energy_est": config.energy.get("ADD", 0.0),
            }
        ]
    else:
        return [
            {
                "op": "ADD",
                "args": [target, expr, "r0"],
                "fused": False,
                "energy_est": config.energy.get("ADD", 0.0),
            }
        ]


def lower_loop(loop, config):
    var = loop.var
    start = loop.start
    end = loop.end
    loop_label = f"loop_{id(loop)}"
    end_label = f"loop_end_{id(loop)}"
    ir = []
    # init var = start
    ir.append(
        {
            "op": "ADD",
            "args": [var, start, "r0"],
            "fused": False,
            "energy_est": config.energy.get("ADD", 0.0),
        }
    )
    # label loop
    ir.append({"op": "LABEL", "args": [loop_label]})
    # body
    for s in loop.body:
        ir.extend(lower_statement(s, config))
    # add var, var, 1
    ir.append(
        {
            "op": "ADD",
            "args": [var, var, "1"],
            "fused": False,
            "energy_est": config.energy.get("ADD", 0.0),
        }
    )
    # br_if LT var, end, loop_label
    ir.append({"op": "BR_IF", "args": ["LT", var, end, loop_label]})
    # label end
    ir.append({"op": "LABEL", "args": [end_label]})

    return ir


def lower_if(if_stmt, config):
    then_label = f"then_{id(if_stmt)}"
    end_label = f"end_if_{id(if_stmt)}"
    ir = []
    # br_if condition, then_label  (assume condition is reg)
    ir.append({"op": "BR_IF", "args": [if_stmt.condition, then_label]})
    # jmp end
    ir.append({"op": "JMP", "args": [end_label]})
    # label then
    ir.append({"op": "LABEL", "args": [then_label]})
    for s in if_stmt.then_block:
        ir.extend(lower_statement(s, config))
    ir.append({"op": "JMP", "args": [end_label]})
    if if_stmt.else_block:
        else_label = f"else_{id(if_stmt)}"
        # after then jmp, label else
        ir.append({"op": "LABEL", "args": [else_label]})
        for s in if_stmt.else_block:
            ir.extend(lower_statement(s, config))
    ir.append({"op": "LABEL", "args": [end_label]})

    return ir


def codegen(program, apply_fusion=True):
    """Generate simulator IR with fused flags and energy estimates."""
    from ..config import Config
    from .passes import apply_fusion_to_ir

    func = program.declarations[0]
    config = Config()
    ir = []
    for i, (name, _) in enumerate(func.params):
        ir.append(
            {
                "op": "ADD",
                "args": [name, f"r{i}", "r0"],
                "fused": False,
                "energy_est": config.energy.get("ADD", 0.0),
            }
        )
    for stmt in func.body:
        ir.extend(lower_statement(stmt, config))
    # Apply fusion to IR if requested
    if apply_fusion:
        ir = apply_fusion_to_ir(ir)
    return ir
