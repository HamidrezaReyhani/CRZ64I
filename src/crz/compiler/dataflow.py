"""
CRZ64I Control Flow Graph and Dataflow Analysis

Builds CFG from AST, enumerates paths, analyzes paths for diagnostics.
"""

from typing import List, Dict, Set, Tuple, Optional, Any
from ..config import Config
from .parser import parse
from .ast import Function, Statement, Instr, If, Loop, Label


class BasicBlock:
    """Represents a basic block in the CFG."""

    def __init__(self, id: int, statements: List[Statement]):
        self.id = id
        self.statements = statements
        self.successors: List[int] = []

    def __repr__(self):
        return (
            f"Block {self.id}: {len(self.statements)} statements -> {self.successors}"
        )


class CFG:
    """Control Flow Graph."""

    def __init__(self, blocks: List[BasicBlock], entry: int = 0):
        self.blocks = blocks
        self.entry = entry

    def get_block(self, id: int) -> BasicBlock:
        return self.blocks[id]

    def enumerate_paths(self, max_paths: int = 100) -> List[List[int]]:
        """Enumerate paths from entry to exit, bounded by max_paths."""
        paths = []

        def dfs(current: int, path: List[int], visited: Set[int]):
            if len(paths) >= max_paths or len(path) > 50:  # Prune long paths
                return
            path.append(current)
            if current == len(self.blocks) - 1:  # Assume last block is exit
                paths.append(path.copy())
            else:
                for succ in self.blocks[current].successors:
                    if succ not in visited:
                        dfs(succ, path, visited.copy())
            path.pop()

        dfs(self.entry, [], set())
        return paths

    def analyze_path(self, path: List[int]) -> List[Dict[str, str]]:
        """Analyze a path for diagnostics."""
        diagnostics = []
        # Simple analysis: check for potential issues
        for block_id in path:
            block = self.blocks[block_id]
            for stmt in block.statements:
                if isinstance(stmt, Instr):
                    # Example: check for division by zero potential
                    if stmt.mnemonic == "DIV" and len(stmt.operands) > 1:
                        if stmt.operands[1] == "0":
                            diagnostics.append(
                                {
                                    "type": "warning",
                                    "message": "Potential division by zero",
                                    "block": block_id,
                                }
                            )
        return diagnostics


def build_cfg(func: Function) -> CFG:
    """Build CFG from Function AST."""
    blocks = []
    current_block = BasicBlock(0, [])
    block_map: Dict[str, int] = {}  # label to block id
    pending_labels: Dict[str, int] = {}  # label to block id to resolve jumps

    def add_block():
        nonlocal current_block
        if current_block.statements:
            blocks.append(current_block)
            current_block = BasicBlock(len(blocks), [])

    for stmt in func.body:
        if isinstance(stmt, Label):
            add_block()
            block_map[stmt.name] = len(blocks)
            current_block = BasicBlock(len(blocks), [stmt])
            blocks.append(current_block)
            current_block = BasicBlock(len(blocks), [])
        elif isinstance(stmt, If):
            add_block()
            current_block.statements.append(stmt)
            # Assume then and else blocks
            then_start = len(blocks)
            current_block.successors.append(then_start)
            # Process then
            for s in stmt.then_block:
                if isinstance(s, Label):
                    add_block()
                    block_map[s.name] = len(blocks)
                    current_block = BasicBlock(len(blocks), [s])
                    blocks.append(current_block)
                    current_block = BasicBlock(len(blocks), [])
                else:
                    current_block.statements.append(s)
            add_block()
            if stmt.else_block:
                else_start = len(blocks)
                current_block.successors.append(else_start)
                # Process else
                for s in stmt.else_block:
                    if isinstance(s, Label):
                        add_block()
                        block_map[s.name] = len(blocks)
                        current_block = BasicBlock(len(blocks), [s])
                        blocks.append(current_block)
                        current_block = BasicBlock(len(blocks), [])
                    else:
                        current_block.statements.append(s)
                add_block()
            # After if, continue
            merge = len(blocks)
            for b in [then_start, else_start if stmt.else_block else None]:
                if b is not None:
                    blocks[b].successors.append(merge)
            current_block = BasicBlock(merge, [])
            blocks.append(current_block)
        elif isinstance(stmt, Loop):
            add_block()
            loop_start = len(blocks)
            current_block.successors.append(loop_start)
            current_block = BasicBlock(loop_start, [])
            for s in stmt.body:
                if isinstance(s, Label):
                    add_block()
                    block_map[s.name] = len(blocks)
                    current_block = BasicBlock(len(blocks), [s])
                    blocks.append(current_block)
                    current_block = BasicBlock(len(blocks), [])
                else:
                    current_block.statements.append(s)
            add_block()
            # Back edge
            blocks[-1].successors.append(loop_start)
            # After loop
            after = len(blocks)
            blocks[-1].successors.append(after)
            current_block = BasicBlock(after, [])
            blocks.append(current_block)
        elif isinstance(stmt, Instr):
            current_block.statements.append(stmt)
            # If jump, end block
            if stmt.mnemonic in ["JMP", "JZ", "JNZ", "CALL", "RET"]:
                add_block()
                # Resolve successors later
        else:
            current_block.statements.append(stmt)

    add_block()
    # Resolve jumps
    for block in blocks:
        for stmt in block.statements:
            if isinstance(stmt, Instr) and stmt.mnemonic in ["JMP", "JZ", "JNZ"]:
                if stmt.operands:
                    target = stmt.operands[0]
                    if target in block_map:
                        block.successors.append(block_map[target])
            elif isinstance(stmt, Instr) and stmt.mnemonic == "CALL":
                # Assume call returns to next
                if block.id + 1 < len(blocks):
                    block.successors.append(block.id + 1)
            elif isinstance(stmt, Instr) and stmt.mnemonic == "RET":
                # No successor
                pass
            else:
                # Sequential
                if block.id + 1 < len(blocks):
                    block.successors.append(block.id + 1)

    return CFG(blocks)


class DataflowAnalyzer:
    """Dataflow analyzer for reversible functions."""

    def __init__(self, func: Function):
        from ..config import load_config

        self.func = func
        self.cfg = build_cfg(func)
        self.config = load_config()
        self.errors: List[Dict[str, Any]] = []

    def analyze(self) -> List[Dict[str, Any]]:
        """Analyze the function for reversible issues."""
        self.errors = []
        if not any(attr.name == "reversible" for attr in self.func.attrs):
            return self.errors  # Only analyze reversible functions

        registers = [f"R{i}" for i in range(8)]

        def analyze_statements(
            statements: List[Statement],
            path_let: Set[str],
            path_written: Set[str],
            current_path: List,
            errors: List,
        ):
            for stmt_idx, stmt in enumerate(statements):
                if isinstance(stmt, Instr):
                    if stmt.mnemonic == "LET":
                        if stmt.operands:
                            var = stmt.operands[0]
                            path_let.add(var)
                    else:
                        for op in stmt.operands:
                            if op in registers:
                                if op not in path_let and op not in path_written:
                                    errors.append(
                                        {
                                            "type": "error",
                                            "message": f"Write to {op} without prior let",
                                            "path": current_path.copy(),
                                            "stmt_idx": stmt_idx,
                                        }
                                    )
                                path_written.add(op)
                elif isinstance(stmt, If):
                    then_path = current_path + ["then"]
                    analyze_statements(
                        stmt.then_block,
                        path_let.copy(),
                        path_written.copy(),
                        then_path,
                        errors,
                    )
                    if stmt.else_block:
                        else_path = current_path + ["else"]
                        analyze_statements(
                            stmt.else_block,
                            path_let.copy(),
                            path_written.copy(),
                            else_path,
                            errors,
                        )
                elif isinstance(stmt, Loop):
                    loop_path = current_path + ["loop"]
                    analyze_statements(
                        stmt.body,
                        path_let.copy(),
                        path_written.copy(),
                        loop_path,
                        errors,
                    )

        # Analyze all paths from CFG
        for path in self.cfg.enumerate_paths(self.config.max_paths):
            path_let = set()
            path_written = set()
            for block_id in path:
                block = self.cfg.get_block(block_id)
                block_path = [block_id]
                analyze_statements(
                    block.statements, path_let, path_written, block_path, self.errors
                )

        return self.errors


def analyze_file(filepath: str) -> Dict[str, List[Dict[str, Any]]]:
    """Analyze a CRZ file for dataflow issues."""
    with open(filepath, "r") as f:
        code = f.read()
    program = parse(code)
    func = next((d for d in program.declarations if isinstance(d, Function)), None)
    if not func:
        return {"issues": []}
    analyzer = DataflowAnalyzer(func)
    issues = analyzer.analyze()
    return {"issues": issues}


def analyze_text(txt: str, max_paths: int = 100, max_len: int = 100) -> Dict[str, str]:
    """Analyze CRZ text for path explosion status."""
    program = parse(txt)
    func = next((d for d in program.declarations if isinstance(d, Function)), None)
    if not func:
        return {"status": "error"}
    cfg = build_cfg(func)
    paths = cfg.enumerate_paths(max_paths)
    if len(paths) >= max_paths:
        status = "bounded"
    else:
        status = "ok"
    return {"status": status}
