"""
CRZ64I Optimization Passes

Implements optimization passes including fusion patterns, reversible checks, and energy optimizations.
"""

from typing import Any, Dict, List, Optional
from .ast import Function, Instr, Statement, Attribute, Loop, If, Program





def apply_reversible_pass(func: Function) -> Function:
    """
    Apply reversible emulation pass: Insert SAVE_DELTA at start, RESTORE_DELTA at end.
    """
    # Check attributes for reversible
    is_reversible = any(attr.name == "reversible" for attr in (func.attrs or []))
    if not is_reversible:
        return func  # No change if not marked

    new_body = (
        [Instr(mnemonic="SAVE_DELTA", operands=[], attrs=[], raw="SAVE_DELTA")]
        + func.body
        + [Instr(mnemonic="RESTORE_DELTA", operands=[], attrs=[], raw="RESTORE_DELTA")]
    )

    return Function(
        name=func.name,
        params=func.params,
        return_type=func.return_type,
        body=new_body,
        attrs=func.attrs,
        meta=func.meta,
    )


def apply_energy_pass(func: Function, energy_config: Dict[str, float]) -> Function:
    """
    Apply energy optimization pass: Replace high-energy ops with low-energy alternatives,
    add thermal hints.
    """
    # Example config: {"MUL": 10.0, "FMA": 8.0}  # FMA lower energy
    new_body = []
    for stmt in func.body:
        if isinstance(stmt, Instr):
            if (
                stmt.mnemonic == "MUL"
                and "FMA" in energy_config
                and energy_config["FMA"] < energy_config.get("MUL", float("inf"))
            ):
                # Replace MUL a,b,c with FMA a,0,b,c if possible (a + b*c)
                if len(stmt.operands) >= 3:
                    fma_operands = [
                        "0",
                        stmt.operands[0],
                        stmt.operands[1],
                        stmt.operands[2],
                    ]  # Assume
                    stmt = Instr(
                        mnemonic="FMA",
                        operands=fma_operands,
                        attrs=stmt.attrs + [Attribute(name="energy_opt")],
                        raw=f"FMA {stmt.raw}",
                    )
            # Add thermal hint if high energy
            total_energy = sum(energy_config.get(op, 0) for op in [stmt.mnemonic])
            if total_energy > 5.0:  # Threshold
                stmt.attrs.append(Attribute(name="thermal_hint", value="cool"))
        new_body.append(stmt)

    return Function(
        name=func.name,
        params=func.params,
        return_type=func.return_type,
        body=new_body,
        attrs=func.attrs,
        meta=func.meta,
    )


def fusion_pass(program) -> List[Instr]:
    """
    Apply fusion pass to the program and return the list of instructions from the first function.

    Args:
        program: Program AST.

    Returns:
        List of instructions.
    """
    config: Dict[str, Any] = {}
    result = run_passes(program, ["fusion"], config)
    func = result.declarations[0]
    return [stmt for stmt in func.body if isinstance(stmt, Instr)]


def apply_fusion_to_ir(ops):
    """
    Apply fusion pass to IR ops list.
    """
    i = 0
    while i < len(ops) - 1:
        op1 = ops[i]
        op2 = ops[i + 1]
        if (
            op1["op"] == "LOAD"
            and op2["op"] == "ADD"
            and op1["args"][0] == op2["args"][1]
        ):
            # Fuse LOAD rd, [addr] ; ADD rd2, rd, imm -> FUSED_LOAD_ADD load_dst, add_dst, addr, imm
            load_dst = op1["args"][0]
            add_dst = op2["args"][0]
            addr = op1["args"][1]
            imm = op2["args"][2]
            fused_op = {
                "op": "FUSED_LOAD_ADD",
                "args": [load_dst, add_dst, addr, imm],
                "fused": True,
                "energy_est": 1.0,
            }
            ops[i] = fused_op
            del ops[i + 1]
            # don't increment i
        else:
            i += 1
    return ops


def run_passes(program, passes, config=None):
    """
    Run optimization passes on the program.

    Args:
        program: Program AST.
        passes: List of pass names.
        config: Config dict.

    Returns:
        Optimized Program.
    """
    if config is None:
        config: Dict[str, Any] = {}
    optimized = []
    for func in program.declarations:
        for pass_name in passes:
            if pass_name == "fusion":
                patterns = config.get("fusion_patterns", {})
                if patterns is None:
                    patterns = {}
                # No apply_fusion_pass_safe exists; apply fusion logic directly if needed
                # If patterns are needed, pass to a fusion function here. For now, just skip patterns.
                # If fusion_pass is meant to operate on the whole program, but here we want per-function, just continue.
                # If you want to apply fusion to each function, you could implement it here.
                # For now, just leave func unchanged or implement fusion logic as needed.
                pass  # TODO: Implement per-function fusion if needed
            elif pass_name == "reversible_emulation":
                func = apply_reversible_pass(func)
            elif pass_name == "energy_profile":
                energy_table = config.get("energy_table", {})
                if energy_table is None:
                    energy_table = {}
                func = apply_energy_pass(func, energy_table)
        optimized.append(func)
    return program.__class__(declarations=optimized)



