"""
CRZ64I Optimization Passes

Implements optimization passes including fusion patterns, reversible checks, and energy optimizations.
"""

from typing import List, Dict, Any
from .ast import Function, Instr, Statement, Attribute, Loop, If


def apply_fusion_pass_safe(func: Function, patterns: Dict[str, List[str]]) -> Function:
    """
    Apply fusion optimization pass using configurable patterns.

    Args:
        func: The function AST to optimize.
        patterns: Dict of fusion patterns, e.g., {"add_mul": ["ADD", "MUL"]}

    Returns:
        Optimized function AST.
    """
    default_patterns = {"load_add": ["LOAD", "ADD"]}
    all_patterns = {**default_patterns, **patterns}

    def fuse_body(body):
        # Fuse in the body
        i = 0
        while i < len(body) - 1:
            stmt1 = body[i]
            stmt2 = body[i + 1]
            if isinstance(stmt1, Instr) and isinstance(stmt2, Instr):
                for pattern_name, pattern_ops in all_patterns.items():
                    if (
                        len(pattern_ops) == 2
                        and stmt1.mnemonic == pattern_ops[0]
                        and stmt2.mnemonic == pattern_ops[1]
                    ):
                        fused_mnemonic = f"FUSED_{stmt1.mnemonic}_{stmt2.mnemonic}"
                        if pattern_name == "load_add":
                            load_dst = stmt1.operands[0]
                            add_dst = stmt2.operands[0]
                            addr = stmt1.operands[1]
                            imm = stmt2.operands[2]
                            fused_operands = [load_dst, add_dst, addr, imm]
                        else:
                            fused_operands = stmt1.operands + stmt2.operands[1:]
                        fused_instr = Instr(
                            mnemonic=fused_mnemonic,
                            operands=fused_operands,
                            attrs=stmt1.attrs + stmt2.attrs,
                            raw=f"{stmt1.raw} {stmt2.raw}",
                        )
                        body[i] = fused_instr
                        del body[i + 1]
                        break
            else:
                i += 1
        return body

    def process_body(body):
        new_body = []
        for stmt in body:
            if isinstance(stmt, Loop):
                new_body.append(
                    Loop(
                        var=stmt.var,
                        start=stmt.start,
                        end=stmt.end,
                        body=fuse_body(stmt.body),
                    )
                )
            elif isinstance(stmt, If):
                new_body.append(
                    If(
                        condition=stmt.condition,
                        then_block=fuse_body(stmt.then_block),
                        else_block=(
                            fuse_body(stmt.else_block) if stmt.else_block else None
                        ),
                    )
                )
            else:
                new_body.append(stmt)
        return fuse_body(new_body)

    new_body = process_body(func.body)

    return Function(
        name=func.name,
        params=func.params,
        return_type=func.return_type,
        body=new_body,
        attrs=func.attrs,
        meta=func.meta,
    )


def apply_reversible_pass(func: Function) -> Function:
    """
    Apply reversible emulation pass: Insert SAVE_DELTA at start, RESTORE_DELTA at end.
    """
    # Check attributes for reversible
    is_reversible = any(attr.name == "reversible" for attr in func.attrs)
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


def fusion_pass(program):
    """
    Apply fusion pass and return list of instructions.
    """
    optimized = run_passes(program, ["fusion"], {})
    func = optimized.declarations[0]
    return [stmt for stmt in func.body if isinstance(stmt, Instr)]


def fusion_pass(program):
    """
    Apply fusion pass to the program and return the list of instructions from the first function.

    Args:
        program: Program AST.

    Returns:
        List of instructions.
    """
    config = {}
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
        config = {}
    optimized = []
    for func in program.declarations:
        for pass_name in passes:
            if pass_name == "fusion":
                patterns = config.get("fusion_patterns", {})
                func = apply_fusion_pass_safe(func, patterns)
            elif pass_name == "reversible_emulation":
                func = apply_reversible_pass(func)
            elif pass_name == "energy_profile":
                energy_table = config.get("energy_table", {})
                func = apply_energy_pass(func, energy_table)
        optimized.append(func)
    return program.__class__(declarations=optimized)


# --- safe fusion pass (added) ---
def apply_fusion_pass_safe(func, patterns=None, max_fuse=100000):
    """
    Semantics-preserving, linear fusion pass.
    Works with AST bodies that are lists of dicts (or objects with 'op'/'args' or 'mnemonic'/'args').
    Pattern fused: LOAD dst, [addr]  +  ADD dst2, dst, imm/reg  -> FUSED_LOAD_ADD dst2, addr, imm/reg
    Preserves ADD destination (so semantics remain).
    max_fuse prevents pathological/unbounded work.
    """
    # get body list (support both dict-function and object-function)
    body = None
    if isinstance(func, dict):
        body = list(func.get("body", []))
    else:
        body = list(getattr(func, "body", []))

    new_body = []
    i = 0
    fused = 0
    while i < len(body):
        if fused >= max_fuse:
            # safety: attach remainder unchanged and stop fusing
            new_body.extend(body[i:])
            break

        stmt = body[i]

        # helper to read op/mnemonic and args from stmt
        def _read(stmt):
            if isinstance(stmt, dict):
                op = stmt.get("op") or stmt.get("mnemonic")
                args = stmt.get("args", [])
            else:
                op = getattr(stmt, "op", None) or getattr(stmt, "mnemonic", None)
                args = getattr(stmt, "args", []) or []
            # normalize op to uppercase string if available
            if isinstance(op, str):
                op_n = op.upper()
            else:
                op_n = None
            return op_n, args

        op, args = _read(stmt)

        # match LOAD followed by ADD pattern
        if op == "LOAD" and (i + 1) < len(body):
            nxt = body[i + 1]
            op2, args2 = _read(nxt)
            if op2 == "ADD":
                # LOAD args: [dst, src_addr]
                # ADD args: [dst2, src_reg, imm_or_reg]
                load_dst = args[0] if len(args) > 0 else None
                add_src = args2[1] if len(args2) > 1 else None
                # only fuse when ADD reads the register written by LOAD
                if load_dst is not None and add_src == load_dst:
                    add_dst = args2[0] if len(args2) > 0 else None
                    imm = args2[2] if len(args2) > 2 else None
                    # fused args: [load_dst, add_dst, load_addr, imm]
                    fused_args = [
                        load_dst,
                        add_dst,
                        args[1] if len(args) > 1 else None,
                        imm,
                    ]
                    fused_instr = {
                        "op": "FUSED_LOAD_ADD",
                        "args": fused_args,
                        "fused": True,
                        "energy_est": 1.0,
                    }
                    new_body.append(fused_instr)
                    fused += 1
                    i += 2
                    continue

        # default: copy statement unchanged
        new_body.append(stmt)
        i += 1

    # write back
    if isinstance(func, dict):
        func["body"] = new_body
    else:
        setattr(func, "body", new_body)
    return func


# --- end safe fusion pass ---
